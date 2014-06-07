# -*- coding: utf-8 -*-

import os

from math import floor
import numpy as np

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from osgeo import ogr

from qgis.core import *
from qgis.gui import *

from qgs_tools.tools import get_current_raster_layers, project_point, \
     make_qgs_point
from qgs_tools.ptmaptool import PointMapToolEmitPoint
    
from geosurf.geoio import read_dem
from geosurf.spatial import Point_2D, Vector_3D
from geosurf.svd import xyz_svd 
from qt_utils.utils import define_save_file_name, define_existing_file_name

from ogr_tools.shapefiles import create_shapefile, open_shapefile, write_point_result
from ogr_tools.errors import OGR_IO_Errors
  
import webbrowser

      

class bestfitplane_QWidget( QWidget ):

    # line_colors = [ "white", "red", "blue", "yellow", "orange", "brown",]
    dem_default_text = '--  required  --'
    
    fields_dict_list = [ dict(name='id', ogr_type=ogr.OFTInteger ),
                     dict(name='x', ogr_type=ogr.OFTReal ),
                     dict(name='y', ogr_type=ogr.OFTReal ),
                     dict(name='z', ogr_type=ogr.OFTReal ),
                     dict(name='dip_dir', ogr_type=ogr.OFTReal ),
                     dict(name='dip_ang', ogr_type=ogr.OFTReal ),
                     dict(name='descript', ogr_type=ogr.OFTString, width=50 )  ]
            


    def __init__( self, canvas, plugin ):

        super( bestfitplane_QWidget, self ).__init__()         
        self.canvas, self.plugin = canvas, plugin       
        self.init_params()                 
        self.setup_gui() 


            
    def init_params(self):
 
        self.previousTool = None        
        self.grid = None
        self.input_points = None
        self.bestfitplane_point_markers = []  
        self.res_id = 0       

        
    def setup_gui( self ):

        dialog_layout = QVBoxLayout()
        main_widget = QTabWidget()        
        main_widget.addTab( self.setup_fplane_tab(), "Processing" )         
        main_widget.addTab( self.setup_about_tab(), "About" )                             
        dialog_layout.addWidget( main_widget )                                     
        self.setLayout( dialog_layout )                    
        self.adjustSize()                       
        self.setWindowTitle( 'qgSurf - best fit plane' )        


    def setup_fplane_tab( self ):
        
        plansurfaceWidget = QWidget()  
        plansurfaceLayout = QVBoxLayout( )        
        plansurfaceLayout.addWidget( self.setup_source_dem() )         
        plansurfaceLayout.addWidget( self.setup_source_points() )   
        plansurfaceLayout.addWidget( self.setup_export_points() )
        plansurfaceLayout.addWidget( self.setup_help() )                                     
        plansurfaceWidget.setLayout( plansurfaceLayout ) 
        return plansurfaceWidget 


    def setup_source_dem( self ):

        sourcedem_QGroupBox = QGroupBox( self.tr("Source DEM") )  
        
        sourcedemLayout = QGridLayout( ) 
     
        self.raster_refreshlayers_pButton = QPushButton( "Get current raster layers" )
        self.raster_refreshlayers_pButton.clicked[bool].connect( self.refresh_raster_layer_list ) 
        self.raster_refreshlayers_pButton.setEnabled( True )       
        sourcedemLayout.addWidget( self.raster_refreshlayers_pButton, 0, 0, 1, 3 )                
        sourcedemLayout.addWidget(QLabel( "Use" ), 1, 0, 1, 1)        
        self.dem_comboBox = QComboBox()
        self.dem_comboBox.addItem(self.dem_default_text)
        sourcedemLayout.addWidget(self.dem_comboBox, 1, 1, 1, 2)  
              
        sourcedem_QGroupBox.setLayout( sourcedemLayout )  
              
        return sourcedem_QGroupBox


    def setup_source_points( self ):
        
        source_points_QGroupBox = QGroupBox( self.tr("Best-fit plane from points") )  
        
        source_points_Layout = QGridLayout( ) 

        self.bestfitplane_definepoints_pButton = QPushButton( "Define source points in map" )
        self.bestfitplane_definepoints_pButton.clicked.connect( self.set_bfp_points )
        self.bestfitplane_definepoints_pButton.setEnabled( False )
        source_points_Layout.addWidget( self.bestfitplane_definepoints_pButton, 0, 0, 1, 2 )
        
        self.bestfitplane_src_points_ListWdgt = QListWidget()
        source_points_Layout.addWidget( self.bestfitplane_src_points_ListWdgt, 1, 0, 1, 2 )
        
        self.bestfitplane_calculate_pButton = QPushButton( "Calculate best-fit plane" )
        self.bestfitplane_calculate_pButton.clicked.connect( self.calculate_bestfitplane )
        self.bestfitplane_calculate_pButton.setEnabled( False )
        source_points_Layout.addWidget( self.bestfitplane_calculate_pButton, 2, 0, 1, 2 )   

        source_points_QGroupBox.setLayout( source_points_Layout ) 
                 
        return source_points_QGroupBox


    def setup_export_points( self ):
        
        export_points_QGroupBox = QGroupBox( self.tr("Save points") )  
        
        export_points_Layout = QGridLayout( )        
        
        self.create_shapefile_pButton = QPushButton( "Create shapefile for storing results" )
        self.create_shapefile_pButton.clicked.connect( self.make_shapefiles )
        self.create_shapefile_pButton.setEnabled( False )
        export_points_Layout.addWidget( self.create_shapefile_pButton, 0, 0, 1, 1 )   
        
        self.use_shapefile_pButton = QPushButton( "Use previous shapefile" )
        self.use_shapefile_pButton.clicked.connect( self.use_shapefile )
        self.use_shapefile_pButton.setEnabled( False )
        export_points_Layout.addWidget( self.use_shapefile_pButton, 0, 1, 1, 1 )   
                
        self.save_solution_pButton = QPushButton( "Add current solution in shapefile" )
        self.save_solution_pButton.clicked.connect( self.save_in_shapefile )
        self.save_solution_pButton.setEnabled( False )
        export_points_Layout.addWidget( self.save_solution_pButton, 1, 0, 1, 2 )   

        self.stop_edit_pButton = QPushButton( "Save and stop edits in shapefile" )
        self.stop_edit_pButton.clicked.connect( self.stop_editing )
        self.stop_edit_pButton.setEnabled( False )
        export_points_Layout.addWidget( self.stop_edit_pButton, 2, 0, 1, 2 )         
        
        export_points_QGroupBox.setLayout( export_points_Layout ) 
                 
        return export_points_QGroupBox
    
 
    def setup_help( self ):
        
        help_QGroupBox = QGroupBox( self.tr("Help") )  
        
        helpLayout = QVBoxLayout( ) 
                
        self.help_pButton = QPushButton( "Open help in browser" )
        self.help_pButton.clicked[bool].connect( self.open_html_help ) 
        self.help_pButton.setEnabled( True )       
        helpLayout.addWidget( self.help_pButton ) 
                
        help_QGroupBox.setLayout( helpLayout )  
              
        return help_QGroupBox
    
               
    def set_bfp_points(self):
       
        try:
            self.bestfitplane_PointMapTool.canvasClicked.disconnect( self.get_point_from_map )
        except:
            pass
                    
        self.reset_point_values() 
        
        self.update_crs_settings()
                      
        self.bestfitplane_PointMapTool = PointMapToolEmitPoint( self.canvas, self.plugin ) # mouse listener
        self.previousTool = self.canvas.mapTool() # save the standard map tool for restoring it at the end
        self.bestfitplane_PointMapTool.canvasClicked.connect( self.get_point_from_map )
        self.bestfitplane_PointMapTool.setCursor( Qt.CrossCursor )        
        self.canvas.setMapTool( self.bestfitplane_PointMapTool )


    def setup_about_tab( self ):
        
        helpWidget = QWidget()  
        helpLayout = QVBoxLayout( )        
        htmlText = """
<h3>qgSurf - Best Fit Plane</h3>
This module allows to calculate the best-fit plane given a DEM and a set of user-defined points.
<br /><br />Created and maintained by M. Alberti (www.malg.eu). 
<br />Licensed under the terms of GNU GPL 3.
        """
        
        helpQTextBrowser = QTextBrowser( helpWidget )        
        helpQTextBrowser.insertHtml( htmlText ) 
        helpLayout.addWidget( helpQTextBrowser )
        helpWidget.setLayout(helpLayout)                  
        return helpWidget 
        

    def update_crs_settings( self ):

        self.get_on_the_fly_projection()
        if self.on_the_fly_projection: self.get_current_canvas_crs()        
        
        
    def get_on_the_fly_projection( self ):
        
        self.on_the_fly_projection = True if self.canvas.hasCrsTransformEnabled() else False
       
        
    def get_current_canvas_crs( self ):        
                
        self.projectCrs = self.canvas.mapRenderer().destinationCrs()


    def reset_all(self):
       
        self.reset_point_values()        
        self.disable_tools()


    def reset_point_values(self):

        self.reset_point_markers()
        self.reset_point_inputs()  


    def reset_point_inputs( self ):

        self.bestfitplane_src_points_ListWdgt.clear()
        self.bestfitplane_points = []  


    def reset_point_markers( self ):

        for mrk in self.bestfitplane_point_markers:
            self.canvas.scene().removeItem( mrk )  
        self.bestfitplane_point_markers = []          
        

    def disable_tools( self ):

        self.bestfitplane_definepoints_pButton.setEnabled( False ); self.bestfitplane_calculate_pButton.setEnabled( False )
        try: 
            self.bestfitplane_PointMapTool.leftClicked.disconnect( self.get_point_from_map )
        except: 
            pass
        try: 
            self.disable_MapTool( self.bestfitplane_PointMapTool )
        except: 
            pass         
        

    def refresh_raster_layer_list( self ):

        self.dem, self.grid = None, None        
        try: 
            self.dem_comboBox.currentIndexChanged[int].disconnect( self.get_dem )
        except: 
            pass                
        self.reset_all()                    
        self.rasterLayers = get_current_raster_layers()                 
        if self.rasterLayers is None or len( self.rasterLayers ) == 0:
            QMessageBox.critical( self, "Source DEMs", "No raster layer found in current project" )
            return
        self.dem_comboBox.clear()
        self.dem_comboBox.addItem( self.dem_default_text )
        for layer in self.rasterLayers: 
            self.dem_comboBox.addItem( layer.name() )            
        self.dem_comboBox.currentIndexChanged[int].connect( self.get_dem )                
        QMessageBox.information( self, "Source DEMs", "Found %d raster layers.<br /><br />Select one in 'Use DEM' (below).<br /><br />Warning: <b>when using DEMs in lat-long</b>, set the project CRS to a planar projection, with horizontal distances and heights in the same units (e.g., meters)." % len( self.rasterLayers ))

              
    def get_dem( self, ndx_DEM_file = 0 ): 
        
        self.dem = None        
        self.reset_all()        
        if self.rasterLayers is None or len( self.rasterLayers ) == 0: 
            return          
                                
        # no DEM layer defined  
        if ndx_DEM_file == 0: 
            return             

        self.dem = self.rasterLayers[ndx_DEM_file-1]        
        try:
            self.grid = read_dem( self.dem.source() )               
        except IOError, e:
            QMessageBox.critical( self, "DEM", str( e ) )
            return

        if self.grid is None: 
            QMessageBox.critical( self, "DEM", "DEM was not read" )
            return

        self.bestfitplane_definepoints_pButton.setEnabled( True )
        

    def coords_within_dem_bndr( self, dem_crs_coord_x, dem_crs_coord_y):
        
        if dem_crs_coord_x <= self.grid.xmin or dem_crs_coord_x >= self.grid.xmax or \
           dem_crs_coord_y <= self.grid.ymin or dem_crs_coord_y >= self.grid.ymax:
            return False        
        return True        
        

    def create_marker(self, canvas, prj_crs_x, prj_crs_y, pen_width= 2, icon_type = 2, icon_size = 18, icon_color = 'limegreen' ):
        
        marker = QgsVertexMarker( canvas )
        marker.setIconType( icon_type )
        marker.setIconSize( icon_size )
        marker.setPenWidth( pen_width )
        marker.setColor( QColor( icon_color ) )
        marker.setCenter(QgsPoint( prj_crs_x, prj_crs_y ))         
        return marker        
        
                
    def get_point_from_map( self, qgs_point, button ): 

        prj_crs_x, prj_crs_y = qgs_point.x(), qgs_point.y()
        if self.on_the_fly_projection:     
            dem_crs_coord_x, dem_crs_coord_y = self.get_dem_crs_coords( prj_crs_x, prj_crs_y )
        else:
            dem_crs_coord_x, dem_crs_coord_y = prj_crs_x, prj_crs_y
                                
        if not self.coords_within_dem_bndr( dem_crs_coord_x, dem_crs_coord_y): return        
       
        marker = self.create_marker( self.canvas, prj_crs_x, prj_crs_y )       
        self.bestfitplane_point_markers.append( marker )        
        self.canvas.refresh()
       
        curr_point = Point_2D( float( dem_crs_coord_x), float( dem_crs_coord_y) )        
        currArrCoord = self.grid.geog2array_coord(curr_point)     
        dem_z_value = floor(self.grid.interpolate_bilinear(currArrCoord))
        
        self.bestfitplane_points.append( [prj_crs_x, prj_crs_y, dem_z_value] )        
        self.bestfitplane_src_points_ListWdgt.addItem( "%.3f %.3f %.3f" % ( prj_crs_x, prj_crs_y, dem_z_value ) )
        
        if self.bestfitplane_src_points_ListWdgt.count () >= 3:
            self.bestfitplane_calculate_pButton.setEnabled( True )

     
    def calculate_bestfitplane(self):        

        xyz_list = self.bestfitplane_points        
        xyz_array = np.array( xyz_list, dtype=np.float64 )
        self.xyz_mean = np.mean( xyz_array, axis = 0 )
        svd = xyz_svd( xyz_array - self.xyz_mean )
        if svd['result'] == None:
            QMessageBox.critical( self, 
                                  "Best fit plane", 
                                  "Unable to calculate result")
            return
        _, _, eigenvectors = svd['result'] 
        lowest_eigenvector = eigenvectors[ -1, : ]  # Solution is last row
        normal = lowest_eigenvector[ : 3 ] / np.linalg.norm( lowest_eigenvector[ : 3 ] )        
        normal_vector = Vector_3D( normal[0], normal[1], normal[2])
        normal_axis = normal_vector.to_geol_axis()
        self.bestfitplane = normal_axis.to_normal_geolplane()
        
        QMessageBox.information( self, "Best fit geological plane", 
                                 "Dip direction: %.1f - dip angle: %.1f" %( self.bestfitplane._dipdir, self.bestfitplane._dipangle ))
    
        self.create_shapefile_pButton.setEnabled( True )
        self.use_shapefile_pButton.setEnabled( True )
    
    
    def disable_points_definition(self):
        
        self.bestfitplane_definepoints_pButton.setEnabled( False )
        self.disable_points_MapTool()
        self.reset_point_markers()
        self.bestfitplane_src_points_ListWdgt.clear()
        
           
    def disable_MapTool( self, mapTool ):
                            
        try:
            if mapTool is not None: self.canvas.unsetMapTool( mapTool )
        except:
            pass                            

        try:
            if self.previousTool is not None: self.canvas.setMapTool( self.previousTool )
        except:
            pass


    def disable_points_MapTool( self ):
        
        self.disable_MapTool( self.bestfitplane_PointMapTool )
        

    def project_coords( self, x, y, source_crs, dest_crs ):
        
        if self.on_the_fly_projection and source_crs != dest_crs:
            dest_crs_qgs_pt = project_point( make_qgs_point( x, y ), source_crs, dest_crs )
            return  dest_crs_qgs_pt.x(), dest_crs_qgs_pt.y() 
        else:
            return  x, y        
       

    def get_dem_crs_coords( self, x, y ):
    
        return self.project_coords( x, y, self.projectCrs, self.dem.crs() )


    def get_prj_crs_coords( self, x, y ):

        return self.project_coords( x, y, self.dem.crs(), self.projectCrs )
        

    def make_shapefiles(self ):

        dialog = NewShapeFilesDialog(self)

        # create_point_shape, create_polygon_shape = False, False
        if dialog.exec_():
            # create_point_shape = dialog.pointCheckBox.isChecked()
            point_shapefile_path = dialog.output_point_shape_QLineEdit.text()
            # create_polygon_shape = dialog.polygonCheckBox.isChecked()
            # polygon_shapefile_path = dialog.output_polygon_shape_QLineEdit.text()
         
        """   
        if not ( create_point_shape or create_polygon_shape):
            return
        """
        if point_shapefile_path == "": 
            QMessageBox.critical( self, 
                                  "Point shapefile", 
                                  "No path provided")
            return
        """
        if create_polygon_shape and polygon_shapefile_path == "": 
            QMessageBox.critical( self, 
                                  "Polygon shapefile", 
                                  "No path provided")
            return
        """
        
        # self.update_point_shape = create_point_shape
        # self.update_polygon_shape = create_polygon_shape
        self.point_shapefile_path = point_shapefile_path
        # self.polygon_shapefile_path = polygon_shapefile_path
                        
        #if self.update_point_shape:            
        self.out_point_shapefile, self.out_point_shapelayer = create_shapefile(point_shapefile_path, 
                                                                                  ogr.wkbPoint, 
                                                                                  bestfitplane_QWidget.fields_dict_list
                                                                                  #,  self.projectCrs, ## adegua def crs con funzione chiamata 
                                                                                 )
        QMessageBox.information( self, "Shapefile", "Point shapefile created " )
            
        self.save_solution_pButton.setEnabled( True )
            
                
    def use_shapefile(self):
        
        dialog = PrevShapeFilesDialog(self)

        # update_point_shape, update_polygon_shape = False, False
        if dialog.exec_():
            # update_point_shape = dialog.pointCheckBox.isChecked()
            point_shapefile_path = dialog.input_point_shape_QLineEdit.text()
            # update_polygon_shape = dialog.polygonCheckBox.isChecked()
            # polygon_shapefile_path = dialog.input_polygon_shape_QLineEdit.text()
        
        """    
        if not ( update_point_shape or update_polygon_shape):
            return
        """
        if point_shapefile_path == "": 
            QMessageBox.critical( self, 
                                  "Point shapefile", 
                                  "No path provided")
            return
        """
        if update_polygon_shape and polygon_shapefile_path == "": 
            QMessageBox.critical( self, 
                                  "Polygon shapefile", 
                                  "No path provided")
            return
        """

        #self.update_point_shape = update_point_shape
        #self.update_polygon_shape = update_polygon_shape
        self.point_shapefile_path = point_shapefile_path
        #self.polygon_shapefile_path = polygon_shapefile_path
        
        try:
            self.out_point_shapefile, self.out_point_shapelayer, prev_solution_list = open_shapefile( self.point_shapefile_path, bestfitplane_QWidget.fields_dict_list )
        except OGR_IO_Errors:
            QMessageBox.critical( self, 
                                  "Point shapefile", 
                                  "Shapefile cannot be edited")
            return            
        
        
        write_point_result( self.out_point_shapefile, self.out_point_shapelayer, prev_solution_list )
        
        self.res_id = max( [ rec[0] for rec in prev_solution_list ] )
         
        self.save_solution_pButton.setEnabled( True ) 
                  
    
    def save_in_shapefile( self ):
                
        descr_dialog = SolutionDescriptDialog( self )
        if descr_dialog.exec_():
            description = descr_dialog.description_QLineEdit.text()
        else:
            return

        self.res_id += 1
                
        solution_list = []
        for rec in self.bestfitplane_points:
            solution_list.append( [ self.res_id, rec[0], rec[1], rec[2], self.bestfitplane._dipdir, self.bestfitplane._dipangle, str( description ) ])

        # if self.update_point_shape:          
        write_point_result( self.out_point_shapefile, self.out_point_shapelayer, solution_list )  
 
        self.stop_edit_pButton.setEnabled( True )
        
 
    def stop_editing( self ):
        
        try:
            self.out_point_shapefile.Destroy()
            QMessageBox.information( self, 
                                  self.tr("Results"), 
                                  self.tr("Results saved in shapefile.<br />Now you can load it" ) )            
            
        except:
            pass
           

    def open_html_help( self ):        

        webbrowser.open('{}/help/help.html'.format(os.path.dirname(__file__)), new = True )

        
        
