# -*- coding: utf-8 -*-


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *


class PointMapTool( QgsMapToolEmitPoint):
    

    def __init__( self, canvas, button ):
        
        super( PointMapTool, self ).__init__( canvas )
        self.canvas = canvas
        self.cursor = QCursor( Qt.CrossCursor )
        self.button = button           
    
    
    def activate( self ):
        
        QgsMapTool.activate( self )
        self.canvas.setCursor( self.cursor )
        self.button.setCheckable( True )
        self.button.setChecked( True )


    def setCursor( self, cursor ):
        
        self.cursor = QCursor( cursor )


    def canvasDoubleClickEvent( self, event ):
        
        pass

