# -*- coding: utf-8 -*-
""" Main module of EU06 Maps report for EnergizAIR """

import datetime
import ogr
import osr
import os
import json
from traits.api import Instance, Str
# from ast import literal_eval
from pytz import timezone
import pytz
import numpy as np

from energizair.config import ENERGIZAIR_PATH, TEMP_ATTACH, APERE_IFRAME_PATH
from energizair.country import Country, Belgium
from energizair.report.indicators_report import IndicatorsReport
from energizair.model.mysql_db_model_01 import Session, Report, TMY, Country as DbCountry
from energizair.indicator.maps_hourly_photovoltaic_indicator_eu06 import MapsHourlyPhotovoltaicIndicatorEU06
from numpy.f2py.auxfuncs import throw_error

__author__ = "Jean Pierre Huart"
__email__ = "jph@openjph.be"
__copyright__ = "Copyright 2016, Jean Pierre Huart"
__license__ = "GPLv3"
__date__ = "2016-02-27"
__version__ = "1.0"
__status__ = "Development"


MAIN_PATH = {'BE': os.path.join(ENERGIZAIR_PATH, 'scripts/belgium/gis_data/')}
DATA_DIR = {'BE': os.path.join(MAIN_PATH['BE'], 'data/')}

class EnergizAIRColorPaletteError(RuntimeError):
    '''raise this when there has been an error replacing the hourly color palette'''

class EU06MapReport(IndicatorsReport):
    """
    Abstract class with all the methods to be used by all Map Reports.

    :param country: The country to run the report on.
    :type country: Instance of Country
    :param dbreportname: The report name, combined with the country, it will allow to retrieve the report object (dbreport) from the database.
    :type dbreportname: String
    :param dbreport: The report object that contain all the details for the report as stored into the database
    :type dbreport: Instance of Report
    :param indicators: The list of indicators used to calculate the report
    :type indicators: List of indicators

    """
    country = Instance(Country)
    dbreportname = Str
    dbreport = Instance(Report)

    def _dbreport_default(self):
        """ Trait initializer. """
        session = Session()
        repcountry = session.query(DbCountry).filter_by(code=self.country.code).first()
        dbreport = session.query(Report).filter_by(countryid=repcountry.id).filter_by(
            code=self.__class__.__name__).filter_by(name=self.dbreportname).first()
        session.close_all()
        if None == dbreport:
            msg = '\'{0}\' report, using class {1}, for country {2} does not exists into the database'.format(
                self.dbreportname, self.__class__.__name__, self.country.name)
            raise ValueError(msg)

        return dbreport

    #### 'IndicatorsReport' protocol ##########################################

