

from PyQt4.QtCore import *
from PyQt4.QtGui import *
#from qgis.core import *
#from qgis.gui import *
import resources
from qgSurf_dialog import qgSurfDialog
# from qgs_tools.ptmaptool import PointMapTool


class qgSurf_gui(object):    

    def __init__( self, interface ):

        self.interface = interface
        self.main_window = self.interface.mainWindow()
        self.canvas = self.interface.mapCanvas()


    def initGui( self ):

        self.plugin = QAction( QIcon( ":/plugins/qgSurf/icons/qgsurf.png" ), "qgSurf", self.main_window )
        self.plugin.setWhatsThis( "Calculate intersection between DEM and plane" )                   
        self.plugin.triggered.connect( self.run )

        self.interface.addToolBarIcon( self.plugin )
        self.interface.addPluginToMenu( "&qgSurf", self.plugin )

   
    def run(self):
     
        dlg = qgSurfDialog( self.canvas, self.plugin )
        dlg.show()
        dlg.exec_()


    def unload(self):

        self.interface.removePluginMenu( "&qgSurf", self.plugin )
        self.interface.removeToolBarIcon( self.plugin )




        

