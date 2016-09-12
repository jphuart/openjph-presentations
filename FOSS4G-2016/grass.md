## GRASS



### How to find your way in GRASS

  * Launch the GUI
  * The help is disappointing, but finally well done
  * Selecting the GIS Database directory
  * Create your LOCATION
  * Create your MAPSET
  * Start the GRASS session



### Add the vector map of Belgium

My country:

	v.in.ogr input=/home/jph/dev/aaa-foss4g/gis_data/be_31370/be_adm0.shp layer=be_adm0 output=be_adm0
	
The same with administrative divisions:

	v.in.ogr input=/home/jph/dev/aaa-foss4g/gis_data/be_31370/be_adm2.shp layer=be_adm2 output=be_adm2



### Setup your project region

The geographic area in which GRASS should work:

  * geographical projection (e.g. Belgian Lambert 72, etc)
  * geographical extension, i.e. the North/South/East/West limits of the area covered
  * number of columns and number of rows for the data
  * resolution, i.e. the extension divided by the number of rows (N-S resolution), respectively columns (E-W resolution).

In other words, **_you need a good friend_** to set the displayed region: 

	g.region n=243900 s=21200 e=295950 w=23700 rows=4454 cols=5445 nsres=50 ewres=50



### Add the data as vector point map

Let's test with the power production at 10 o'clock:

	v.in.ascii --overwrite input=/home/jph/dev/aaa-foss4g/gis_data/data/test_map_2015-08-11_10.csv output=data_map_2015_08_11_10 separator=comma skip=1



### Build a raster from the vector point map

We have chosen the rst interpolation:

	v.surf.rst --overwrite input=data_map_2015_08_11_10@mymapset zcolumn=dbl_3 elevation=rst_20150811H10 smooth=1



### Add a mask

I want to limit my raster to the country limits:

	r.mask --overwrite vector=be_adm0@mymapset
	
To directly build the raster including the mask:
	
	v.surf.rst --overwrite input=test_map_2015_08_11_10@mymapset zcolumn=dbl_3 elevation=rst_20150811H10 mask=MASK@mymapset smooth=1



### Save the result as an image

<div style="text-align:center;"><img src="../images/my_first_image.png" alt="My first result" height="100%"></div>



<div style="text-align:center;"><img src="../images/sat20160811.gif" alt="satellite meteo picture" height="100%"></div>
