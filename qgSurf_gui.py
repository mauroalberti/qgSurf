

"""
Some code modified after: profiletool, script: profileplugin.py

#-----------------------------------------------------------
# 
# Profile
# Copyright (C) 2008  Borys Jurgiel
# Copyright (C) 2012  Patrice Verchere
#-----------------------------------------------------------
# 
# licensed under the terms of GNU GPL 2
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# 
#---------------------------------------------------------------------
"""


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
        QObject.connect( self.plugin, SIGNAL("triggered()"), self.run )

        self.interface.addToolBarIcon( self.plugin )
        self.interface.addPluginToMenu( "&qgSurf", self.plugin )

   
    def run(self):
     
        dlg = qgSurfDialog( self.canvas, self.plugin )
        dlg.show()
        dlg.exec_()


    def unload(self):

        self.interface.removePluginMenu( "&qgSurf", self.plugin )
        self.interface.removeToolBarIcon( self.plugin )




        