#     template_clrsky = TEMPLATE_CLSKY

    def _indicators_default(self):
        """ Trait initializer. """

        if self.country is None:
            raise ValueError('The EU06MapReport needs a country',
                             ' attribute.')

        """init indicators with the selected date - 1 day due to the provider constraints"""
        indicators = [MapsHourlyPhotovoltaicIndicatorEU06(
            name='map_pv_eu06',
            country=self.country,
            report=self.dbreport,
        ),
        ]

        return indicators

    bln_clean = True

    ###########################################################################
    # 'Report' protocol.
    ###########################################################################

    def generate(self, pdate, storage):
        """
        Generate all the report data: list of files that has been generated.

        Should be overridden by child classes

        :param pdate: The date of the report.
        :type pdate: datetime.date
        :param storage: The storage used by the model (normally the same as the server one)
        :type storage: Instance of HDF5TimeSeriesStorageClient
        :return: values resulting of the calculation of all the defined indicators formatted as defined in Report
        :rtype: formatted data, generally XML or HTML string

        """
        pass

    def _convert_longlat_in_lambert(self, longitude, latitude):
        """
        Convert the stored values (EPSG 4326) in Lambert 72 projection (EPSG 31370)
        """
        pointX = longitude
        pointY = latitude
        # Spatial Reference System
        inputEPSG = 4326
        outputEPSG = 31370
        # create a geometry from coordinates
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(pointX, pointY)
        # create coordinate transformation
        inSpatialRef = osr.SpatialReference()
        inSpatialRef.ImportFromEPSG(inputEPSG)

        outSpatialRef = osr.SpatialReference()
        outSpatialRef.ImportFromEPSG(outputEPSG)
        coordTransform = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)
        # transform point
        point.Transform(coordTransform)

        # return longitude latitude in EPSG 31370
        return point.GetX(), point.GetY()

    def _delete_csv_data_files(self):
        """ delete csv data """
        from glob import glob
        try:

            for csvfile in glob(DATA_DIR[self.country.code] + '*.csv'):
                os.remove(csvfile)

            treated = True

        except:
            treated = False

        finally:
            return treated

    def _generate_daily_csv_4maps(self, pv, solar_point_details, datafilenames):
        """ 
        Create a csv file per date with all the solar points.
        """

        try:
            content, fc_date = self._generate_daily_data_4maps(pv, solar_point_details, datafilenames)
            datafilename = self._set_names('map_daily', fc_date)

            with open(os.path.join(DATA_DIR[self.country.code], datafilename + '.csv'), 'w') as f:
                f.write(content.encode('utf8'))

            datafilenames.append(datafilename)

            treated = True

        except:
            treated = False

        finally:
            return treated, datafilenames
        
    def _generate_daily_data_4maps(self, pv, solar_point_details, datafilenames):
        """ 
        Create a csv file per date with all the solar points.

        Result daily power is expressed in percentage of clearsky.
        Result hourly power is expressed in Wh/Wp

        We want to display a map displaying for each point a percentage of the clearky production.
        In other words, is it a bright day for the season.

        To do that we use "TMY" clear sky values obtained via METEONORM

        kWh/m² Meteonorm (total par jour) * 0,148 = kWh/m² PV (production clear sky)

        (production clear sky)*16/3 = kWh/kWp

         NB relation identifée en comparant des journées de production clear sky sur l’installation bruxelloise Michel, 
         2010 – 2011 – 2012 – 2013 – 2014 – 2015, plein sud 35° inclinaison, Sunpower WHT 300W. 3 kWc=16m², 
         avec une année de rayonnement clear sky meteonorm, sur base journalière. 

         La relation rayonnement clear sky vs production clear sky est linéaire et : 

         Production = rayonnement*0,148. 

         Le facteur 16/3 permet la conversion de valeur énergétiques d’ensoleillement par m² 
         en valeur énergétique par puissance crète étant donné que la relation précédente 
         se base sur un certain type de capteur, Sunpower WHT 300W. 

        """
        FILE_HEADER_DATA0 = u"LONGITUDE,LATITUDE,CLEARSKY,SOLPOINT,DATE,PEAK,PLAGE,GRPHPLAGE,MAPLON,MAPLAT,H1,H2,H3,H4,H5,H6,H7,H8,H9,H10,H11,H12,H13,H14,H15,H16,H17,H18,H19,H20,H21,H22,H23,H24"
        TEMPLATE_DATA0 = u"{longitude},{latitude},{pvpower},{solpoint},{date},{peak},{plage},{graph_plage},{map_lon},{map_lat},{hours}"

        try:
            fc_date = 'problem'
            hourly_pv_points = u''
            for fc_date in pv[0]['hourly_energy_wh'].keys():
                """ treat hourly data for each pv point """
                result = {}
                for point in pv:
                    longitude, latitude = point['longitude'], point['latitude']
                    maplon, maplat = solar_point_details[str(point['epice_id'])]['map_lon'], solar_point_details[str(point['epice_id'])]['map_lat']
                    if self.country == Belgium:
                        longitude, latitude = self._convert_longlat_in_lambert(point['longitude'], point['latitude'])
                        maplon, maplat = self._convert_longlat_in_lambert(maplon, maplat)

                    result['longitude'] = longitude
                    result['latitude'] = latitude
                    result['map_lon'] = maplon
                    result['map_lat'] = maplat
                    result['solpoint'] = solar_point_details[str(point['epice_id'])]['tran']['fr']
                    result['date'] = fc_date

                    result['hours'] = ''
                    result['pvpower'] = 0
                    fc_hour = 0
                    hour_data = []
                    while fc_hour < 24:
                        """ hourly pvpower is expressed in Wh/Wp """
                        result['hours'] = result['hours'] + \
                            '{0},'.format(point['hourly_energy_wh'][fc_date][fc_hour])
                        result['pvpower'] += point['hourly_energy_wh'][fc_date][fc_hour]
                        hour_data.append(point['hourly_energy_wh'][fc_date][fc_hour])
                        fc_hour += 1

                    """ Retrieve clearsky reference and hourly correction from tmy data """
                    clearsky_reference, hourly_correction = self._get_daily_meteonorm_tmy(
                        int(fc_date[5:7]), int(fc_date[8:10]), solar_point_details[str(point['epice_id'])]['id'])
                    """ express daily pvpower in clearsky percentages """
                    result['pvpower'] = result['pvpower'] / clearsky_reference * 100
                    result['hours'] = result['hours'][:-1]
                    
                    """ Calculate peak and plage """
                    ar_data = np.array(hour_data)
                    result['peak'], result['plage'], result['graph_plage'] = self._set_plage(ar_data, fc_date)
                    
                    hourly_pv_points += TEMPLATE_DATA0.format(**result) + u'\n'
                    
                    """ Redefine hourly color palette in function of hourly_correction """
                    check = self._set_hourly_color_palette(hourly_correction)                    

            content = FILE_HEADER_DATA0 + u'\n' + hourly_pv_points

        except:
            content = False           

        finally:
            return content, fc_date
        
    def _generate_daily_summary_csv(self, datafiles, return_files):
        # load csv file
        # Record clearsky index
        # define peak hour , power
        # calculate mean value
        # calculate median value
        # define sunny interval
        # save it on a csv

        # Options
        # display a chart

        FILE_HEADER_SUMMARY = u"SOLPOINT,DATE,CLEARSKY,PEAK,PEAKPOWER,MEAN,MEDIAN,PLAGE,GRAPHPLAGE"
        TEMPLATE_SUMMARY = u"{solptname},{date},{clearsky},{peak},{peakpower},{mean},{median},{plage},{graph_plage}"

        try:
            for datafile in datafiles:
                csvdata = os.path.join(
                    MAIN_PATH[self.country.code], 'data/{0}.csv'.format(datafile))
                data = np.genfromtxt(csvdata, delimiter=',', dtype=('float64', 'float64', 'float64', 'S255', 'S255', 'int8', 'S255', 'S255','float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64'),
                                     names=True)

                fc_date = 'problem'
                summary = u''
                result = {}

                for i in range(0, data.size):
                    solpt = data[i]
                    fc_date = solpt[4]
                    result['solptname'] = u'{0}'.format(solpt[3].decode('utf8'))
                    result['clearsky'] = solpt[2]
                    result['date'] = fc_date
                    
                    ar_data = np.array(list(solpt)[10:])
                    result['peak'], result['peakpower'], result['mean'], result['median'], result[
                        'plage'], result['graph_plage'] = self._set_plage_apere(ar_data, fc_date)

                    summary += TEMPLATE_SUMMARY.format(**result) + u'\n'

                content = FILE_HEADER_SUMMARY + u'\n' + summary
                datafilename = self._set_names('summary_daily', fc_date)
                with open(os.path.join(MAIN_PATH[self.country.code], 'outputs/' + datafilename + '.csv'), 'w') as f:
                    f.write(content.encode('utf8'))

                if return_files:
                    self.generated_files.append({'filepath': os.path.join(
                        MAIN_PATH[self.country.code], 'outputs/'), 'filename': '{0}.csv'.format(datafilename)})

            treated = True

        except:
            treated = False

        finally:
            return treated
    
    def _generate_daily_summary_pdf(self, datafiles):
        """
        Load the xml summary
        Transform it inan HTML format
        Transform HTML in PDF
        """
        try:
            for datafile in datafiles:
                content, fc_date = self._generate_daily_xml_content(datafile, True)
                datafilename = self._set_names('summary_daily', fc_date)
                xslFileName = self.dbreport.get_xsl_filename()

                if xslFileName != None:
                    htmlcontent = self.apply_xsl_transformation(xslFileName, content)
                    with open(os.path.join(TEMP_ATTACH, datafilename + '.html'), 'w') as f:
                        f.write(htmlcontent.encode('latin1'))

                    os.system("wkhtmltopdf -q {0} {1}".format(
                        os.path.join(TEMP_ATTACH, datafilename + '.html'), os.path.join(TEMP_ATTACH, datafilename + '.pdf')))

                    self.generated_files.append(os.path.join(TEMP_ATTACH, datafilename + '.pdf'))

                else:
                    with open(os.path.join(TEMP_ATTACH, datafilename + '.xml'), 'w') as f:
                        f.write(content.encode('utf8'))

                    self.generated_files.append(os.path.join(TEMP_ATTACH, datafilename + '.xml'))

            treated = True

        except:
            treated = False

        finally:
            return treated

    def _generate_daily_summary_xml(self, datafiles, with_map=False):
        """
        Generate the xml file for rtbf television
        """
        try:
            for datafile in datafiles:
                content, fc_date = self._generate_daily_xml_content(datafile, with_map)
                datafilename = self._set_names('summary_daily', fc_date)
                
                xslFileName = self.dbreport.get_xsl_filename()

                if xslFileName != None:
                    xmlcontent = self.apply_xsl_transformation(xslFileName, content)
                
                else:
                    xmlcontent = content
                    
                with open(os.path.join(MAIN_PATH[self.country.code], 'outputs/' + datafilename + '.xml'), 'w') as f:
                    f.write(xmlcontent.encode('utf8'))

                self.generated_files.append({'filepath': os.path.join(
                    MAIN_PATH[self.country.code], 'outputs/'), 'filename': '{0}.xml'.format(datafilename)})

                treated = True

        except:
            treated = False

        finally:
            return treated

    def _generate_daily_xml_content(self, datafile, with_map=False):
        """
        Generate the XML content of the daily summary
        """
        TEMPLATE_XML = u"""\
<?xml version='1.0' encoding='utf-8' standalone='yes' ?> 
<daily_pv_forecast_report>
    <country_name>{country}</country_name>
    <date>{date}</date>
    <calc_date><![CDATA[{calc_date}]]></calc_date>
    <calc_time><![CDATA[{calc_time}]]></calc_time>
    <utc_offset>{utc_offset}</utc_offset>
    <image>{image_io}</image>
    <pv_points>
{pv_points}
    </pv_points>
</daily_pv_forecast_report>
"""
        PV_POINT_TEMPLATE = u"""\
        <solar_point>
            <name_fr><![CDATA[{solptname}]]></name_fr>
            <clearsky_textual_fr><![CDATA[{clearsky_textual}]]></clearsky_textual_fr>
            <peak>{peak}</peak>
            <graphical_plage>{graph_plage}</graphical_plage> 
        </solar_point>
"""

        try:
            csvdata = os.path.join(
                MAIN_PATH[self.country.code], 'data/{0}.csv'.format(datafile))
            data = np.genfromtxt(csvdata, delimiter=',', dtype=('float64', 'float64', 'float64', 'S255', 'S255', 'int8', 'S255', 'S255', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64'),
                                 names=True)
            
            fc_date = 'problem'
            pv_points = u''
            result = {}
            
            image_io = ''
            if with_map:
                with open(os.path.join(MAIN_PATH[self.country.code], 'outputs/{0}.png'.format(datafile)), "rb") as f:
                    myimage = f.read()
                    image_io = myimage.encode("base64")

            for i in range(0, data.size):
                solpt = data[i]
                fc_date = solpt[4]
                result['date'] = fc_date
#                 local_offset = self._set_country_offset_hour(fc_date)
                local_offset = self.country.get_country_offset_hour(datetime.date(int(fc_date[:4]), int(fc_date[5:7]), int(fc_date[8:10])))
                result['utc_offset'] = local_offset
                result['solptname'] = u'{0}'.format(solpt[3].decode('utf8'))
#                 result['clearsky'] = solpt[2]
                result['clearsky_textual'] = u'{0}'.format(
                    self._get_textual_clearsky(solpt[2]))
                result['peak'] = solpt[5] 
#                 result['plage'] = solpt[6] 
                result['graph_plage'] = solpt[7]
                
                pv_points += PV_POINT_TEMPLATE.format(**result)
            
            now = datetime.datetime.now() + datetime.timedelta(hours=local_offset)
            calc_date = u'{0:%d/%m/%Y}'.format(now)
            calc_time = u'{0:%H:%M}'.format(now)
            content = TEMPLATE_XML.format(
                country=self.country.name, date=fc_date, utc_offset=local_offset, pv_points=pv_points, image_io=image_io, calc_date=calc_date, calc_time=calc_time)

        except:
            content = False

        return content, fc_date
    
    def _generate_hourly_csv_4maps(self, pv, solar_point_details, datafilenames):
        """ 
        Create a csv file per date with all the solar points.
        """

        try:
            content, fc_date = self._generate_daily_data_4maps(pv, solar_point_details, datafilenames)
            datafilename = self._set_names('map_hourly', fc_date)

            with open(os.path.join(DATA_DIR[self.country.code], datafilename + '.csv'), 'w') as f:
                f.write(content.encode('utf8'))

            datafilenames.append(datafilename)

            treated = True

        except:
            treated = False

        finally:
            return treated, datafilenames

    def _generate_hourly_json_content(self, datafile):
        """
        Generate a json content for hourly maps on a web iframe
        We suppose the reference csv does contains only one date
        """
        fc_date = 'problem'
        try:
            csvdata = os.path.join(MAIN_PATH[self.country.code], 'data/{0}.csv'.format(datafile))
            data = np.genfromtxt(csvdata, delimiter=',', dtype=('float64', 'float64', 'float64', 'S255', 'S255', 'int8', 'S255', 'S255', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64'),
                                 names=True)
            """
            Pour définir start_hour et end_hour, parcourir les colonnes de data concernant les heures et prendre la première et la dernière ayant un total de l'énergie > 0
            On peut en profiter pour identifier la date concernée
            """
            ar_hours = []
            for i in range(0, data.size):
                fc_date = data[i][4]
                hours_row = [data[i][x] for x in range(10, 34)]
                ar_hours.append(hours_row)
            
            ar_hours = np.array(ar_hours)
            
            ar_hours = np.array(ar_hours)   
            start_hour = 0
            while (sum(ar_hours[:,start_hour]) == 0.0):
                start_hour = start_hour + 1
                if start_hour > 24:
                    break
            
            start_hour = start_hour + 1
            end_hour = 0
            while (sum(ar_hours[:,-end_hour]) == 0.0):
                end_hour = end_hour + 1
                if end_hour > 24:
                    break
                
            end_hour = 24 - end_hour + 1
            
            local_offset = self.country.get_country_offset_hour(datetime.date(int(fc_date[:4]), int(fc_date[5:7]), int(fc_date[8:10])))
            result = {}
            result['date'] = fc_date
            result['utc_offset'] = local_offset
            result['start_hour'] = start_hour
            result['end_hour'] = end_hour
            result['zpoints'] = {}
            for i in range(0, data.size):
                ptkey = 'pt{0}'.format(i)
                result['zpoints'][ptkey] = {}
                solpt = data[i]                
                result['zpoints'][ptkey]['longitude'] = solpt[8]
                result['zpoints'][ptkey]['latitude'] = solpt[9]
                result['zpoints'][ptkey]['solptname'] = u'{0}'.format(solpt[3].decode('utf8'))
                # ATTENTION valeurs calculée pour toute la journée pour affichage dans le popup
                result['zpoints'][ptkey]['clearsky_textual'] = u'{0}'.format(self._get_textual_clearsky(solpt[2]))
                result['zpoints'][ptkey]['peak'] = str(solpt[5])
                result['zpoints'][ptkey]['plage'] = solpt[6]
                result['zpoints'][ptkey]['graph_plage'] = solpt[7]
                      
            content = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)
            
        except Exception, e:
#             print e
            content = False
            fc_date = '{0}'.format(e)

        return content, fc_date, start_hour, end_hour

    def _generate_hourly_summary_json(self, datafiles):
        """
        JSON formatted summary report
        Daily summary to be used in a web page with hourly maps
        """
        treated = False
        start_hour = 1
        end_hour = 1
        try:
            for datafile in datafiles:
                jsoncontent, fc_date, start_hour, end_hour = self._generate_hourly_json_content(datafile)
                datafilename = self._set_names('summary_daily', fc_date)
                                    
                with open(os.path.join(APERE_IFRAME_PATH, datafilename + '.json'), 'w') as f:
                    f.write(jsoncontent.encode('utf8'))

                self.generated_files.append({'filepath': APERE_IFRAME_PATH, 'filename': '{0}.json'.format(datafilename)})

                treated = True

        except:
            treated = False

        finally:
            return treated, start_hour, end_hour


    def _generate_maps(self, datafiles, return_files, cleanup=True, start_hour=1, end_hour=24):
        """ 
        TODO all parameters should be defined per country

        Cleanup: it can be useful to use False value for debugging purposes. 
        In this case all vectors and rasters remains in the Grass database and they can be analyzed with the Grass GUI
        """
        try:
            HOUR_RANGE = range(start_hour, end_hour + 1)
            BE_SMOOTH = 0
            BE_TENSION = 40

            from energizair.io.grass7_session import Grass7Session

            mysession = Grass7Session(country='BE', debug=False)
            mysession.start_grass()
            # To be done only once
#             mysession.set_region()
#             mysession.remove_layer('vector', 'be_adm0')
#             mysession.insert_vector_shapefile(input=os.path.join(MAIN_PATH[self.country.code], 'be_31370/be_adm0.shp'), layer='be_adm0', output='be_adm0')
#             mysession.remove_layer('raster', 'MASK')
#             mysession.set_mask('be_adm0')
#             mysession.remove_layer('vector', 'be_adm2')
#             mysession.insert_vector_shapefile(input=os.path.join(MAIN_PATH[self.country.code], 'be_31370/be_adm2.shp'), layer='be_adm2', output='be_adm2')

            for datafile in datafiles:
                map_data_vector = '{0}'.format(datafile)
                # load data
                mysession.insert_vector_csv(
                    input=os.path.join(MAIN_PATH[self.country.code], 'data/{0}.csv'.format(datafile)), output=map_data_vector)
                
                if 'hourly' in datafile:                    
                    mypalette = 'palette_rtbf_10_hourly'
                    for hour in HOUR_RANGE:
                        map_data_raster = 'rst_{0}_{1}_s{2}_t{3}'.format(datafile, hour, BE_SMOOTH, BE_TENSION)
                        # create the interpolation raster
                        mysession.create_rst_interpolation_raster(
                            input=map_data_vector, elevation=map_data_raster, zcolumn='h{0}'.format(hour), smooth=BE_SMOOTH, tension=BE_TENSION, npmin=20, segmax=40)
                        # Apply color tables
                        mysession.set_color_palette(map='rst_{0}_{1}_s{2}_t{3}'.format(
                            datafile, hour, BE_SMOOTH, BE_TENSION), rules=os.path.join(MAIN_PATH[self.country.code], 'color_palettes/{0}'.format(mypalette)))
                        # Save the png file without the administrative map (map='')
                        result = mysession.save_png(filename=os.path.join(APERE_IFRAME_PATH, '{0}_{1}.png'.format(
                            datafile, hour)), raster=map_data_raster, map='')
        
                        if result and return_files:
                            self.generated_files.append(
                                {'filepath': APERE_IFRAME_PATH, 'filename': '{0}_{1}.png'.format(datafile, hour)})
                        
                        # Clean up
                        if cleanup:
                            mysession.remove_layer('raster', map_data_raster)                        
                    
                else:
                    mypalette = 'palette_rtbf_10_daily' 
                    map_data_raster = 'rst_{0}_s{1}_t{2}'.format(datafile, BE_SMOOTH, BE_TENSION)                   
                    # create the interpolation raster
                    mysession.create_rst_interpolation_raster(
                        input=map_data_vector, elevation=map_data_raster, zcolumn='power', smooth=BE_SMOOTH, tension=BE_TENSION, npmin=20, segmax=40)
                    # Apply color tables
                    mysession.set_color_palette(map='rst_{0}_s{1}_t{2}'.format(
                        datafile, BE_SMOOTH, BE_TENSION), rules=os.path.join(MAIN_PATH[self.country.code], 'color_palettes/{0}'.format(mypalette)))
                    # Save the png file
                    if start_hour > 1:
                        # this is the hourly report for the apere iframe and we want to save also the daily maps
                        result = mysession.save_png(filename=os.path.join(APERE_IFRAME_PATH, '{0}.png'.format(datafile)), raster=map_data_raster, map='be_adm2')
                        
                        if result and return_files:
                            self.generated_files.append({'filepath': APERE_IFRAME_PATH, 'filename': '{0}.png'.format(datafile)})
                            
                    else:
                        result = mysession.save_png(filename=os.path.join(MAIN_PATH[self.country.code], 'outputs/{0}.png'.format(
                        datafile)), raster=map_data_raster, map='be_adm2')
    
                        if result and return_files:
                            self.generated_files.append(
                                {'filepath': os.path.join(MAIN_PATH[self.country.code], 'outputs/'), 'filename': '{0}.png'.format(datafile)})
                            
                    # Clean up
                    if cleanup:
                        mysession.remove_layer('raster', map_data_raster)

                # Clean up
                if cleanup:
#                     mysession.remove_layer('raster', map_data_raster)
                    mysession.remove_layer('vector', map_data_vector)

            # End of Script
#             mysession.stop_grass()
            treated = True

        except:
            treated = False

        finally:
            return treated

    def _get_daily_meteonorm_tmy(self, month, day, solptid):
        """
         kWh/m² Meteonorm (total par jour) * 0,148 = kWh/m² PV (production clear sky)
        (production clear sky)*16/3 = kWh/kWp = Wh/Wp
        """
        # get the records for the given solar point and given day
        ctrl = TMY()
        records = ctrl.get_daily_tmy(month, day, solptid)
        daily_meteonorm_tmys = [rec.clsky_meteonorm for rec in records]
        hourly_corrections = [rec.clsky_apere_max_noon for rec in records if rec.hour == 12]
        # case of undefined value
        hourly_correction = 1.0
        if len(hourly_corrections) > 0:
            hourly_correction = hourly_corrections[0] / 10000.0        
            if hourly_correction <= 0.0:
                hourly_correction = 1.0
        
        # sum all hourly values for the daily value this is expressed in mWh\m²
        daily_clearsky = sum(daily_meteonorm_tmys)

        # transform mWh\m² in kWh\kWp
        result_kWhperkWp = (daily_clearsky / 1000000) * 0.148 * 16.0 / 3.0

        return result_kWhperkWp, hourly_correction

    def _get_textual_clearsky(self, clearsky_percent, lang='fr'):
        """
        Translate a clearsky percentage in words
        """
        ret_text = ''
        clearsky_percent = float(clearsky_percent)
        if clearsky_percent >= 0.0 and clearsky_percent < 20.0:
            refs = {'fr': u'Médiocre'}
            ret_text = refs[lang]
        elif clearsky_percent >= 20.0 and clearsky_percent < 40.0:
            refs = {'fr': u'Faible'}
            ret_text = refs[lang]
        elif clearsky_percent >= 40.0 and clearsky_percent < 60.0:
            refs = {'fr': u'Moyen'}
            ret_text = refs[lang]
        elif clearsky_percent >= 60.0 and clearsky_percent < 80.0:
            refs = {'fr': u'Bon'}
            ret_text = refs[lang]
        elif clearsky_percent >= 80.0:
            refs = {'fr': u'Excellent'}
            ret_text = refs[lang]
        else:
            refs = {'fr': u'Non défini'}
            ret_text = refs[lang]

        return ret_text

#     def _set_country_offset_hour(self, fc_date):
#         # define belgian offset from utc
#         utc = pytz.utc
#         country_tz = timezone('Europe/Brussels')
#         if self.country.code == "GB":
#             country_tz = timezone('Europe/London')
# 
#         fmt = '%z'
#         utc_dt = datetime.datetime(
#             int(fc_date[:4]), int(fc_date[5:7]), int(fc_date[8:10]), 0, 0, 0, tzinfo=utc)
#         loc_dt = utc_dt.astimezone(country_tz)
# 
#         hr_offset = int(loc_dt.strftime(fmt)) / 100
# 
#         return hr_offset

    def _set_hourly_color_palette(self, correction=1.0):
        """
        Retrieve from the tmy table the percentage of change to apply to 
        the reference color palette, this is function of the date.
        Modify the reference color palette using this percentage
        Save it 
        """
        try:
            map_palette = 'palette_rtbf_10_hourly'
            ref_palette = 'palette_rtbf_10_hourly_ref'
            ref_file = os.path.join(MAIN_PATH[self.country.code], 'color_palettes/{0}'.format(ref_palette))
            
            with open(os.path.join(MAIN_PATH[self.country.code], 'color_palettes/{0}'.format(map_palette)), "w") as fmap:
                with open(ref_file, 'r') as fref:
                    data = fref.readlines()
                
                    for idx, line in enumerate(data):
                        words = line.split()
                        if idx > 0 and idx < (len(data)-1):
                            fmap.write('{0} {1}\n'.format(float(words[0])*correction, words[1]))
                        else:
                            fmap.write('{0} {1}\n'.format(float(words[0]), words[1]))
            
            return True
        
        except:
            raise EnergizAIRColorPaletteError('Failed creating a new hourly color palette')
            

    def _set_names(self, prefix, date, postfix=''):
        """ 
        set the name of the map to be generated, the raster will have the same name.
        For RTBF we want to keep always the same name for today and tomorrow.
        """
        if len(postfix) > 0:
            postfix = '_' + postfix

        dujour = datetime.date.today()
        demain = dujour + datetime.timedelta(days=1)

        if date == dujour.strftime("%Y-%m-%d"):
            datix = 'today'

        elif date == demain.strftime("%Y-%m-%d"):
            datix = 'tomorrow'

        else:
            datix = date.replace('-', '_')

        myname = '{0}_{1}{2}'.format(prefix, datix, postfix)

        return myname

    def _set_plage(self, ar_data, fc_date):
        """ 
        plage is an interval of hours.

        First approach : 
        look for the period of hours above median and mean value including
        the peak of the day. 
        In case we have 2 peaks we select the longest period.

        """
        # define country offset from utc
#         local_offset = self._set_country_offset_hour(fc_date)
        local_offset = self.country.get_country_offset_hour(datetime.date(int(fc_date[:4]), int(fc_date[5:7]), int(fc_date[8:10])))
        # define reference points
        index_peak = np.argmax(ar_data, axis=0)        
        peak = index_peak + local_offset
        peakpower = ar_data[index_peak]
        non_zero_hours = ar_data.nonzero()
        non_zero_data = ar_data[non_zero_hours]
        average = np.mean(non_zero_data, axis=0)
        median = np.median(non_zero_data, axis=0)
        # define plage as all hours where production is higher than average and median
        # record in which plage interval we have the peak
        id_opt = 1
        plage = {}
        plage[id_opt] = {'hours': [], 'has_peak': False}
        id_hours = 0 + local_offset
        for moment in ar_data:
            if moment >= average and moment >= median:
                plage[id_opt]['hours'].append(id_hours)
                if moment == peakpower:
                    plage[id_opt]['has_peak'] = True

            else:
                id_opt = id_opt + 1
                plage[id_opt] = {'hours': [], 'has_peak': False}

            id_hours = id_hours + 1

        # short plage: select the best plage interval
        #
        # count how many intervals have a peak
        # if we have more than one, select the largest
        # else give the interval of the one containing the peak
        #
        best_intervals = [bestid for bestid in plage.keys() if plage[bestid]['has_peak']]
        
        if len(best_intervals) == 1:
            myplage = plage[best_intervals[0]]['hours']

        else:
            myplage = []
            for item in best_intervals:
                if len(plage[item]['hours']) >= len(myplage):
                    myplage = plage[item]['hours']

        if peak not in myplage:
            # this does not happens very oftem multiple peaks on a day
            # find at which hour we have the peakpower
            peak = 0
            for item in myplage:
                if ar_data[item - local_offset] == peakpower:
                    peak = item

        formatted_plage = u'[{0}-{1}]'.format(myplage[0], myplage[-1])

        # define graphic plage
        id_hours = 0 + local_offset
        graphic_plage = u''
        for moment in ar_data:
            if id_hours in myplage:
                if moment == peakpower:
                    graphic_plage += u'M'
                else:
                    graphic_plage += u'o'

            else:
                graphic_plage += u'_'

            id_hours = id_hours + 1

        return peak, formatted_plage, graphic_plage

    def _set_plage_apere(self, ar_data, fc_date):
        """ 
        plage is an interval of hours

        """

#         local_offset = self._set_country_offset_hour(fc_date)
        local_offset = self.country.get_country_offset_hour(datetime.date(int(fc_date[:4]), int(fc_date[5:7]), int(fc_date[8:10])))

        # define reference points
        index_peak = np.argmax(ar_data, axis=0)
        peak = index_peak + local_offset
        peakpower = ar_data[index_peak]
        non_zero_hours = ar_data.nonzero()
        non_zero_data = ar_data[non_zero_hours]
        average = np.mean(non_zero_data, axis=0)
        median = np.median(non_zero_data, axis=0)
        # define plage as all hours where production is higher than average and median
        plage = []
        graphic_plage = u''
        idx = 0 + local_offset
        for moment in ar_data:
            if moment >= average and moment >= median:
                plage.append(idx)
                if moment == peakpower:
                    graphic_plage += u'M'
                else:
                    graphic_plage += u'o'

            else:
                graphic_plage += u'_'

            idx = idx + 1

        formatted_plage = u'['
        ref = 0
        for item in plage:
            if item > ref + 1:
                if ref == 0:
                    formatted_plage += str(item)
                else:
                    formatted_plage += u'-' + str(ref) + u'|' + str(item)

            ref = item

        formatted_plage += u'-' + str(ref) + u']'

        return peak, peakpower, average, median, formatted_plage, graphic_plage
