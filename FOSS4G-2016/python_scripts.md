## Python Scripts



## Scripting GRASS

[https://grasswiki.osgeo.org/wiki/Working_with_GRASS_without_starting_it_explicitly](https://grasswiki.osgeo.org/wiki/Working_with_GRASS_without_starting_it_explicitly#Python:_GRASS_GIS_7_with_existing_location)

The EnergizAIR <a href="grass7_session.py">GRASS session class</a>.

	mysession = Grass7Session()
    mysession.start_grass()
    mysession.gscript.message('Current GRASS GIS 7 environment:')
    print mysession.gscript.gisenv()
    """ Do what you want """
    
Now you have access to **gscript.run_command()** to run the following functions.



## Generate maps

#### Add the PV forecasts as vector point map

    def insert_vector_csv(self, input, output):
        columns = 'long double precision , lat double precision, power double precision, name varchar(255), date varchar(20), peak integer, plage varchar(255), grphplage varchar(50), maplon double precision , maplat double precision, h1 double precision,h2 double precision,h3 double precision,h4 double precision,h5 double precision,h6 double precision,h7 double precision,h8 double precision,h9 double precision,h10 double precision,h11 double precision,h12 double precision,h13 double precision,h14 double precision,h15 double precision,h16 double precision,h17 double precision,h18 double precision,h19 double precision,h20 double precision,h21 double precision,h22 double precision,h23 double precision, h24 double precision'
        result = self.gscript.run_command(
        				'v.in.ascii'
						, overwrite=True
						, input=input
						, separator='comma'
						, skip=1
						, output=output
						, columns=columns
						, quiet=not self.debug)



#### Build a raster from the vector point map

	def create_rst_interpolation_raster(self, input, elevation, zcolumn, 
							smooth=0, tension=40, npmin=20, segmax=40):

    	result = self.gscript.run_command(
    						'v.surf.rst'
							, overwrite=True
							, input='{0}@{1}'.format(input, self.mapset)
							, zcolumn=zcolumn
							, elevation=elevation
							, mask='MASK@{0}'.format(self.mapset)
							, smooth=smooth
							, tension=tension
							, npmin=npmin
							, segmax=segmax
							, quiet=not self.debug)



#### Define the color palette

Define the palette rules and colors in a separate file:
	
	0 78:148:228
	10.0 78:198:228
	20.0 21:177:98
	30.0 37:211:24
	40.0 122:237:20
	50.0 218:255:10
	60.0 255:229:10
	70.0 255:177:10
	80.0 255:99:5
	90.0 188:38:13
	150.0 188:38:13

Pass it to the python script (rules):

	def set_color_palette(self, map, rules):
	    result = self.gscript.run_command(
	    				'r.colors'
						, map='{0}@{1}'.format(map, self.mapset)
						, rules=rules
						, quiet=not self.debug)




#### Add a mask

	def set_mask(self, name):
        result = self.gscript.run_command(
        				'r.mask',
						, overwrite=True,
						, vector='{0}@{1}'.format(name, self.mapset)
						, quiet=not self.debug)



#### Save the map in a png file with transparent background

    def save_png(self, filename, raster, map, height=960, width=1280):
        # SETTINGS for PNG DRIVER
        os.system('rm {0}'.format(filename))
        os.environ['GRASS_RENDER_IMMEDIATE'] = 'png'
        os.environ['GRASS_RENDER_FILE'] = filename
        os.environ['GRASS_RENDER_FILE_READ'] = 'TRUE'
        os.environ['GRASS_RENDER_TRANSPARENT'] = 'TRUE'
        os.environ['GRASS_RENDER_HEIGHT'] = str(height)
        os.environ['GRASS_RENDER_WIDTH'] = str(width)
 
        self.gscript.run_command('d.rast'
        						, map='{0}@{1}'.format(raster, self.mapset)
        						, quiet=not self.debug)
        						
        self.gscript.run_command('d.vect'
        						, map='{0}@{1}'.format(map, self.mapset)
        						, color='white'
        						, fill_color='none'
        						, quiet=not self.debug)



#### Save all values as XML and json array

  * To be able to build friendly reports for the radio stations.
  * To pass values to the leaflet Iframe for popups.



#### Build a PDF friendly report

    """ Load the xml summary """
    content, fc_date = self._generate_daily_xml_content(datafile, True)
    
	""" Transform it in HTML format with XSL stylesheet """
    htmlcontent = self.apply_xsl_transformation('radio_report.xsl', content)
    with open('report.html', 'w') as f:
        f.write(htmlcontent.encode('latin1'))
	
	""" Transform HTML in PDF """
    os.system("wkhtmltopdf -q {0} {1}".format('report.html', 'report.pdf'))
    
<br>_NB to insert the image into the xml, it is encoded in base64_

	with open('mymap.png'), "rb") as f:
	    myimage = f.read()
	    image_io = myimage.encode("base64")



<div style="text-align:center;"><img src="../images/summary_daily_today.png" alt="daily summary" height="700"></div>
