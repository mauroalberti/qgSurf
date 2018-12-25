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
from builtins import zip
from builtins import str
from builtins import range

from typing import Tuple

import os
from math import sqrt, sin, cos, tan, atan, degrees, radians

import numpy as np

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *

from qgis.core import *
from qgis.gui import *
    
from osgeo import ogr

#from .geosurf.geoio import read_dem
#from .geosurf.spatial import Point_2D, Segment_2D, Vector_2D, GeolPlane
#from .geosurf.intersections import Intersection_Parameters, Intersections

from .pygsf.topography.plane_intersect import plane_dem_intersection
from .pygsf.orientations.orientations import Plane, Direct
from .pygsf.libs_utils.gdal.gdal import try_read_raster_band
from .pygsf.spatial.rasters.geoarray import GeoArray
from .pygsf.libs_utils.qgis.qgs_tools import loaded_raster_layers, qgs_project_xy, qgs_project_point, qgs_point
from .pygsf.libs_utils.qgis.qgs_tools import PointMapToolEmitPoint
from .pygsf.spatial.vectorial.vectorial import Point, Segment


class DemPlaneIntersectionWidget(QWidget):
    """
    Constructor
    
    """

    line_colors = [ "white", "red", "blue", "yellow", "orange", "brown",]
    dem_default_text = '--  required  --'

    def __init__(self, tool_nm, canvas, plugin_qaction):

        super(DemPlaneIntersectionWidget, self).__init__()

        self.tool_nm = tool_nm
        self.canvas, self.plugin = canvas, plugin_qaction

        self.init_params()
        self.setup_gui() 

    def init_params(self):

        self.reset_values() 
        self.previousTool = None        
        self.geoarray = None
        self.input_points = None
        self.intersection_PointMapTool = None         
        self.intersection_markers_list = []

    def setup_gui(self):

        dialog_layout = QVBoxLayout()
        main_widget = QTabWidget()        
        main_widget.addTab(self.setup_fplane_tab(), "Processing")         
        main_widget.addTab(self.setup_help_tab(), "Help")
        
        dialog_layout.addWidget(main_widget)                                     
        self.setLayout(dialog_layout)                    
        self.adjustSize()                       
        self.setWindowTitle('qgSurf - DEM-plane intersection')        

    def setup_fplane_tab(self):
        
        plansurfaceWidget = QWidget()  
        plansurfaceLayout = QVBoxLayout()        
        plansurfaceLayout.addWidget(self.setup_source_dem())         
        plansurfaceLayout.addWidget(self.setup_tabs())                                       
        plansurfaceWidget.setLayout(plansurfaceLayout) 
        return plansurfaceWidget 

    def setup_source_dem(self):

        sourcedemWidget = QWidget()

        sourcedemLayout = QGridLayout()

        self.raster_refreshlayers_pButton = QPushButton("Update raster layer list")
        self.raster_refreshlayers_pButton.clicked[bool].connect(self.refresh_raster_layer_list)
        self.raster_refreshlayers_pButton.setEnabled(True)
        sourcedemLayout.addWidget( self.raster_refreshlayers_pButton, 0, 0, 1, 3 )

        sourcedemLayout.addWidget(QLabel("Choose current DEM layer"), 1, 0, 1, 1)
        self.define_dem_QComboBox = QComboBox()
        self.define_dem_QComboBox.addItem(self.dem_default_text)
        sourcedemLayout.addWidget(self.define_dem_QComboBox, 1, 1, 1, 2)

        self.refresh_raster_layer_list()

        sourcedemWidget.setLayout(sourcedemLayout)
        return sourcedemWidget

    def setup_tabs(self):  

        intersectionWidget = QWidget() 
        intersectionLayout = QVBoxLayout() 
        intersection_toolbox = QToolBox()
        intersection_toolbox.addItem (self.setup_geographicdata_sect(), 'Geographic parameters')
        intersection_toolbox.addItem (self.setup_geologicdata_sect(), 'Geological parameters')
        intersection_toolbox.addItem (self.setup_output_sect(), 'Output')             
        intersectionLayout.addWidget(intersection_toolbox)
        intersectionWidget.setLayout(intersectionLayout)        
        return intersectionWidget

    def setup_help_tab(self):
        
        qwdtHelp = QWidget()
        qlytHelp = QVBoxLayout()

        # About section

        qtbrHelp = QTextBrowser(qwdtHelp)
        url_path = "file:///{}/help/help_di.html".format(os.path.dirname(__file__))
        qtbrHelp.setSource(QUrl(url_path))
        qtbrHelp.setSearchPaths(['{}/help'.format(os.path.dirname(__file__))])
        qlytHelp.addWidget(qtbrHelp)

        qwdtHelp.setLayout(qlytHelp)

        return qwdtHelp

    def setup_geographicdata_sect(self):        
        
        inputWidget = QWidget()  
        inputLayout = QGridLayout()        
        self.intersection_definepoint_pButton = QPushButton("Set source point in map")
        self.intersection_definepoint_pButton.clicked[bool].connect(self.set_intersection_point)        
        inputLayout.addWidget(self.intersection_definepoint_pButton, 0, 0, 1, 3)        

        self.intersection_resetsrcpt_pButton = QPushButton("Reset source point")
        self.intersection_resetsrcpt_pButton.clicked[bool].connect(self.reset_src_point)      
        inputLayout.addWidget(self.intersection_resetsrcpt_pButton, 1, 0, 1, 3)        
                      
        inputLayout.addWidget(QLabel("X"), 2, 0, 1, 1)
        self.Pt_x_QLineEdit = QLineEdit()
        self.Pt_x_QLineEdit.textEdited.connect(self.update_intersection_point_pos)
        inputLayout.addWidget(self.Pt_x_QLineEdit, 2, 1, 1, 2)  
              
        inputLayout.addWidget(QLabel("Y"), 3, 0, 1, 1)
        self.Pt_y_QLineEdit = QLineEdit()
        self.Pt_y_QLineEdit.textEdited.connect(self.update_intersection_point_pos)
        inputLayout.addWidget(self.Pt_y_QLineEdit, 3, 1, 1, 2) 
                      
        inputLayout.addWidget(QLabel("Z"), 4, 0, 1, 1)
        self.Pt_z_QLineEdit = QLineEdit()
        self.Pt_z_QLineEdit.textEdited.connect(self.check_z_congruence_with_dem)
        inputLayout.addWidget(self.Pt_z_QLineEdit, 4, 1, 1, 2) 
               
        self.fixz2dem_checkBox = QCheckBox("lock z value to DEM surface")
        self.fixz2dem_checkBox.setChecked(True)
        self.fixz2dem_checkBox.stateChanged[int].connect(self.update_z_value)
        inputLayout.addWidget(self.fixz2dem_checkBox, 5, 0, 1, 3)        
        
        self.reset_input()
        
        inputWidget.setLayout(inputLayout) 
        
        return inputWidget

    def refresh_raster_layer_list(self):

        try:
            self.define_dem_QComboBox.currentIndexChanged[int].disconnect(self.get_working_dem)
        except:
            pass

        try:
            self.define_dem_QComboBox.clear()
        except:
            return

        self.define_dem_QComboBox.addItem(self.dem_default_text)

        self.rasterLayers = loaded_raster_layers()
        if self.rasterLayers is None or len(self.rasterLayers) == 0:
            return
        for layer in self.rasterLayers:
            self.define_dem_QComboBox.addItem(layer.name())

        self.define_dem_QComboBox.currentIndexChanged[int].connect(self.get_working_dem)

    def update_crs_settings(self):

        self.projectCrs = self.canvas.mapSettings().destinationCrs()

    def reset_values(self):

        self.current_z_value = None
        self.intersection_z_from_dem = False
        self.reset_srcpt()
        self.reset_results()

    def reset_srcpt(self):        

        self.srcpt_x = None
        self.srcpt_y = None
        self.intersection_sourcepoint_marker = None
        
    def reset_results(self):

        self.intersections_x = []
        self.intersections_y = []
        self.intersections_xprt = {}        
        self.inters = None
       
    def check_z_congruence_with_dem(self):
        
        if self.intersection_z_from_dem and float(self.Pt_z_QLineEdit.text()) != self.current_z_value:
            self.intersection_z_from_dem = False
            self.fixz2dem_checkBox.setChecked(False)
            
        self.current_z_value = float(self.Pt_z_QLineEdit.text())

    def reset_src_point(self):
        
        self.intersection_resetsrcpt_pButton.setEnabled(False)
        self.reset_srcpoint_QLineEdit()                           
        self.reset_markers()
        self.reset_values()
                    
    def setup_geologicdata_sect(self):

        planeorientationWidget = QWidget()  
        planeorientationLayout = QGridLayout()
        
        dip_dir_label = QLabel("Dip direction")
        dip_dir_label.setAlignment (Qt.AlignCenter)       
        planeorientationLayout.addWidget(dip_dir_label, 0, 0, 1, 2)

        dip_ang_label = QLabel("Dip angle")
        dip_ang_label.setAlignment(Qt.AlignCenter)       
        planeorientationLayout.addWidget(dip_ang_label, 0, 2, 1, 1)
        
        self.DDirection_dial = QDial()
        self.DDirection_dial.setRange(0, 360)
        self.DDirection_dial.setPageStep(1)
        self.DDirection_dial.setProperty("value", 180)
        self.DDirection_dial.setSliderPosition(180)
        self.DDirection_dial.setTracking(True)
        self.DDirection_dial.setOrientation(Qt.Vertical)
        self.DDirection_dial.setWrapping(True)
        self.DDirection_dial.setNotchTarget(30.0)
        self.DDirection_dial.setNotchesVisible(True)   
        self.DDirection_dial.valueChanged[int].connect(self.update_dipdir_spinbox)    
        planeorientationLayout.addWidget(self.DDirection_dial, 1, 0, 1, 2)        
                
        self.DAngle_verticalSlider = QSlider()
        self.DAngle_verticalSlider.setRange(0,90)
        self.DAngle_verticalSlider.setProperty("value", 45)
        self.DAngle_verticalSlider.setOrientation(Qt.Vertical)
        self.DAngle_verticalSlider.setInvertedAppearance(True)
        self.DAngle_verticalSlider.setTickPosition(QSlider.TicksBelow)
        self.DAngle_verticalSlider.setTickInterval(15)
        self.DAngle_verticalSlider.valueChanged[int].connect(self.update_dipang_spinbox)
        planeorientationLayout.addWidget(self.DAngle_verticalSlider, 1, 2, 1, 1)

        self.DDirection_spinBox = QSpinBox()
        self.DDirection_spinBox.setRange(0,360)
        self.DDirection_spinBox.setSingleStep(1)
        self.DDirection_spinBox.valueChanged[int].connect(self.update_dipdir_slider)
        planeorientationLayout.addWidget(self.DDirection_spinBox, 2, 0, 1, 2)        
         
        self.DAngle_spinBox = QSpinBox()
        self.DAngle_spinBox.setRange(0,90)
        self.DAngle_spinBox.setSingleStep(1)
        self.DAngle_spinBox.setProperty("value", 45) 
        self.DAngle_spinBox.valueChanged[int].connect(self.update_dipang_slider)
        planeorientationLayout.addWidget(self.DAngle_spinBox, 2, 2, 1, 1)
 
        self.Intersection_calculate_pushButton = QPushButton("Calculate intersection")
        self.Intersection_calculate_pushButton.clicked[bool].connect(self.calculate_intersection)
        planeorientationLayout.addWidget(self.Intersection_calculate_pushButton, 3, 0, 1, 3)
        
        planeorientationLayout.addWidget(QLabel("Intersection color"), 4, 0, 1, 1)
        
        self.Intersection_color_comboBox = QComboBox()
        self.Intersection_color_comboBox.insertItems(0, ["blue", "white", "red", "yellow", "orange", "brown", "green", "pink", "darkblue", "gray"])

        self.Intersection_color_comboBox.currentIndexChanged[int].connect(self.plot_intersections)
                                                                  
        planeorientationLayout.addWidget(self.Intersection_color_comboBox, 4, 1, 1, 2)                                                             
         
        self.Intersection_cancel_pushButton = QPushButton("Cancel intersections")
        self.Intersection_cancel_pushButton.clicked.connect(self.reset_intersections)
        planeorientationLayout.addWidget(self.Intersection_cancel_pushButton, 5, 0, 1, 3)  
                                      
        planeorientationWidget.setLayout(planeorientationLayout)              

        return planeorientationWidget
        
    def setup_output_sect(self):

        outputWidget = QWidget()  
        outputLayout = QGridLayout()

        outputLayout.addWidget(QLabel(self.tr("Save results in")), 0, 0, 1, 1)
        
        self.Output_FileName_Input = QLineEdit()
        outputLayout.addWidget(self.Output_FileName_Input, 0, 1, 1, 2)

        self.Output_Browse = QPushButton(".....")
        self.Output_Browse.clicked.connect(self.selectOutputVectorFile)
        outputLayout.addWidget(self.Output_Browse, 0, 3, 1, 1) 

        outputLayout.addWidget(QLabel(self.tr("with geometry:")), 1, 0, 1, 1)
                               
        saveGroup = QButtonGroup(outputWidget)
        
        self.Save_points_rButt = QRadioButton("points")
        self.Save_points_rButt.setChecked(True)
        saveGroup.addButton(self.Save_points_rButt, 0)
        outputLayout.addWidget(self.Save_points_rButt, 1, 1, 1, 1)
        
        self.Save_lines_rButt = QRadioButton("lines")
        saveGroup.addButton(self.Save_lines_rButt, 1)
        outputLayout.addWidget(self.Save_lines_rButt, 1, 2, 1, 1)        
                
        self.Load_output_checkBox = QCheckBox("load output in project")
        outputLayout.addWidget(self.Load_output_checkBox, 2, 0, 1, 2)  
                       
        self.Save_pushButton = QPushButton("Save last intersections")
        self.Save_pushButton.clicked.connect(self.write_results)
        outputLayout.addWidget(self.Save_pushButton, 3, 0, 1, 4)
                
        outputWidget.setLayout(outputLayout)              

        return outputWidget

    def set_intersection_point(self):
        
        try:
            self.intersection_PointMapTool.canvasClicked.disconnect(self.update_intersection_point_pos)
        except:
            pass            
         
        self.update_crs_settings()
                       
        self.intersection_PointMapTool = PointMapToolEmitPoint(self.canvas, self.plugin)  # mouse listener
        self.previousTool = self.canvas.mapTool()  # save the standard map tool for restoring it at the end
        self.intersection_PointMapTool.canvasClicked.connect(self.update_intersection_point_pos)
        self.intersection_PointMapTool.setCursor(Qt.CrossCursor)                
        self.canvas.setMapTool(self.intersection_PointMapTool)

    def reset_all(self):

        self.reset_markers() 
        self.reset_input()
        self.reset_values()

    def reset_input(self):

        self.disable_tools()
        self.reset_srcpoint_QLineEdit()

    def disable_tools(self):
        
        self.intersection_definepoint_pButton.setEnabled(False)
        self.intersection_resetsrcpt_pButton.setEnabled(False)
        
        try: 
            self.intersection_PointMapTool.canvasClicked.disconnect(self.update_intersection_point_pos)
        except: 
            pass
        
        try: 
            self.disable_MapTool(self.intersection_PointMapTool)
        except: 
            pass

    def reset_markers(self):       
        
        self.reset_intersections()
        self.remove_srcpt_marker_from_canvas()

    def reset_intersections(self):
        
        self.remove_markers_from_canvas()
        self.intersection_markers_list = []
        self.reset_results()        

    def remove_markers_from_canvas(self):

        for mrk in self.intersection_markers_list:
            self.canvas.scene().removeItem(mrk) 

    def remove_srcpt_marker_from_canvas(self):
        
        if self.intersection_sourcepoint_marker is not None:
            self.canvas.scene().removeItem(self.intersection_sourcepoint_marker)

    def refresh_raster_layer_list(self):

        try:
            self.define_dem_QComboBox.currentIndexChanged[int].disconnect(self.get_working_dem)
        except:
            pass

        try:
            self.reset_all()
            self.reset_dem_input_states()
        except:
            pass

        try:
            self.define_dem_QComboBox.clear()
        except:
            return

        self.define_dem_QComboBox.addItem(self.dem_default_text)

        self.rasterLayers = loaded_raster_layers()
        if self.rasterLayers is None or len(self.rasterLayers) == 0:
            return
        for layer in self.rasterLayers:
            self.define_dem_QComboBox.addItem(layer.name())

        self.define_dem_QComboBox.currentIndexChanged[int].connect(self.get_working_dem)

    def reset_dem_input_states(self):

        self.dem, self.geoarray = None, None

    def get_working_dem(self, ndx_DEM_file = 0):

        self.dem = None        
        self.reset_all()       
        if self.rasterLayers is None or len(self.rasterLayers) == 0: 
            return          
                                
        # no DEM layer defined  
        if ndx_DEM_file == 0: 
            return             

        self.dem = self.rasterLayers[ndx_DEM_file-1]

        dem_src = self.dem.source()
        success, cntnt = try_read_raster_band(raster_source=dem_src)
        if not success:
            QMessageBox.critical(self, "DEM", "{} was not read".format(dem_src))
            return

        geotransform, projection, band_params, data = cntnt
        self.geoarray = GeoArray(inGeotransform=geotransform, inProjection=projection, inLevels=[data])

        self.intersection_definepoint_pButton.setEnabled(True)
        self.intersection_resetsrcpt_pButton.setEnabled(True)

    def coords_within_dem_bndr(self, dem_crs_coord_x, dem_crs_coord_y):
        
        if dem_crs_coord_x <= self.geoarray.xmin or dem_crs_coord_x >= self.geoarray.xmax or \
           dem_crs_coord_y <= self.geoarray.ymin or dem_crs_coord_y >= self.geoarray.ymax:
            return False        
        return True        

    def create_marker(self, canvas, prj_crs_x, prj_crs_y, pen_width= 2, icon_type = 2, icon_size = 18, icon_color = 'limegreen'):
        
        marker = QgsVertexMarker(canvas)
        marker.setIconType(icon_type)
        marker.setIconSize(icon_size)
        marker.setPenWidth(pen_width)
        marker.setColor(QColor(icon_color))
        marker.setCenter(QgsPointXY(prj_crs_x, prj_crs_y))
        return marker        

    def update_intersection_point_pos(self, qgs_point = None, button = None): # Add point to analyze

        if self.geoarray is None:
            QMessageBox.critical(self, "Intersection source point", "Source DEM is not defined") 
            return

        self.intersection_resetsrcpt_pButton.setEnabled(True)
               
        if self.sender() == self.intersection_PointMapTool:
            
            self.srcpt_x = qgs_point.x()
            self.srcpt_y = qgs_point.y()
            self.Pt_x_QLineEdit.setText(str(self.srcpt_x))
            self.Pt_y_QLineEdit.setText(str(self.srcpt_y))
            
        elif self.sender() == self.Pt_x_QLineEdit:
            
            if self.Pt_x_QLineEdit.text() == '':
                QMessageBox.critical(self, "qgSurf", "Error: x value is not defined") 
                return
            try:
                self.srcpt_x = float(self.Pt_x_QLineEdit.text())
            except:
                QMessageBox.critical(self, "qgSurf", "Error: x value is not correctly defined")
                return 
                                   
        elif self.sender() == self.Pt_y_QLineEdit:
            
            if self.Pt_y_QLineEdit.text() == '':
                QMessageBox.critical(self, "qgSurf", "Error: y value is not defined") 
                return  
            try:
                self.srcpt_y = float(self.Pt_y_QLineEdit.text())
            except:
                QMessageBox.critical(self, "qgSurf", "Error: y value is not correctly defined")
                return            
        
        z_value_from_dem = self.update_z_value()
        if z_value_from_dem is None: 
            self.current_z_value = None
            self.Pt_z_QLineEdit.setText("")
        else:
            self.current_z_value = z_value_from_dem 
            self.Pt_z_QLineEdit.setText(str(self.current_z_value))
            self.intersection_z_from_dem = True
                           
        self.remove_markers_from_canvas(); self.remove_srcpt_marker_from_canvas()        
        self.intersection_sourcepoint_marker = self.create_marker(self.canvas,
                                                                  self.srcpt_x, self.srcpt_y,
                                                                  icon_type = 1,
                                                                  icon_color = QColor(str(self.Intersection_color_comboBox.currentText())))
        self.canvas.refresh()

    def update_z_value (self):
        """
        Update z value.
        
        """         
        
        # to prevent action when the DEM is not set              
        if self.geoarray is None:
            return None 
               
        if not self.fixz2dem_checkBox.isChecked(): 
            return None

        dem_crs_source_pt_x, dem_crs_source_pt_y = self.project_from_prj_to_dem_crs(self.srcpt_x, self.srcpt_y)

        """
        if not self.coords_within_dem_bndr(dem_crs_source_pt_x, dem_crs_source_pt_y): 
            QMessageBox.critical(self, "Intersection source point", 
                                 "Defined point is outside source DEM extent")                 
            return None
        """

        z = self.geoarray.interpolate_bilinear(dem_crs_source_pt_x, dem_crs_source_pt_y)
        if z is None: 
            return None
        
        return z

    def disable_MapTool(self, mapTool):
                            
        try:
            if mapTool is not None: self.canvas.unsetMapTool(mapTool)
        except:
            pass                            

        try:
            if self.previousTool is not None: self.canvas.setMapTool(self.previousTool)
        except:
            pass

    def reset_srcpoint_QLineEdit(self):
        
        for qlineedit in (self.Pt_x_QLineEdit, self.Pt_y_QLineEdit, self.Pt_z_QLineEdit):
            qlineedit.clear()

    def update_dipdir_slider(self):
        """
        Update the value of the dip direction in the slider.""
        """        
        transformed_dipdirection = self.DDirection_spinBox.value() + 180.0
        if transformed_dipdirection > 360.0: transformed_dipdirection -= 360.0            
        self.DDirection_dial.setValue(transformed_dipdirection) 

    def update_dipdir_spinbox(self):            
        """
        Update the value of the dip direction in the spinbox.
        """        
        real_dipdirection = self.DDirection_dial.value() - 180.0
        if real_dipdirection < 0.0: real_dipdirection += 360.0            
        self.DDirection_spinBox.setValue(real_dipdirection) 

    def update_dipang_slider(self):
        """
        Update the value of the dip angle in the slider.
        """
        
        self.DAngle_verticalSlider.setValue(self.DAngle_spinBox.value())    

    def update_dipang_spinbox(self):            
        """
        Update the value of the dip angle in the spinbox.
        """        
        
        self.DAngle_spinBox.setValue(self.DAngle_verticalSlider.value()) 

    def project_from_prj_to_dem_crs(self, x: float, y: float) -> Tuple[float, float]:
        """
        Converts point coordinates from project to DEM crs.

        :param x: x coordinate in the project CRS.
        :type x: float.
        :param y: y coordinate in the project CRS.
        :type y: float.
        :return: the point coordinates in the DEM crs.
        :rtype: tuple of two float values.
        """

        return qgs_project_xy(x, y, self.projectCrs, self.dem.crs())

    def project_from_dem_to_prj_crs(self, x: float, y: float) -> Tuple[float, float]:
        """
        Converts point coordinates from project to DEM crs.

        :param x: x coordinate in the DEM CRS.
        :type x: float.
        :param y: y coordinate in the DEM CRS.
        :type y: float.
        :return: the point coordinates in the project crs.
        :rtype: tuple of two float values.
        """

        return qgs_project_xy(x, y, self.dem.crs(), self.projectCrs)

    def calculate_intersection(self):
        """
        Calculate intersection points.
        """

        # check if all input data are correct
        if self.geoarray is None:
            QMessageBox.information(self, "qgSurf", "Please first define a source DEM")
            return
                
        if self.Pt_x_QLineEdit.text() == '' or self.Pt_y_QLineEdit.text() == '' or self.Pt_z_QLineEdit.text() == '':
            QMessageBox.information(self, "qgSurf", "Define the location of the source point in 'Geographic parameters' section")
            return
        
        try:
            z = float(self.Pt_z_QLineEdit.text())
        except:
            QMessageBox.information(self, "qgSurf", "z value is not correctly defined")
            return

        # source point

        srcpt_prjcrs_x, srcpt_prjcrs_y = self.srcpt_x, self.srcpt_y

        # Calculates dip direction correction with respect to project CRS y-axis orientation

        srcpt_epsg4326_lon, srcpt_epsg4326_lat = qgs_project_xy(
            x=srcpt_prjcrs_x,
            y=srcpt_prjcrs_y,
            srcCrs=self.projectCrs)

        north_dummpy_pt_lon = srcpt_epsg4326_lon  # no change
        north_dummpy_pt_lat = srcpt_epsg4326_lat + (1.0/1200.0)  # add 3 minute-seconds (approximately 90 meters)

        dummypt_prjcrs_x, dummypt_prjcrs_y = qgs_project_xy(
            x=north_dummpy_pt_lon,
            y=north_dummpy_pt_lat,
            destCrs=self.projectCrs)

        start_pt = Point(
            srcpt_prjcrs_x,
            srcpt_prjcrs_y)

        end_pt = Point(
            dummypt_prjcrs_x,
            dummypt_prjcrs_y)

        north_vector = Segment(
            start_pt=start_pt,
            end_pt=end_pt).vector()

        azimuth_correction = north_vector.azimuth

        print("Azimuth correction: {}".format(azimuth_correction))

        src_dip_direction, src_dip_angle = self.DDirection_spinBox.value(), self.DAngle_verticalSlider.value()

        prjcrs_dipdir = (src_dip_direction + azimuth_correction) % 360.0
        prjcrs_dipang = src_dip_angle

        print("Project CRS corrected plane orientation: dip dir. = {}, dip ang. = {}".format(prjcrs_dipdir, prjcrs_dipang))

        # Correct dip direction and angle by DEM crs

        """
        srcpt_prjcrs_x, srcpt_prjcrs_y = self.srcpt_x, self.srcpt_y
        prjcrs_dipdir, prjcrs_dipang
        """

        prjcrs_dir_versor = Direct.fromAzPl(
            az=prjcrs_dipdir,
            pl=0.0).asVersor()

        dummy_distance = 100  # meters

        prjcrs_dir_vector = prjcrs_dir_versor.scale(dummy_distance)

        # NOTE: it assumes that the project crs is not in lon-lat !!

        prjcrs_srcpt = Point(
            srcpt_prjcrs_x,
            srcpt_prjcrs_y)

        endpt_prjcrs_x, endpt_prjcrs_y, _ = prjcrs_srcpt.shiftByVect(prjcrs_dir_vector).toXYZ()

        prjcrs_zeta = dummy_distance * tan(radians(prjcrs_dipang))

        srcpt_demcrs_x, srcpt_demcrs_y = self.project_from_prj_to_dem_crs(
            x=srcpt_prjcrs_x,
            y=srcpt_prjcrs_y)

        dem_crs_source_point = Point(srcpt_demcrs_x, srcpt_demcrs_y)

        endpt_demcrs_x, endpt_demcrs_y = self.project_from_prj_to_dem_crs(
            x=endpt_prjcrs_x,
            y=endpt_prjcrs_y)

        # geoplane attitude in DEM CRS

        demcrs_vector = Segment(
            start_pt=dem_crs_source_point,
            end_pt=Point(endpt_demcrs_x, endpt_demcrs_y)
          ).vector()

        corr_dip_direction = demcrs_vector.azimuth

        demcrs_len = demcrs_vector.len2D
        demcrs_zeta = prjcrs_zeta

        corr_dip_angle = degrees(atan(demcrs_zeta / demcrs_len))

        print("corrected dummy lenght: {}, corr. dip dir.: {}, corr. dip ang.: {}".format(
            demcrs_len,
            corr_dip_direction,
            corr_dip_angle
        ))

        #corr_dip_direction, corr_dip_angle = self.corrected_plane_attitude(src_dip_direction, src_dip_angle)

        self.srcPlaneAttitude = Plane(corr_dip_direction, corr_dip_angle)

        # intersection points

        dem_crs_pt = Point(
            x=srcpt_demcrs_x,
            y=srcpt_demcrs_y,
            z=z)

        self.intersection_pts = plane_dem_intersection(
            srcPlaneAttitude=self.srcPlaneAttitude,
            srcPt=dem_crs_pt,
            geo_array=self.geoarray)

        self.plot_intersections()

    def plot_intersections(self):

        intersections_x = list(map(lambda pt: pt.x, self.intersection_pts))
        intersections_y = list(map(lambda pt: pt.y, self.intersection_pts))

        current_markers_list = []
        for dem_crs_x, dem_crs_y in zip(intersections_x, intersections_y):

            prj_crs_x, prj_crs_y = self.project_from_dem_to_prj_crs(dem_crs_x, dem_crs_y)

            marker = self.create_marker(self.canvas, prj_crs_x, prj_crs_y, pen_width= 1, icon_type = 1, icon_size = 8, 
                                         icon_color = QColor(str(self.Intersection_color_comboBox.currentText())))
            current_markers_list.append(marker)        
        self.intersection_markers_list += current_markers_list   
        self.canvas.refresh()

    def selectOutputVectorFile(self):
            
        output_filename, __ = QFileDialog.getSaveFileName(self,
                                                      self.tr("Save shapefile"), 
                                                      "*.shp", 
                                                      "shp (*.shp *.SHP)")        
        if not output_filename: 
            return        
        self.Output_FileName_Input.setText(output_filename) 

    def write_results(self):
        """
        Write intersection results in the output shapefile.
        """
 
        # check for result existence
        
        if self.inters is None:
            QMessageBox.critical(self, "Save results", "No results available") 
            return            
            
        self.output_filename = str(self.Output_FileName_Input.text()) 
        if self.output_filename == '':
            QMessageBox.critical(self, "Save results", "No output file defined") 
            return
                           
        # set output type
        if self.Save_points_rButt.isChecked(): self.result_geometry = 'points'
        else: self.result_geometry = 'lines'        
        
        # creation of output shapefile
        shape_driver = ogr.GetDriverByName("ESRI Shapefile")              
        self.out_shape = shape_driver.CreateDataSource(self.output_filename)
        if self.out_shape is None:
            QMessageBox.critical(self, "Results", "Unable to create output shapefile: %s" % self.output_filename)
            return
        
        if self.result_geometry == 'points':
            self.out_layer = self.out_shape.CreateLayer('output_lines', geom_type=ogr.wkbPoint)            
        else:
            self.out_layer = self.out_shape.CreateLayer('output_lines', geom_type=ogr.wkbLineString) 
        
        if self.out_layer is None:
            QMessageBox.critical(self, "Results", "Unable to create output shapefile: %s" % self.output_filename) 
            return
        
        # set analysis parameters
        sourcePoint = self.inters.parameters._srcPt
        self.srcPlaneAttitude = self.inters.parameters._srcPlaneAttitude
        self.plane_z = self.srcPlaneAttitude.closure_plane_from_geo(sourcePoint)
              
        # add fields to the output shapefile  
        id_fieldDef = ogr.FieldDefn('id', ogr.OFTInteger)
        self.out_layer.CreateField(id_fieldDef) 

        if self.result_geometry == 'points':
            x_fieldDef = ogr.FieldDefn('x', ogr.OFTReal)
            self.out_layer.CreateField(x_fieldDef)    
            y_fieldDef = ogr.FieldDefn('y', ogr.OFTReal)
            self.out_layer.CreateField(y_fieldDef)    
            z_fieldDef = ogr.FieldDefn('z', ogr.OFTReal)
            self.out_layer.CreateField(z_fieldDef)  
        
        srcPt_x_fieldDef = ogr.FieldDefn('srcPt_x', ogr.OFTReal)
        self.out_layer.CreateField(srcPt_x_fieldDef)
        srcPt_y_fieldDef = ogr.FieldDefn('srcPt_y', ogr.OFTReal)
        self.out_layer.CreateField(srcPt_y_fieldDef)
        srcPt_z_fieldDef = ogr.FieldDefn('srcPt_z', ogr.OFTReal)
        self.out_layer.CreateField(srcPt_z_fieldDef)
        DipDir_fieldDef = ogr.FieldDefn('dip_dir', ogr.OFTReal)
        self.out_layer.CreateField(DipDir_fieldDef)
        DipAng_fieldDef = ogr.FieldDefn('dip_ang', ogr.OFTReal)
        self.out_layer.CreateField(DipAng_fieldDef)        
                        
        # get the layer definition of the output shapefile
        self.outshape_featdef = self.out_layer.GetLayerDefn() 

        # write results
        if self.result_geometry == 'points':
            self.write_intersections_as_points()
        else:
            self.write_intersections_as_lines()
        QMessageBox.information(self, "Result", "Saved to shapefile: %s" % self.output_filename)

        # add theme to QGis project
        if self.Load_output_checkBox.isChecked():
            try:
                intersection_layer = QgsVectorLayer(self.output_filename, QFileInfo(self.output_filename).baseName(), "ogr")                    
                QgsProject.instance().addMapLayer(intersection_layer)
            except:            
                QMessageBox.critical(self, "Result", "Unable to load layer in project")
                return

    def write_intersections_as_points(self):
        """
        Write intersection results in the output shapefile.
        """
                                
        x_filtered_coord_x = self.inters.xcoords_x[ np.logical_not(np.isnan(self.inters.xcoords_x)) ] 
        x_filtered_coord_y = self.inters.xcoords_y[ np.logical_not(np.isnan(self.inters.xcoords_x)) ]            
        x_filtered_coord_z = self.plane_z(x_filtered_coord_x, x_filtered_coord_y)

        y_filtered_coord_x = self.inters.ycoords_x[ np.logical_not(np.isnan(self.inters.ycoords_y)) ] 
        y_filtered_coord_y = self.inters.ycoords_y[ np.logical_not(np.isnan(self.inters.ycoords_y)) ]             
        y_filtered_coord_z = self.plane_z(y_filtered_coord_x, y_filtered_coord_y)        
        
        intersections_x = list(x_filtered_coord_x) + list(y_filtered_coord_x)    
        intersections_y = list(x_filtered_coord_y) + list(y_filtered_coord_y)                                           
        intersections_z = list(x_filtered_coord_z) + list(y_filtered_coord_z)       
         
        curr_Pt_id = 0   
        for curr_Pt in zip(intersections_x, intersections_y, intersections_z):            
            curr_Pt_id += 1

            prj_crs_x, prj_crs_y = self.project_from_dem_to_prj_crs(float(curr_Pt[0]), float(curr_Pt[1]))

            # pre-processing for new feature in output layer
            curr_Pt_geom = ogr.Geometry(ogr.wkbPoint)
            curr_Pt_geom.AddPoint(prj_crs_x, prj_crs_y, float(curr_Pt[2]))
                
            # create a new feature
            curr_Pt_shape = ogr.Feature(self.outshape_featdef)
            curr_Pt_shape.SetGeometry(curr_Pt_geom)
            curr_Pt_shape.SetField('id', curr_Pt_id)
                                    
            curr_Pt_shape.SetField('x', prj_crs_x)
            curr_Pt_shape.SetField('y', prj_crs_y) 
            curr_Pt_shape.SetField('z', curr_Pt[2]) 

            prj_crs_src_pt_x, prj_crs_src_pt_y = self.project_from_dem_to_prj_crs(self.intersections_xprt['point']['x'], self.intersections_xprt['point']['y'])

            curr_Pt_shape.SetField('srcPt_x', prj_crs_src_pt_x)
            curr_Pt_shape.SetField('srcPt_y', prj_crs_src_pt_y) 
            curr_Pt_shape.SetField('srcPt_z', self.intersections_xprt['point']['z'])

            curr_Pt_shape.SetField('dip_dir', self.srcPlaneAttitude._dipdir)
            curr_Pt_shape.SetField('dip_ang', self.srcPlaneAttitude._dipangle)             

            # add the feature to the output layer
            self.out_layer.CreateFeature(curr_Pt_shape)            
            
            # destroy no longer used objects
            curr_Pt_geom.Destroy()
            curr_Pt_shape.Destroy()
                            
        # destroy output geometry
        self.out_shape.Destroy() 

    def write_intersections_as_lines(self):
        """
        Write intersection results in a line shapefile.
        """
                
        # create dictionary of cell with intersection points        
        self.inters.links = self.inters.get_intersections()
        self.inters.neighbours = self.inters.set_neighbours() 
        self.inters.define_paths()  
        
        # networks of connected intersections
        self.inters.networks = self.inters.define_networks()   
        
        for curr_path_id, curr_path_points in self.inters.networks.items():
            line = ogr.Geometry(ogr.wkbLineString)            
            for curr_point_id in curr_path_points:                            
                curr_intersection = self.inters.links[ curr_point_id-1 ]                           
                i, j, direct = curr_intersection['i'], curr_intersection['j'], curr_intersection['pi_dir']                
                if direct == 'x': dem_crs_x, dem_crs_y = self.inters.xcoords_x[ i, j ], self.inters.xcoords_y[ i, j ]
                if direct == 'y': dem_crs_x, dem_crs_y = self.inters.ycoords_x[ i, j ], self.inters.ycoords_y[ i, j ]                                        
                z = self.plane_z(dem_crs_x, dem_crs_y)

                prj_crs_x, prj_crs_y = self.project_from_dem_to_prj_crs(dem_crs_x, dem_crs_y)

                line.AddPoint(prj_crs_x, prj_crs_y, z)            
                                       
            # create a new feature
            line_shape = ogr.Feature(self.outshape_featdef)
            line_shape.SetGeometry(line)   

            line_shape.SetField('id', curr_path_id)
            
            prj_crs_src_pt_x, prj_crs_src_pt_y = self.project_from_dem_to_prj_crs(self.intersections_xprt['point']['x'], self.intersections_xprt['point']['y'])

            line_shape.SetField('srcPt_x', prj_crs_src_pt_x)
            line_shape.SetField('srcPt_y', prj_crs_src_pt_y) 
            line_shape.SetField('srcPt_z', self.intersections_xprt['point']['z'])
    
            line_shape.SetField('dip_dir', self.srcPlaneAttitude._dipdir)
            line_shape.SetField('dip_ang', self.srcPlaneAttitude._dipangle)             
    
            # add the feature to the output layer
            self.out_layer.CreateFeature(line_shape)            
            
            # destroy no longer used objects
            line.Destroy()
            line_shape.Destroy()
                            
        # destroy output geometry
        self.out_shape.Destroy() 
        
    
        
          
            
            