class NewShapeFilesDialog( QDialog ):
    
    def __init__(self, parent=None):
        
        super( NewShapeFilesDialog, self ).__init__(parent)
    
        #self.pointCheckBox = QCheckBox( "&Point shapefile:" )
        self.output_point_shape_QLineEdit = QLineEdit()
        self.output_point_shape_browse_QPushButton = QPushButton(".....")
        self.output_point_shape_browse_QPushButton.clicked.connect( self.set_out_point_shapefile_name )
        
        """"
        self.polygonCheckBox = QCheckBox( "&Polygon shapefile:" )
        self.output_polygon_shape_QLineEdit = QLineEdit()
        self.output_polygon_shape_browse_QPushButton = QPushButton(".....")
        self.output_polygon_shape_browse_QPushButton.clicked.connect( self.set_out_polygon_shapefile_name )
        """
        
        okButton = QPushButton("&OK")
        cancelButton = QPushButton("Cancel")

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(okButton)
        buttonLayout.addWidget(cancelButton)
        
        layout = QGridLayout()
        #layout.addWidget(self.pointCheckBox, 0, 0, 1, 1 )
        layout.addWidget(self.output_point_shape_QLineEdit, 0, 1, 1, 1 ) 
        layout.addWidget(self.output_point_shape_browse_QPushButton, 0, 2, 1, 1 ) 
          
        """     
        layout.addWidget(self.polygonCheckBox, 1, 0)
        layout.addWidget(self.output_polygon_shape_QLineEdit, 1, 1, 1, 1 ) 
        layout.addWidget(self.output_polygon_shape_browse_QPushButton, 1, 2, 1, 1 ) 
        """
                
        layout.addLayout(buttonLayout, 2, 0, 1, 3)
        self.setLayout(layout)

        self.connect(okButton, SIGNAL("clicked()"),
                     self, SLOT("accept()"))
        self.connect(cancelButton, SIGNAL("clicked()"),
                     self, SLOT("reject()"))
        
        self.setWindowTitle("Create shapefile")
        
        
    def set_out_point_shapefile_name(self):
        
        out_shapefile_name = define_save_file_name( self, 
                                                    "Choose shapefile name", 
                                                    "*.shp", 
                                                    "shp (*.shp *.SHP)" )
        
        self.output_point_shape_QLineEdit.setText( out_shapefile_name )
        

    def set_out_polygon_shapefile_name(self):
        
        out_shapefile_name = define_save_file_name( self, 
                                                    "Choose shapefile name", 
                                                    "*.shp", 
                                                    "shp (*.shp *.SHP)" )
        
        self.output_polygon_shape_QLineEdit.setText( out_shapefile_name )


