# -*- coding: utf-8 -*-

from __future__ import absolute_import
from builtins import str

import os
import sys


import webbrowser

from osgeo import ogr

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *

from qgis.core import *
from qgis.gui import *

from .geosurf.geoio import read_dem
from .geosurf.spatial import Vector_3D, list3_to_list, remove_equal_consecutive_xypairs
from .geosurf.svd import xyz_svd
from .geosurf.qt_utils import define_save_file_name, define_existing_file_name
from .geosurf.qgs_tools import *
from .geosurf.ogr_tools import create_shapefile, open_shapefile, write_point_result
from .geosurf.errors import OGR_IO_Errors, VectorIOException

from .pygsf.orientations.orientations import *


class bestfitplane_QWidget(QWidget):

    dem_default_text = '--  required  --'
    ptlnlyr_default_text = '--  choose  --'
        
    fields_dict_list = [dict(name='id', ogr_type=ogr.OFTInteger),
                         dict(name='x', ogr_type=ogr.OFTReal),
                         dict(name='y', ogr_type=ogr.OFTReal),
                         dict(name='z', ogr_type=ogr.OFTReal),
                         dict(name='dip_dir', ogr_type=ogr.OFTReal),
                         dict(name='dip_ang', ogr_type=ogr.OFTReal),
                         dict(name='descript', ogr_type=ogr.OFTString, width=50)]

    bfp_calc_update = pyqtSignal()

    def __init__(self, canvas, plugin):

        super(bestfitplane_QWidget, self).__init__()         
        self.canvas, self.plugin = canvas, plugin       
        self.init_params()                 
        self.setup_gui()



        self.bfp_calc_update.connect(self.update_bfpcalc_btn_state)

    def init_params(self):
 
        self.reset_dem_input_states()
        self.previousTool = None        
        self.input_points = None
        self.bestfitplane_point_markers = []  
        self.res_id = 0

        self.out_point_shapefile, self.out_point_shapelayer = None, None
        self.bestfitplane = None
        self.stop_shapefile_edits = False

    def reset_dem_input_states(self):
        
        self.dem, self.grid = None, None

    def setup_gui(self):

        dialog_layout = QVBoxLayout()
        main_widget = QTabWidget()        
        main_widget.addTab(self.setup_processing_tab(), "Processing")
        main_widget.addTab(self.setup_help_tab(), "Help")
                                     
        dialog_layout.addWidget(main_widget)                                     
        self.setLayout(dialog_layout)                    
        self.adjustSize()                       
        self.setWindowTitle('qgSurf - best fit plane')        

    def setup_processing_tab(self):
        
        plansurfaceWidget = QWidget()  
        plansurfaceLayout = QVBoxLayout()        
        plansurfaceLayout.addWidget(self.setup_source_dem())         
        plansurfaceLayout.addWidget(self.setup_source_points())   
        plansurfaceLayout.addWidget(self.setup_results_io())
        plansurfaceWidget.setLayout(plansurfaceLayout) 
        return plansurfaceWidget 

    def setup_source_dem(self):

        sourcedem_QGroupBox = QGroupBox(self.tr("Source DEM"))  
        
        sourcedemLayout = QGridLayout() 
    
        sourcedemLayout.addWidget(QLabel("Choose DEM layer"), 0, 0, 1, 1)        
        self.define_dem_QComboBox = QComboBox()
        self.define_dem_QComboBox.addItem(self.dem_default_text)
        sourcedemLayout.addWidget(self.define_dem_QComboBox, 0, 1, 1, 2)  

        self.refresh_raster_layer_list()
        QgsProject.instance().layerWasAdded.connect(self.refresh_raster_layer_list)
        QgsProject.instance().layerRemoved.connect(self.refresh_raster_layer_list)
                             
        sourcedem_QGroupBox.setLayout(sourcedemLayout)  
              
        return sourcedem_QGroupBox

    def setup_source_points(self):
        
        source_points_QGroupBox = QGroupBox(self.tr("Best-fit plane from points"))  
        
        source_points_Layout = QGridLayout() 

        self.bestfitplane_definepoints_pButton = QPushButton("Define source points in map")
        self.bestfitplane_definepoints_pButton.clicked.connect(self.bfp_inpoint_from_map_click)
        source_points_Layout.addWidget(self.bestfitplane_definepoints_pButton, 0, 0, 1, 2)

        self.bestfitplane_getpointsfromlyr_pButton = QPushButton("Get source points from layer")
        self.bestfitplane_getpointsfromlyr_pButton.clicked.connect(self.bfp_points_from_lyr)
        source_points_Layout.addWidget(self.bestfitplane_getpointsfromlyr_pButton, 1, 0, 1, 1)

        self.bestfitplane_inpts_lyr_list_QComboBox = QComboBox()
        source_points_Layout.addWidget(self.bestfitplane_inpts_lyr_list_QComboBox, 1, 1, 1, 1)

        self.bestfitplane_resetpoints_pButton = QPushButton("Reset source points")
        self.bestfitplane_resetpoints_pButton.clicked.connect(self.bfp_reset_all_inpoints)
        source_points_Layout.addWidget(self.bestfitplane_resetpoints_pButton, 2, 0, 1, 2)

        self.refresh_inpts_layer_list()
        QgsProject.instance().layerWasAdded.connect(self.refresh_inpts_layer_list)
        QgsProject.instance().layerRemoved.connect(self.refresh_inpts_layer_list)
        
        self.bestfitplane_src_points_ListWdgt = QListWidget()
        source_points_Layout.addWidget(self.bestfitplane_src_points_ListWdgt, 3, 0, 1, 2)

        self.bestfitplane_calculate_pButton = QPushButton("Calculate best-fit plane")
        self.bestfitplane_calculate_pButton.clicked.connect(self.calculate_bestfitplane)
        self.bestfitplane_calculate_pButton.setEnabled(False)
        source_points_Layout.addWidget(self.bestfitplane_calculate_pButton, 4, 0, 1, 2)

        self.enable_point_input_buttons(False)

        source_points_QGroupBox.setLayout(source_points_Layout) 
                 
        return source_points_QGroupBox

    def setup_results_io(self):
        
        export_points_QGroupBox = QGroupBox(self.tr("Save points"))  
        
        export_points_Layout = QGridLayout()        
        
        self.create_shapefile_pButton = QPushButton("Create new shapefile for result storage")
        self.create_shapefile_pButton.clicked.connect(self.make_shapefiles)
        self.create_shapefile_pButton.setEnabled(True)
        export_points_Layout.addWidget(self.create_shapefile_pButton, 0, 0, 1, 1)   
        
        self.use_shapefile_pButton = QPushButton("Load previous shapefile")
        self.use_shapefile_pButton.clicked.connect(self.use_shapefile)
        self.use_shapefile_pButton.setEnabled(True)
        export_points_Layout.addWidget(self.use_shapefile_pButton, 0, 1, 1, 1)   
                
        self.save_solution_pButton = QPushButton("Add current solution in shapefile")
        self.save_solution_pButton.clicked.connect(self.save_in_shapefile)
        self.save_solution_pButton.setEnabled(False)
        export_points_Layout.addWidget(self.save_solution_pButton, 1, 0, 1, 2)   

        self.stop_edit_pButton = QPushButton("Save and stop edits in shapefile")
        self.stop_edit_pButton.clicked.connect(self.stop_editing)
        self.stop_edit_pButton.setEnabled(False)
        export_points_Layout.addWidget(self.stop_edit_pButton, 2, 0, 1, 2)         
        
        export_points_QGroupBox.setLayout(export_points_Layout) 
                 
        return export_points_QGroupBox

    def setup_help_tab(self):

        qwdtHelp = QWidget()
        qlytHelp = QVBoxLayout()

        # About section

        qtbrHelp = QTextBrowser(qwdtHelp)
        url_path = "file:///{}/help/help_bfp.html".format(os.path.dirname(__file__))
        qtbrHelp.setSource(QUrl(url_path))
        qtbrHelp.setSearchPaths(['{}/help'.format(os.path.dirname(__file__))])
        qlytHelp.addWidget(qtbrHelp)

        qwdtHelp.setLayout(qlytHelp)

        return qwdtHelp

    def add_marker(self, prj_crs_x, prj_crs_y):
        
        marker = self.create_marker(self.canvas, prj_crs_x, prj_crs_y)       
        self.bestfitplane_point_markers.append(marker)        
        self.canvas.refresh()        

    def set_bfp_input_point(self, qgs_pt, add_marker = True): 

        prj_crs_x, prj_crs_y = qgs_pt.x(), qgs_pt.y()
        if self.on_the_fly_projection:     
            dem_crs_coord_x, dem_crs_coord_y = self.get_dem_crs_coords(prj_crs_x, prj_crs_y)
        else:
            dem_crs_coord_x, dem_crs_coord_y = prj_crs_x, prj_crs_y
                                
        if not self.coords_within_dem_bndr(dem_crs_coord_x, dem_crs_coord_y):
            return        
       
        if add_marker:
            self.add_marker(prj_crs_x, prj_crs_y)
       
        curr_point = Point_2D(float(dem_crs_coord_x), float(dem_crs_coord_y))        
        currArrCoord = self.grid.geog2array_coord(curr_point)     
        dem_z_value = self.grid.interpolate_bilinear(currArrCoord)
        
        self.bestfitplane_points.append([prj_crs_x, prj_crs_y, dem_z_value])        
        self.bestfitplane_src_points_ListWdgt.addItem("%.3f %.3f %.3f" % (prj_crs_x, prj_crs_y, dem_z_value))

        self.bfp_calc_update.emit()

    def bfp_reset_all_inpoints(self):
        
        self.reset_point_input_values()
        self.bfp_calc_update.emit()
                       
    def bfp_inpoint_from_map_click(self):
       
        try:
            self.bestfitplane_PointMapTool.canvasClicked.disconnect(self.set_bfp_input_point)
        except:
            pass
        
        self.update_crs_settings()
                      
        self.bestfitplane_PointMapTool = PointMapToolEmitPoint(self.canvas, self.plugin) # mouse listener
        self.previousTool = self.canvas.mapTool() # save the standard map tool for restoring it at the end
        self.bestfitplane_PointMapTool.canvasClicked.connect(self.set_bfp_input_point)
        self.bestfitplane_PointMapTool.setCursor(Qt.CrossCursor)        
        self.canvas.setMapTool(self.bestfitplane_PointMapTool)

    def bfp_points_from_lyr(self):
        
        # get vector layer
        
        try:
            assert self.bestfitplane_inpts_lyr_list_QComboBox.currentIndex() > 0
            inpts_lyr_qgis_ndx = self.bestfitplane_inpts_lyr_list_QComboBox.currentIndex() - 1
            inpts_lyr = self.inpts_Layers[inpts_lyr_qgis_ndx ]
        except:
            QMessageBox.critical(self, 
                                  "Input point layer", 
                                  "Check chosen input layer") 
            return

        # read xy tuples from layer (removed consecutive duplicates)
        layer_geom_type = vector_type(inpts_lyr)
        if layer_geom_type == 'point':
            xypair_list = pt_geoms_attrs(inpts_lyr)
        elif layer_geom_type == 'line':
            xypair_list3 = line_geoms_attrs(inpts_lyr)
            xypair_list3_1 = [xypair_list02[0] for xypair_list02 in xypair_list3 ]
            xypair_flatlist = list3_to_list(xypair_list3_1)
            xypair_list = remove_equal_consecutive_xypairs(xypair_flatlist)
        else:
            raise VectorIOException("Geometry type of chosen layer is not point or line")
        
        if len(xypair_list) > 50:
            QMessageBox.critical(self, 
                                  "Input point layer", 
                                  "More than 50 points to handle. Please use less features") 
            return            

        # for all xy tuples, project to project CRS as a qgis point
        self.update_crs_settings()
        if self.on_the_fly_projection:
            proj_crs_qgispoint_list = [project_qgs_point(qgs_point(x,y), inpts_lyr.crs(), self.projectCrs) for (x,y) in xypair_list ]
        else:
            proj_crs_qgispoint_list = [qgs_point(xypair[0], xypair[1]) for xypair in xypair_list ]
                
        # for all qgs points, process them for the input point processing queue
        for qgs_pt in proj_crs_qgispoint_list:
            self.set_bfp_input_point(qgs_pt, add_marker = False)

    def update_crs_settings(self):

        self.get_on_the_fly_projection()
        if self.on_the_fly_projection: 
            self.get_current_canvas_crs()
        
    def get_on_the_fly_projection(self):
        
        self.on_the_fly_projection = True
        
    def get_current_canvas_crs(self):        
                
        self.projectCrs = self.canvas.mapSettings().destinationCrs()

    def reset_input_point_states(self):
       
        self.reset_point_input_values()        
        self.disable_point_tools()

        self.bfp_calc_update.emit()

    def reset_point_input_values(self):

        self.reset_point_markers()
        self.reset_point_inputs()  

    def reset_point_inputs(self):

        self.bestfitplane_src_points_ListWdgt.clear()
        self.bestfitplane_points = []  

    def reset_point_markers(self):

        for mrk in self.bestfitplane_point_markers:
            self.canvas.scene().removeItem(mrk)  
        self.bestfitplane_point_markers = []          

    def enable_point_input_buttons(self, choice = True):
        
        self.bestfitplane_definepoints_pButton.setEnabled(choice)
        self.bestfitplane_getpointsfromlyr_pButton.setEnabled(choice)
        self.bestfitplane_inpts_lyr_list_QComboBox.setEnabled(choice)
        self.bestfitplane_resetpoints_pButton.setEnabled(choice)

    def enable_point_save_buttons(self, choice=True):

        self.stop_edit_pButton.setEnabled(choice)

    def disable_point_tools(self):

        self.enable_point_input_buttons(False)
        self.enable_point_save_buttons(False)
        
        try: 
            self.bestfitplane_PointMapTool.leftClicked.disconnect(self.set_bfp_input_point)
        except: 
            pass
        try: 
            self.disable_MapTool(self.bestfitplane_PointMapTool)
        except: 
            pass         

    def refresh_raster_layer_list(self):

        self.reset_dem_input_states()
                
        try: 
            self.define_dem_QComboBox.currentIndexChanged[int].disconnect(self.get_working_dem)
        except: 
            pass
         
        try:               
            self.reset_input_point_states()
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

    def refresh_inpts_layer_list(self):
        
        try:
            self.bestfitplane_inpts_lyr_list_QComboBox.clear()
        except:
            return
        
        self.bestfitplane_inpts_lyr_list_QComboBox.addItem(bestfitplane_QWidget.ptlnlyr_default_text)
                                  
        self.inpts_Layers = loaded_point_layers() + loaded_line_layers()                
        if self.inpts_Layers is None or len(self.inpts_Layers) == 0:
            return
        for layer in self.inpts_Layers: 
            self.bestfitplane_inpts_lyr_list_QComboBox.addItem(layer.name())

    def get_working_dem(self, ndx_DEM_file = 0): 
        
        self.reset_dem_input_states()       
        self.reset_input_point_states()        
        if self.rasterLayers is None or len(self.rasterLayers) == 0: 
            return          
                                
        # no DEM layer defined  
        if ndx_DEM_file == 0: 
            return             

        self.dem = self.rasterLayers[ndx_DEM_file-1]        
        try:
            self.grid = read_dem(self.dem.source())               
        except IOError as e:
            QMessageBox.critical(self, "DEM", str(e))
            return

        if self.grid is None: 
            QMessageBox.critical(self, "DEM", "DEM was not read")
            return

        if self.grid.domain.g_xrange() <= 360.0 and self.grid.domain.g_yrange() <= 180.0:
            QMessageBox.warning(self, "DEM", "The used DEM appears to be in polar coordinates (i.e., lat-lon).\n\nAssign a planar CRS (e.g., UTM, Lambert Conformal Conic) to the project to avoid getting incorrect results.")
               
        self.enable_point_input_buttons()

    def coords_within_dem_bndr(self, dem_crs_coord_x, dem_crs_coord_y):
        
        if dem_crs_coord_x <= self.grid.xmin or dem_crs_coord_x >= self.grid.xmax or \
           dem_crs_coord_y <= self.grid.ymin or dem_crs_coord_y >= self.grid.ymax:
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

    def update_bfpcalc_btn_state(self):

        if self.bestfitplane_src_points_ListWdgt.count () >= 3:
            state = True
        else:
            state = False

        self.bestfitplane_calculate_pButton.setEnabled(state)

    def calculate_bestfitplane(self):        

        xyz_list = self.bestfitplane_points        
        xyz_array = np.array(xyz_list, dtype=np.float64)
        self.xyz_mean = np.mean(xyz_array, axis = 0)
        svd = xyz_svd(xyz_array - self.xyz_mean)
        if svd['result'] == None:
            QMessageBox.critical(self, 
                                  "Best fit plane", 
                                  "Unable to calculate result")
            return
        _, _, eigenvectors = svd['result'] 
        lowest_eigenvector = eigenvectors[-1, : ]  # Solution is last row
        normal = lowest_eigenvector[: 3 ] / np.linalg.norm(lowest_eigenvector[: 3 ])        
        normal_vector = Vector_3D(normal[0], normal[1], normal[2])
        normal_axis = normal_vector.to_geol_axis()
        self.bestfitplane = normal_axis.to_normal_geolplane()
        
        QMessageBox.information(self, "Best fit geological plane", 
                                 "Dip direction: %.1f - dip angle: %.1f" %(self.bestfitplane._dipdir, self.bestfitplane._dipangle))

        self.update_save_solution_state()

    def update_save_solution_state(self):

        if self.out_point_shapefile is not None and self.out_point_shapelayer is not None and \
                self.bestfitplane is not None and not self.stop_shapefile_edits:
            self.save_solution_pButton.setEnabled(True)
        else:
            self.save_solution_pButton.setEnabled(False)

    def view_plane_in_stereonet(self):
        """
        Plot plane solution in stereonet.

        :return: None
        """

        # plane = self.bestfitplane
        # splot([(plane, "c=blue")])

        x = np.linspace(0, 10, 501)
        y = np.tan(x)

        qapp = QApplication(sys.argv)

        app = PlotWindow(x, y)
        app.show()
        qapp.exec_()

    def disable_points_definition(self):
        
        self.enable_point_input_buttons(False)

        self.disable_points_MapTool()
        self.reset_point_markers()
        self.bestfitplane_src_points_ListWdgt.clear()

    def disable_MapTool(self, mapTool):
                            
        try:
            if mapTool is not None: self.canvas.unsetMapTool(mapTool)
        except:
            pass                            

        try:
            if self.previousTool is not None: self.canvas.setMapTool(self.previousTool)
        except:
            pass

    def disable_points_MapTool(self):
        
        self.disable_MapTool(self.bestfitplane_PointMapTool)

    def project_coords(self, x, y, source_crs, dest_crs):
        
        if self.on_the_fly_projection and source_crs != dest_crs:
            dest_crs_qgs_pt = project_qgs_point(qgs_point(x, y), source_crs, dest_crs)
            return  dest_crs_qgs_pt.x(), dest_crs_qgs_pt.y() 
        else:
            return  x, y        

    def get_dem_crs_coords(self, x, y):
    
        return self.project_coords(x, y, self.projectCrs, self.dem.crs())

    def get_prj_crs_coords(self, x, y):

        return self.project_coords(x, y, self.dem.crs(), self.projectCrs)

    def make_shapefiles(self):

        dialog = NewShapeFilesDialog(self)

        if dialog.exec_():
            point_shapefile_path = dialog.output_point_shape_QLineEdit.text()
        else:
            return

        if point_shapefile_path == "": 
            QMessageBox.critical(self, 
                                  "Point shapefile", 
                                  "No path provided")
            return

        self.point_shapefile_path = point_shapefile_path

        self.out_point_shapefile, self.out_point_shapelayer = create_shapefile(point_shapefile_path, 
                                                                                  ogr.wkbPoint, 
                                                                                  bestfitplane_QWidget.fields_dict_list,
                                                                                  self.projectCrs)
        QMessageBox.information(self, "Shapefile", "Point shapefile created ")

        self.update_save_solution_state()

    def use_shapefile(self):
        
        dialog = PrevShapeFilesDialog(self)

        # update_point_shape, update_polygon_shape = False, False
        if dialog.exec_():
            point_shapefile_path = dialog.input_point_shape_QLineEdit.text()
        else:
            return

        if point_shapefile_path == "": 
            QMessageBox.critical(self, 
                                  "Point shapefile", 
                                  "No path provided")
            return

        self.point_shapefile_path = point_shapefile_path

        try:
            self.out_point_shapefile, self.out_point_shapelayer, prev_solution_list = open_shapefile(self.point_shapefile_path, bestfitplane_QWidget.fields_dict_list)
        except OGR_IO_Errors:
            self.out_point_shapefile, self.out_point_shapelayer = None, None
            QMessageBox.critical(self, 
                                  "Point shapefile", 
                                  "Shapefile cannot be edited")
            return            
        
        if len(prev_solution_list) == 0:
            QMessageBox.critical(self, 
                                  "Point shapefile", 
                                  "Shapefile is empty")
            return                      
        
        write_point_result(self.out_point_shapefile, self.out_point_shapelayer, prev_solution_list)

        self.res_id = max([rec[0] for rec in prev_solution_list ])

        self.update_save_solution_state()

    def save_in_shapefile(self):
                
        descr_dialog = SolutionDescriptDialog(self)
        if descr_dialog.exec_():
            description = descr_dialog.description_QLineEdit.text()
        else:
            return

        self.res_id += 1
                
        solution_list = []
        for rec in self.bestfitplane_points:
            solution_list.append([self.res_id, rec[0], rec[1], rec[2], self.bestfitplane._dipdir, self.bestfitplane._dipangle, str(description) ])

        # if self.update_point_shape:          
        write_point_result(self.out_point_shapefile, self.out_point_shapelayer, solution_list)

        self.save_solution_pButton.setEnabled(False)
        self.stop_edit_pButton.setEnabled(True)

    def stop_editing(self):
        
        try:
            self.out_point_shapefile.Destroy()
            QMessageBox.information(self, 
                                  self.tr("Results"), 
                                  self.tr("Results saved in shapefile.<br />Now you can load it"))            
            
        except:
            pass

        self.stop_shapefile_edits = True
        self.enable_point_save_buttons(False)
        self.update_save_solution_state()

        
