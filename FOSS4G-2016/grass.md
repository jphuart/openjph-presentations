# GRASS


## How to find your way in GRASS

  * Launch the GUI
  * The help is well done
  * Selecting the GIS Database directory
  * Create your LOCATION
  * Create your MAPSET
  * Start the GUI
  
## Setup your project

Region: g.region n=243900 s=21200 e=295950 w=23700 rows=4454 cols=5445 nsres=50 ewres=50

#             mysession.set_region()
#             mysession.insert_vector_shapefile(input=os.path.join(MAIN_PATH[self.country.code], 'be_31370/be_adm0.shp'), layer='be_adm0', output='be_adm0')
#             mysession.set_mask('be_adm0')
#             mysession.insert_vector_shapefile(input=os.path.join(MAIN_PATH[self.country.code], 'be_31370/be_adm2.shp'), layer='be_adm2', output='be_adm2')

## Add the map of Belgium

v.in.ogr input=/home/jph/dev/aaa-foss4g/gis_data/be_31370/be_adm0.shp layer=be_adm0 output=be_adm0
v.in.ogr input=/home/jph/dev/aaa-foss4g/gis_data/be_31370/be_adm2.shp layer=be_adm2 output=be_adm2


## Add the data as vector point map

v.in.ascii --overwrite input=/home/jph/dev/aaa-foss4g/gis_data/data/test_map_2015-08-11_8.csv output=data_map_2015_08_11_8 separator=comma skip=1


## Build a raster from the vector point map

v.surf.rst --overwrite input=data_map_2015_08_11_8@mymapset zcolumn=dbl_3 elevation=rst_20150811H8 smooth=1


## Add a mask

r.mask --overwrite vector=be_adm0@mymapset
v.surf.rst --overwrite input=test_map_2015_08_11_8@mymapset zcolumn=dbl_3 elevation=rst_20150811H8 mask=MASK@mymapset smooth=1


## Save the result as an image