class PrevShapeFilesDialog( QDialog ):
    
    def __init__(self, parent=None):
        
        super( PrevShapeFilesDialog, self ).__init__(parent)
    
        # self.pointCheckBox = QCheckBox( "&Point shapefile:" )
        self.input_point_shape_QLineEdit = QLineEdit()
        self.input_point_shape_browse_QPushButton = QPushButton(".....")
        self.input_point_shape_browse_QPushButton.clicked.connect( self.set_in_point_shapefile_name )
        
        """
        self.polygonCheckBox = QCheckBox( "&Polygon shapefile:" )
        self.input_polygon_shape_QLineEdit = QLineEdit()
        self.input_polygon_shape_browse_QPushButton = QPushButton(".....")
        self.input_polygon_shape_browse_QPushButton.clicked.connect( self.set_in_polygon_shapefile_name )
        """
        
        okButton = QPushButton("&OK")
        cancelButton = QPushButton("Cancel")

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(okButton)
        buttonLayout.addWidget(cancelButton)
        
        layout = QGridLayout()
        #layout.addWidget(self.pointCheckBox, 0, 0, 1, 1 )
        layout.addWidget(self.input_point_shape_QLineEdit, 0, 1, 1, 1 ) 
        layout.addWidget(self.input_point_shape_browse_QPushButton, 0, 2, 1, 1 ) 
          
        """     
        layout.addWidget(self.polygonCheckBox, 1, 0)
        layout.addWidget(self.input_polygon_shape_QLineEdit, 1, 1, 1, 1 ) 
        layout.addWidget(self.input_polygon_shape_browse_QPushButton, 1, 2, 1, 1 ) 
        """
                
        layout.addLayout(buttonLayout, 2, 0, 1, 3)
        self.setLayout(layout)

        self.connect(okButton, SIGNAL("clicked()"),
                     self, SLOT("accept()"))
        self.connect(cancelButton, SIGNAL("clicked()"),
                     self, SLOT("reject()"))
        
        self.setWindowTitle("Get shapefile")
        
        
    def set_in_point_shapefile_name(self):
        
        in_shapefile_name = define_existing_file_name( self, 
                                                    "Choose shapefile name", 
                                                    "*.shp", 
                                                    "shp (*.shp *.SHP)" )
        
        self.input_point_shape_QLineEdit.setText( in_shapefile_name )
        

    def set_in_polygon_shapefile_name(self):
        
        in_shapefile_name = define_existing_file_name( self, 
                                                    "Choose shapefile name", 
                                                    "*.shp", 
                                                    "shp (*.shp *.SHP)" )
        
        self.input_polygon_shape_QLineEdit.setText( in_shapefile_name )
    

class SolutionDescriptDialog( QDialog ):
    
    def __init__(self, parent=None):
        
        super( SolutionDescriptDialog, self ).__init__(parent)

        layout = QVBoxLayout()
        
        descr_layout = QHBoxLayout()
        descr_layout.addWidget( QLabel("Description (max 50 char.)") )
        self.description_QLineEdit = QLineEdit()
        self.description_QLineEdit.setMaxLength(50)
        descr_layout.addWidget( self.description_QLineEdit )

        okButton = QPushButton("&OK")
        cancelButton = QPushButton("Cancel")

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(okButton)
        buttonLayout.addWidget(cancelButton)

        layout.addLayout( descr_layout )                
        layout.addLayout( buttonLayout )
        self.setLayout(layout)

        self.connect(okButton, SIGNAL("clicked()"),
                     self, SLOT("accept()"))
        self.connect(cancelButton, SIGNAL("clicked()"),
                     self, SLOT("reject()"))
        
        self.setWindowTitle("Solution")
        
        
        
                        