class NewShapeFilesDialog(QDialog):
    
    def __init__(self, parent=None):
        
        super(NewShapeFilesDialog, self).__init__(parent)
    
        #self.pointCheckBox = QCheckBox("&Point shapefile:")
        self.output_point_shape_QLineEdit = QLineEdit()
        self.output_point_shape_browse_QPushButton = QPushButton(".....")
        self.output_point_shape_browse_QPushButton.clicked.connect(self.set_out_point_shapefile_name)
        
        """"
        self.polygonCheckBox = QCheckBox("&Polygon shapefile:")
        self.output_polygon_shape_QLineEdit = QLineEdit()
        self.output_polygon_shape_browse_QPushButton = QPushButton(".....")
        self.output_polygon_shape_browse_QPushButton.clicked.connect(self.set_out_polygon_shapefile_name)
        """
        
        okButton = QPushButton("&OK")
        cancelButton = QPushButton("Cancel")

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(okButton)
        buttonLayout.addWidget(cancelButton)
        
        layout = QGridLayout()

        layout.addWidget(self.output_point_shape_QLineEdit, 0, 1, 1, 1) 
        layout.addWidget(self.output_point_shape_browse_QPushButton, 0, 2, 1, 1) 

        layout.addLayout(buttonLayout, 2, 0, 1, 3)
        self.setLayout(layout)

        okButton.clicked.connect(self.accept)
        cancelButton.clicked.connect(self.reject)

        self.setWindowTitle("Create shapefile")

    def set_out_point_shapefile_name(self):
        
        out_shapefile_name = define_save_file_name(self, 
                                                    "Choose shapefile name", 
                                                    "*.shp", 
                                                    "shp (*.shp *.SHP)")
        
        self.output_point_shape_QLineEdit.setText(out_shapefile_name)

    def set_out_polygon_shapefile_name(self):
        
        out_shapefile_name = define_save_file_name(self, 
                                                    "Choose shapefile name", 
                                                    "*.shp", 
                                                    "shp (*.shp *.SHP)")
        
        self.output_polygon_shape_QLineEdit.setText(out_shapefile_name)


