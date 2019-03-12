"""
/***************************************************************************
 qgSurf - plugin for Quantum GIS

 Processing of geological planes and surfaces

                              -------------------
        begin                : 2011-12-21
        copyright            : (C) 2011-2019 by Mauro Alberti
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
from builtins import str

from typing import Tuple

import os
from math import tan, atan, degrees, radians

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *

from qgis.core import *
from qgis.gui import *
    
from osgeo import ogr

from .pygsf.topography.plane_intersect import plane_dem_intersection
from .pygsf.orientations.orientations import Plane, Direct
from .pygsf.libs_utils.gdal.gdal import try_read_raster_band
from .pygsf.spatial.rasters.geoarray import GeoArray
from .pygsf.libs_utils.qgis.qgs_tools import loaded_raster_layers, qgs_project_xy
from .pygsf.libs_utils.qgis.qgs_tools import PointMapToolEmitPoint
from .pygsf.spatial.vectorial.vectorial import Point, Segment
from .pygsf.geography.projections import calculate_azimuth_correction


class DemPlaneIntersectionWidget(QWidget):
    """
    Constructor
    
    """

    line_colors = ["white", "red", "blue", "yellow", "orange", "brown"]
    dem_default_text = '--  required  --'

    def __init__(self, tool_nm, canvas, plugin_qaction):

        super(DemPlaneIntersectionWidget, self).__init__()

        self.tool_nm = tool_nm
        self.canvas, self.plugin = canvas, plugin_qaction

        self.setup_gui()
        self.init_params()

    def init_params(self):

        self.previousTool = None
        self.intersection_z_from_dem = False
        self.intersection_PointMapTool = None

        self.init_post_dem_change()

    def init_post_dem_change(self):

        self.disable_canvas_tools()
        self.reset_full_io_values()

    def srcpt_resetting_action(self):

        self.intersection_resetsrcpt_pButton.setEnabled(False)
        self.reset_srcpt_intersections()

    def reset_full_io_values(self):

        self.reset_full_input_values()
        self.reset_intersections()

    def reset_full_input_values(self):

        self.nullify_input_dem_vars()
        self.reset_srcpt()
        self.nullify_input_geoplane_vars()

    def nullify_input_dem_vars(self):

        self.dem = None
        self.geoarray = None
        self.current_z_value = None

    def disable_canvas_tools(self):

        self.intersection_definepoint_pButton.setEnabled(False)
        self.intersection_resetsrcpt_pButton.setEnabled(False)

        try:
            self.intersection_PointMapTool.canvasClicked.disconnect(self.update_intersection_point_pos)
        except:
            pass

        try:
            self.restore_previous_maptool(self.intersection_PointMapTool)
        except:
            pass

    def reset_srcpt_intersections(self):

        self.reset_intersections()
        self.reset_srcpt()

    def reset_intersections(self):

        if hasattr(self, 'intersections_markers_list'):
            self.remove_from_canvas_markers_intersections()
        self.nullify_intersections_vals()

    def nullify_intersections_markers_val(self):

        self.intersections_markers_list = []

    def nullify_intersections_xyzs_val(self):

        self.intersections_prjcrs_xyz = []

    def nullify_intersections_vals(self):

        self.nullify_intersections_markers_val()
        self.nullify_intersections_xyzs_val()

    def reset_srcpt(self):

        self.clear_srcpoint_qlineedits()
        if hasattr(self, 'source_point_marker_list'):
            self.remove_from_canvas_marker_srcpt()
        self.nullify_srcpt_vars()
        self.nullify_scrpt_markers_var()

    def nullify_srcpt_vars(self):

        self.srcpt_x = None
        self.srcpt_y = None
        self.srcpt_z = None

    def nullify_scrpt_markers_var(self):

        self.source_point_marker_list = []

    def remove_from_canvas_markers_intersections(self):

        for mrk in self.intersections_markers_list:
            self.canvas.scene().removeItem(mrk)

    def remove_from_canvas_marker_srcpt(self):

        for mrk in self.source_point_marker_list:
            self.canvas.scene().removeItem(mrk)

    def nullify_input_geoplane_vars(self):

        self.src_dipdir = None
        self.src_dipang = None

    def refresh_raster_layer_list(self):

        try:
            self.define_dem_QComboBox.currentIndexChanged[int].disconnect(self.get_working_dem)
        except:
            pass

        try:
            self.init_post_dem_change()
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
        self.intersection_resetsrcpt_pButton.clicked[bool].connect(self.srcpt_resetting_action)
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
        
        #self.reset_input()
        
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

    def check_z_congruence_with_dem(self):
        
        if self.intersection_z_from_dem and float(self.Pt_z_QLineEdit.text()) != self.current_z_value:
            self.intersection_z_from_dem = False
            self.fixz2dem_checkBox.setChecked(False)
            
        self.current_z_value = float(self.Pt_z_QLineEdit.text())

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
        self.DDirection_spinBox.setRange(0, 360)
        self.DDirection_spinBox.setSingleStep(1)
        self.DDirection_spinBox.valueChanged[float].connect(self.update_dipdir_slider)
        planeorientationLayout.addWidget(self.DDirection_spinBox, 2, 0, 1, 2)        
         
        self.DAngle_spinBox = QDoubleSpinBox()
        self.DAngle_spinBox.setRange(0.0, 90.0)
        self.DAngle_spinBox.setDecimals(1)
        self.DAngle_spinBox.setSingleStep(0.1)
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

        """
        self.Save_lines_rButt = QRadioButton("lines")
        saveGroup.addButton(self.Save_lines_rButt, 1)
        outputLayout.addWidget(self.Save_lines_rButt, 1, 2, 1, 1)   
        """
                
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

    def get_working_dem(self, ndx_DEM_file = 0):

        self.dem = None        
        self.init_post_dem_change()
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

    """
    def coords_within_dem_bndr(self, dem_crs_coord_x, dem_crs_coord_y):
        
        if dem_crs_coord_x <= self.geoarray.xmin or dem_crs_coord_x >= self.geoarray.xmax or \
           dem_crs_coord_y <= self.geoarray.ymin or dem_crs_coord_y >= self.geoarray.ymax:
            return False        
        return True   
    """

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
                QMessageBox.critical(
                    self,
                    "qgSurf",
                    "Error: y value is not defined")
                return  
            try:
                self.srcpt_y = float(self.Pt_y_QLineEdit.text())
            except:
                QMessageBox.critical(
                    self,
                    "qgSurf",
                    "Error: y value is not correctly defined")
                return            
        
        z_value_from_dem = self.update_z_value()
        if z_value_from_dem is None: 
            self.current_z_value = None
            self.Pt_z_QLineEdit.setText("")
        else:
            self.current_z_value = z_value_from_dem 
            self.Pt_z_QLineEdit.setText(str(self.current_z_value))
            self.intersection_z_from_dem = True
                           
        self.remove_from_canvas_markers_intersections()
        self.remove_from_canvas_marker_srcpt()
        color = QColor(str(self.Intersection_color_comboBox.currentText()))
        source_point_marker = self.create_marker(
            self.canvas,
            self.srcpt_x, self.srcpt_y,
            icon_type=1,
            icon_color=color)
        self.source_point_marker_list = [source_point_marker]

        self.canvas.refresh()

    def update_z_value (self):
        """
        Update z value.
        
        """

        # does nothing when the height source is not from DEM

        if not self.fixz2dem_checkBox.isChecked():
            return None

        # prevent action when the DEM is not read

        if self.geoarray is None:
            return None 

        # get z value from ptLyr

        srcpt_demcrs_x, srcpt_demcrs_y = self.project_from_prj_to_dem_crs(self.srcpt_x, self.srcpt_y)

        # return None or a numeric value
        return self.geoarray.interpolate_bilinear(
            srcpt_demcrs_x,
            srcpt_demcrs_y)

    def restore_previous_maptool(self, mapTool):

        if mapTool:
            self.canvas.unsetMapTool(mapTool)

        if self.previousTool:
            self.canvas.setMapTool(self.previousTool)

    def clear_srcpoint_qlineedits(self):
        
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
            self.srcpt_z = float(self.Pt_z_QLineEdit.text())
        except:
            QMessageBox.information(self, "qgSurf", "z value is not correctly defined")
            return

        # source point

        srcpt_prjcrs_x, srcpt_prjcrs_y = self.srcpt_x, self.srcpt_y

        # Calculates dip direction correction with respect to project CRS y-axis orientation

        azimuth_correction = calculate_azimuth_correction(
            src_pt=Point(srcpt_prjcrs_x, srcpt_prjcrs_y),
            crs=self.projectCrs)

        print("Azimuth correction: {}".format(azimuth_correction))

        self.src_dipdir = self.DDirection_spinBox.value()
        self.src_dipang = self.DAngle_spinBox.value()

        prjcrs_dipdir = (self.src_dipdir + azimuth_correction) % 360.0
        prjcrs_dipang = self.src_dipang

        print("Project CRS corrected plane orientation: dip dir. = {}, dip ang. = {}".format(prjcrs_dipdir, prjcrs_dipang))

        # Correct dip direction and angle by DEM crs

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

        self.srcPlaneAttitude_demcrs = Plane(corr_dip_direction, corr_dip_angle)

        # intersection points

        srcpt_3d_demcrs = Point(
            x=srcpt_demcrs_x,
            y=srcpt_demcrs_y,
            z=self.srcpt_z)

        intersection_pts_demcrs = plane_dem_intersection(
            srcPlaneAttitude=self.srcPlaneAttitude_demcrs,
            srcPt=srcpt_3d_demcrs,
            geo_array=self.geoarray)

        self.intersections_prjcrs_xyz = []
        for pt3d in intersection_pts_demcrs:
            x, y, z = pt3d.toXYZ()
            prj_crs_x, prj_crs_y = self.project_from_dem_to_prj_crs(x, y)
            self.intersections_prjcrs_xyz.append((prj_crs_x, prj_crs_y, z))
        self.plot_intersections()

    def plot_intersections(self):

        current_markers_list = []
        for prj_crs_x, prj_crs_y, _ in self.intersections_prjcrs_xyz:
            marker = self.create_marker(
                self.canvas,
                prj_crs_x,
                prj_crs_y,
                pen_width=1,
                icon_type=1,
                icon_size=8,
                icon_color=QColor(str(self.Intersection_color_comboBox.currentText())))

            current_markers_list.append(marker)        
        self.intersections_markers_list += current_markers_list
        self.canvas.refresh()

    def selectOutputVectorFile(self):
            
        output_filename, __ = QFileDialog.getSaveFileName(
            self,
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
        
        if not self.intersections_prjcrs_xyz:
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

        curr_Pt_id = 0

        for x, y, z in self.intersections_prjcrs_xyz:

            curr_Pt_id += 1

            # pre-processing for new feature in output layer
            curr_Pt_geom = ogr.Geometry(ogr.wkbPoint25D)
            curr_Pt_geom.AddPoint(x, y, z)
                
            # create a new feature
            curr_Pt_shape = ogr.Feature(self.outshape_featdef)
            curr_Pt_shape.SetGeometry(curr_Pt_geom)
            curr_Pt_shape.SetField('id', curr_Pt_id)
                                    
            curr_Pt_shape.SetField('x', x)
            curr_Pt_shape.SetField('y', y)
            curr_Pt_shape.SetField('z', z)

            curr_Pt_shape.SetField('srcPt_x', self.srcpt_x)
            curr_Pt_shape.SetField('srcPt_y', self.srcpt_y)
            curr_Pt_shape.SetField('srcPt_z', self.srcpt_z)

            curr_Pt_shape.SetField('dip_dir', self.src_dipdir)
            curr_Pt_shape.SetField('dip_ang', self.src_dipang)

            # add the feature to the output layer
            self.out_layer.CreateFeature(curr_Pt_shape)            
            
            # destroy no longer used objects
            curr_Pt_geom.Destroy()
            curr_Pt_shape.Destroy()
                            
        # destroy output geometry
        self.out_shape.Destroy() 

        
          
            
            



