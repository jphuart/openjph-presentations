# -*- coding: utf-8 -*-
""" Module of EU06 Maps report for RTBF """

from energizair.report.eu06_map_report_main import EU06MapReport


__author__ = "Jean Pierre Huart"
__email__ = "jph@openjph.be"
__copyright__ = "Copyright 2016, Jean Pierre Huart"
__license__ = "GPLv3"
__date__ = "2016-02-27"
__version__ = "1.0"
__status__ = "Development"


class EU06MapReportRtbf(EU06MapReport):
    """
    A EU06 report for EnergizAIR.
    This report generates files on the server. The list of their paths and names are returned by the generate function.

    see EU06MapReport for parameters

    """

    def generate(self, pdate, storage):
        """
        Generate all the report data: list of files that has been generated.

        :param pdate: The date of the report.
        :type pdate: datetime.date
        :param storage: The storage used by the model (normally the same as the server one)
        :type storage: Instance of HDF5TimeSeriesStorageClient
        :return: values resulting of the calculation of all the defined indicators formatted as defined in Report
        :rtype: formatted data, generally XML or HTML string

        """
        self.generated_files = []
        """ Generate the contents of the report for the given date. """
        indicator_values = self.get_indicator_values(pdate, storage)

        """ solar PV """
        solar_point_details = self.dbreport.get_solar_point_details()
        pv = indicator_values.pop('map_pv_eu06')

        datafilenames = []
        """ generate daily data for the maps """
        result, datafilenames = self._generate_daily_csv_4maps(
            pv, solar_point_details, datafilenames)

        """ generate the maps and return them """
        result = self._generate_maps(datafilenames, True, True)
        """ generate the summary in xml format """
        result = self._generate_daily_summary_xml(datafilenames, False)

        """ delete the csv files """
        result = self._delete_csv_data_files()

        return self.generated_files