class PrevShapeFilesDialog(QDialog):
    
    def __init__(self, parent=None):
        
        super(PrevShapeFilesDialog, self).__init__(parent)
    
        # self.pointCheckBox = QCheckBox("&Point shapefile:")
        self.input_point_shape_QLineEdit = QLineEdit()
        self.input_point_shape_browse_QPushButton = QPushButton(".....")
        self.input_point_shape_browse_QPushButton.clicked.connect(self.set_in_point_shapefile_name)

        okButton = QPushButton("&OK")
        cancelButton = QPushButton("Cancel")

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(okButton)
        buttonLayout.addWidget(cancelButton)
        
        layout = QGridLayout()
        layout.addWidget(self.input_point_shape_QLineEdit, 0, 1, 1, 1)
        layout.addWidget(self.input_point_shape_browse_QPushButton, 0, 2, 1, 1) 

        layout.addLayout(buttonLayout, 2, 0, 1, 3)
        self.setLayout(layout)

        okButton.clicked.connect(self.accept)
        cancelButton.clicked.connect(self.reject)
        
        self.setWindowTitle("Get shapefile")

    def set_in_point_shapefile_name(self):
        
        in_shapefile_name = define_existing_file_name(self, 
                                                    "Choose shapefile name", 
                                                    "*.shp", 
                                                    "shp (*.shp *.SHP)")
        
        self.input_point_shape_QLineEdit.setText(in_shapefile_name)

    def set_in_polygon_shapefile_name(self):
        
        in_shapefile_name = define_existing_file_name(self, 
                                                    "Choose shapefile name", 
                                                    "*.shp", 
                                                    "shp (*.shp *.SHP)")
        
        self.input_polygon_shape_QLineEdit.setText(in_shapefile_name)
    

class SolutionDescriptDialog(QDialog):
    
    def __init__(self, parent=None):
        
        super(SolutionDescriptDialog, self).__init__(parent)

        layout = QVBoxLayout()
        
        descr_layout = QHBoxLayout()
        descr_layout.addWidget(QLabel("Description (max 50 char.)"))
        self.description_QLineEdit = QLineEdit()
        self.description_QLineEdit.setMaxLength(50)
        descr_layout.addWidget(self.description_QLineEdit)

        okButton = QPushButton("&OK")
        cancelButton = QPushButton("Cancel")

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(okButton)
        buttonLayout.addWidget(cancelButton)

        layout.addLayout(descr_layout)                
        layout.addLayout(buttonLayout)
        self.setLayout(layout)

        okButton.clicked.connect(self.accept)
        cancelButton.clicked.connect(self.reject)
        
        self.setWindowTitle("Solution")

