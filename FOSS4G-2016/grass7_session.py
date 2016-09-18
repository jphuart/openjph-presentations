# -*- coding: utf-8 -*-
"""
energizair.io.grass7_session

Based on https://grasswiki.osgeo.org/wiki/Working_with_GRASS_without_starting_it_explicitly#Python:_GRASS_GIS_7_with_existing_location

Class to start a Grass session using the installed grass.
Tested only with grass version 7.

"""

__author__ = 'jph'
__email__ = 'jph@openjph.be'
__copyright__ = 'Copyright 2016, Jean Pierre Huart'
__license__ = 'GPLv3'
__date__ = '2016-03-03'
__version__ = '1.0'
__status__ = 'Development'

import os
import sys
import subprocess
from energizair.config import ENERGIZAIR_PATH

COUNTRY_PATHS = {'BE': os.path.join(ENERGIZAIR_PATH, 'belgium/')}
COUNTRY_LOCATIONS = {'BE': 'belgium31370'}
COUNTRY_MAPSETS = {'BE': 'apere0'}
    
    
class Grass7Session(object):
    """
    Instantiate a GRASS session and propose methods used by EnergizAIR
    for map generation on png format.
    This works only on Linux, for other OS check 

    https://grasswiki.osgeo.org/wiki/Working_with_GRASS_without_starting_it_explicitly#Python:_GRASS_GIS_7_with_existing_location

    """

    def __init__(self, country, debug=True):
        """
        Each country will have it's own grass database 
        thus it's own path, location and mapset
        """
        self.country = country
        self.debug = debug
        # The following is valid only for Linux
        self.grass7bin = 'grass70'
        # define GRASS DATABASE
        # add your path to grassdata (GRASS GIS database) directory
        self.gisdb = os.path.join(COUNTRY_PATHS[country], "grassdb")
        # specify (existing) location and mapset
        self.location = COUNTRY_LOCATIONS[country]
        self.mapset = COUNTRY_MAPSETS[country]

        return

    def start_grass(self):
        # query GRASS 7 itself for its GISBASE
        startcmd = [self.grass7bin, '--config', 'path']

        p = subprocess.Popen(startcmd
                            , shell=False
                            , stdout=subprocess.PIPE
                            , stderr=subprocess.PIPE)
        out, err = p.communicate()
        if p.returncode != 0:
            print >>sys.stderr, "ERROR: Cannot find GRASS GIS 7 start script (%s)" % startcmd
            sys.exit(-1)

        self.gisbase = out.strip('\n\r')

        # Set GISBASE environment variable
        os.environ['GISBASE'] = self.gisbase
        # the following not needed with trunk
        os.environ['PATH'] += os.pathsep
        os.environ['PATH'] += os.path.join(self.gisbase, 'extrabin')
        # add path to GRASS addons
        home = os.path.expanduser("~")
        os.environ['PATH'] += os.pathsep 
        os.environ['PATH'] += os.path.join(home
                                          , '.grass7'
                                          , 'addons'
                                          , 'scripts')

        # define GRASS-Python environment
        gpydir = os.path.join(self.gisbase, "etc", "python")
        sys.path.append(gpydir)

        # DATA
        # Set GISDBASE environment variable
        os.environ['GISDBASE'] = self.gisdb

        import grass.script.setup as gsetup
        # launch session
        gsetup.init(self.gisbase, self.gisdb, self.location, self.mapset)

        import grass.script as gscript
        self.gscript = gscript
        return

    def stop_grass(self):
        self.gscript.message('End of GRASS script.')
        sys.exit(0)
        return

if __name__ == "__main__":
    # Small self test
    mysession = Grass7Session()
    mysession.start_grass()
    mysession.gscript.message('Current GRASS GIS 7 environment:')
    print mysession.gscript.gisenv()
    mysession.stop_grass()
