"""
/***************************************************************************
 qgSurf - plugin for Quantum GIS

 Processing of geological planes and surfaces

                              -------------------
        begin                : 2011-12-21
        copyright            : (C) 2011-2018 by Mauro Alberti
        email                : alberti.m65@gmail.com

 ***************************************************************************/

# licensed under the terms of GNU GPL 3

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 3 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

# -*- coding: utf-8 -*-


from __future__ import absolute_import


from builtins import object

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *

from . import resources

from .BestFitPlaneTool import bestfitplane_QWidget
from .DEMPlaneIntersectionTool import plane_dem_intersection_QWidget
from .AboutDialog import about_Dialog

from .config.tools import *
from .pygsf.libs_utils.qt.tools import *


class qgSurf_gui(object):    

    def __init__(self, interface):

        self.interface = interface
        self.main_window = self.interface.mainWindow()
        self.canvas = self.interface.mapCanvas()

    def initGui(self):

        self.bestfitplane_geoproc = make_qaction(
            params=bestfitplane_tool_params,
            parent=self.main_window)

        self.bestfitplane_geoproc = QAction(QIcon(":/plugins/qgSurf/icons/bestfitplane.png"), "Best fit plane", self.main_window)
        self.bestfitplane_geoproc.setWhatsThis("Best fit plane from points")
        self.bestfitplane_geoproc.triggered.connect(self.run_bestfitplane_geoproc)
        self.interface.addPluginToMenu("&qgSurf", self.bestfitplane_geoproc)
        
        self.demplaneinters_geoproc = QAction(QIcon(":/plugins/qgSurf/icons/qgsurf.png"), "DEM-plane intersection", self.main_window)
        self.demplaneinters_geoproc.setWhatsThis("Intersection of planar surfaces with topography")
        self.demplaneinters_geoproc.triggered.connect(self.run_demplaneinters_geoproc)
        self.interface.addPluginToMenu("&qgSurf", self.demplaneinters_geoproc)
        
        self.qgsurf_about = QAction(QIcon(":/plugins/qgSurf/icons/about.png"), "About", self.main_window)
        self.qgsurf_about.setWhatsThis("qgSurf about")                   
        self.qgsurf_about.triggered.connect(self.run_qgsurf_about)
        self.interface.addPluginToMenu("&qgSurf", self.qgsurf_about)
 
    def bfp_win_closeEvent(self, event):

        for mrk in self.bestfitplane_Qwidget.bestfitplane_point_markers:
            self.bestfitplane_Qwidget.canvas.scene().removeItem(mrk)
                    
        try:
            QgsProject.instance().layerWasAdded.disconnect(self.bestfitplane_Qwidget.refresh_raster_layer_list)
        except:
            pass

        try:
            QgsProject.instance().layerRemoved.disconnect(self.bestfitplane_Qwidget.refresh_raster_layer_list)
        except:
            pass
        
        try:      
            self.bestfitplane_Qwidget.bestfitplane_PointMapTool.canvasClicked.disconnect(self.bestfitplane_Qwidget.set_bfp_input_point)
        except:
            pass
               
        try:
            QgsProject.instance().layerWasAdded.disconnect(self.bestfitplane_Qwidget.refresh_inpts_layer_list)
        except:
            pass
                
        try:            
            QgsProject.instance().layerRemoved.disconnect(self.bestfitplane_Qwidget.refresh_inpts_layer_list)
        except:
            pass
                
        try:
            self.bestfitplane_Qwidget.bestfitplane_PointMapTool.leftClicked.disconnect(self.bestfitplane_Qwidget.set_bfp_input_point) 
        except:
            pass   
                       
    def run_bestfitplane_geoproc(self):

        bestfitplane_DockWidget = QDockWidget('Best fit plane', self.interface.mainWindow())        
        bestfitplane_DockWidget.setAttribute(Qt.WA_DeleteOnClose)
        bestfitplane_DockWidget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        self.bestfitplane_Qwidget = bestfitplane_QWidget(self.canvas, self.bestfitplane_geoproc)
        bestfitplane_DockWidget.setWidget(self.bestfitplane_Qwidget)
        bestfitplane_DockWidget.destroyed.connect(self.bfp_win_closeEvent)                  
        self.interface.addDockWidget(Qt.RightDockWidgetArea, bestfitplane_DockWidget)

    def run_demplaneinters_geoproc(self):

        plane_geoprocessing_DockWidget = QDockWidget('DEM-plane intersection', self.interface.mainWindow())
        plane_geoprocessing_DockWidget.setAttribute(Qt.WA_DeleteOnClose)
        plane_geoprocessing_DockWidget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        self.planeProcess_Qwidget = plane_dem_intersection_QWidget(self.canvas, self.demplaneinters_geoproc)
        plane_geoprocessing_DockWidget.setWidget(self.planeProcess_Qwidget)
        plane_geoprocessing_DockWidget.destroyed.connect(self.pdint_closeEvent)
        self.interface.addDockWidget(Qt.RightDockWidgetArea, plane_geoprocessing_DockWidget)

    def pdint_closeEvent(self, event):

        for mrk in self.planeProcess_Qwidget.intersection_markers_list:
            self.planeProcess_Qwidget.canvas.scene().removeItem(mrk)

        if self.planeProcess_Qwidget.intersection_sourcepoint_marker is not None:
            self.planeProcess_Qwidget.canvas.scene().removeItem(self.planeProcess_Qwidget.intersection_sourcepoint_marker) 
            
        try:
            self.planeProcess_Qwidget.intersection_PointMapTool.canvasClicked.disconnect(self.planeProcess_Qwidget.update_intersection_point_pos)
        except:
            pass  


        
    def run_qgsurf_about(self):
     
        qgsurf_about_dlg = about_Dialog()
        qgsurf_about_dlg.show()
        qgsurf_about_dlg.exec_()
        
    def unload(self):

        self.interface.removePluginMenu("&qgSurf", self.bestfitplane_geoproc)
        self.interface.removePluginMenu("&qgSurf", self.demplaneinters_geoproc)
        self.interface.removePluginMenu("&qgSurf", self.qgsurf_about)


        

