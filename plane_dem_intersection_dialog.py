# -*- coding: utf-8 -*-

from math import sqrt, sin, cos, tan, atan, degrees, radians

import numpy as np

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *
    
from osgeo import ogr

from geosurf.geoio import read_dem
from geosurf.spatial import Point_2D, Segment_2D, Vector_2D, Point_3D, GeolPlane, versor_from_azimuth
from geosurf.intersections import Intersection_Parameters, Intersections

from geosurf.qgs_tools import loaded_raster_layers, project_qgs_point, \
     qgs_point
from geosurf.qgs_tools import PointMapToolEmitPoint


class plane_dem_intersection_QWidget( QWidget ):
    """
    Constructor
    
    """

    line_colors = [ "white", "red", "blue", "yellow", "orange", "brown",]
    dem_default_text = '--  required  --'


    def __init__( self, canvas, plugin ):

        super( plane_dem_intersection_QWidget, self ).__init__()       
        self.canvas, self.plugin = canvas, plugin        
        self.init_params()                 
        self.setup_gui() 

            
    def init_params(self):

        self.reset_values() 
        self.previousTool = None        
        self.grid = None
        self.input_points = None
        self.intersection_PointMapTool = None         
        self.intersection_markers_list = []

        
    def setup_gui( self ):

        dialog_layout = QVBoxLayout()
        main_widget = QTabWidget()        
        main_widget.addTab( self.setup_fplane_tab(), "Processing" )         
        main_widget.addTab( self.setup_about_tab(), "Help" )                             
        dialog_layout.addWidget( main_widget )                                     
        self.setLayout( dialog_layout )                    
        self.adjustSize()                       
        self.setWindowTitle( 'qgSurf - DEM-plane intersection' )        


    def setup_fplane_tab( self ):
        
        plansurfaceWidget = QWidget()  
        plansurfaceLayout = QVBoxLayout( )        
        plansurfaceLayout.addWidget( self.setup_source_dem() )         
        plansurfaceLayout.addWidget( self.setup_tabs() )                                       
        plansurfaceWidget.setLayout( plansurfaceLayout ) 
        return plansurfaceWidget 


    def setup_source_dem( self ):

        sourcedemWidget = QWidget()  
        sourcedemLayout = QGridLayout( )
        sourcedemLayout.addWidget(QLabel( "Source DEM" ), 0, 0, 1, 3)        
        self.raster_refreshlayers_pButton = QPushButton( "Get current raster layers" )
        self.raster_refreshlayers_pButton.clicked[bool].connect( self.refresh_raster_layer_list ) 
        self.raster_refreshlayers_pButton.setEnabled( True )       
        sourcedemLayout.addWidget( self.raster_refreshlayers_pButton, 1, 0, 1, 3 )                
        sourcedemLayout.addWidget(QLabel( "Use DEM" ), 2, 0, 1, 1)        
        self.dem_comboBox = QComboBox()
        self.dem_comboBox.addItem(self.dem_default_text)
        sourcedemLayout.addWidget(self.dem_comboBox, 2, 1, 1, 2)        
        sourcedemWidget.setLayout( sourcedemLayout )        
        return sourcedemWidget


    def setup_tabs( self ):  

        intersectionWidget = QWidget() 
        intersectionLayout = QVBoxLayout() 
        intersection_toolbox = QToolBox()
        intersection_toolbox.addItem ( self.setup_geographicdata_sect(), 'Geographic parameters' )
        intersection_toolbox.addItem ( self.setup_geologicdata_sect(), 'Geological parameters' )
        intersection_toolbox.addItem ( self.setup_output_sect(), 'Output' )             
        intersectionLayout.addWidget( intersection_toolbox )
        intersectionWidget.setLayout( intersectionLayout )        
        return intersectionWidget 
    

    def setup_about_tab( self ):
        
        helpWidget = QWidget()  
        helpLayout = QVBoxLayout( )        
        htmlText = """
This module allows to calculate the intersections of a plane with the DEM, given the plane attitude expressed according
to geological convention and a source point.

<h4>Loading of DEM data</h4>
<b>a)</b> Load in the QGis project the required DEM(s) layers and whatsoever vector or image layers needed for your analysis.
<br /><b>b)</b> Use "Get current raster layers" in qgSurf plugin: this will allow the plugin to know which raster layers are currently loaded.
<br /><b>c)</b> From the "Use DEM" combo box, choose the DEM to use.
 
<h4>Plane-DEM intersection</h4>
<b>d)</b> You have to define the source point in the map, with "Set source point in map" in the "Plane-DEM intersection" tab, "Geographic parameters" section. 
You can erase the current value with "Reset source point" or just define a new one by simply clicking in the map.
<br /><b>e)</b> In the X, Y and Z spinboxes, the coordinates of the source point are displayed. You can modify them from within the spinboxes.
You can also choose to use Z values not fixed to the DEM surfaces, by setting the 'lock z value to DEM surface' checkbox off.
<br /><b>f)</b> In the "Geological parameters" section, you can define the dip direction and the dip angle, and then calculate the
theoretical intersections by pressing "Calculate intersection".
<br /><b>g)</b> You can change the last intersection color by choosing a color from the "Intersection color" combo box, and delete all the intersections
with "Cancel intersections".
<br /><b>h)</b> In the "Output" section, you can save the last intersections as a point or line shapefile, also loading it 
within the current project.

<h4>Known limitations</h4>
- Rotation angles for input rasters (DEM) are not supported. Errors with DEM reading will be generated.
  
<h4>Known bugs</h4>
- Very large DEM could produce memory errors. Please resize your DEM to a smaller extent or resample it to a larger cell size.
<br />- If you try to define source points outside the DEM extent (for instance, because you have on-the-fly reprojection to a project CRS different from that of the DEM), 
a message warning can be repeated more that once.

        """
        
        helpQTextBrowser = QTextBrowser( helpWidget )        
        helpQTextBrowser.insertHtml( htmlText ) 
        helpLayout.addWidget( helpQTextBrowser )
        helpWidget.setLayout(helpLayout)                  
        return helpWidget 
        
                  
    def setup_geographicdata_sect( self ):        
        
        inputWidget = QWidget()  
        inputLayout = QGridLayout( )        
        self.intersection_definepoint_pButton = QPushButton( "Set source point in map" )
        self.intersection_definepoint_pButton.clicked[bool].connect( self.set_intersection_point )        
        inputLayout.addWidget( self.intersection_definepoint_pButton, 0, 0, 1, 3 )        

        self.intersection_resetsrcpt_pButton = QPushButton( "Reset source point" )
        self.intersection_resetsrcpt_pButton.clicked[bool].connect( self.reset_src_point )      
        inputLayout.addWidget( self.intersection_resetsrcpt_pButton, 1, 0, 1, 3 )        
                      
        inputLayout.addWidget( QLabel("X"), 2, 0, 1, 1 )
        self.Pt_x_QLineEdit = QLineEdit()
        self.Pt_x_QLineEdit.textEdited.connect( self.update_intersection_point_pos )
        inputLayout.addWidget( self.Pt_x_QLineEdit, 2, 1, 1, 2 )  
              
        inputLayout.addWidget( QLabel("Y"), 3, 0, 1, 1 )
        self.Pt_y_QLineEdit = QLineEdit()
        self.Pt_y_QLineEdit.textEdited.connect( self.update_intersection_point_pos )
        inputLayout.addWidget( self.Pt_y_QLineEdit, 3, 1, 1, 2 ) 
                      
        inputLayout.addWidget( QLabel("Z"), 4, 0, 1, 1 )
        self.Pt_z_QLineEdit = QLineEdit()
        self.Pt_z_QLineEdit.textEdited.connect( self.check_z_congruence_with_dem )
        inputLayout.addWidget( self.Pt_z_QLineEdit, 4, 1, 1, 2 ) 
               
        self.fixz2dem_checkBox = QCheckBox("lock z value to DEM surface")
        self.fixz2dem_checkBox.setChecked(True)
        self.fixz2dem_checkBox.stateChanged[int].connect( self.update_z_value )
        inputLayout.addWidget( self.fixz2dem_checkBox, 5, 0, 1, 3 )        
        
        self.reset_input()
        
        inputWidget.setLayout(inputLayout) 
        
        return inputWidget


    def update_crs_settings( self ):

        self.on_the_fly_projection = True if self.canvas.hasCrsTransformEnabled() else False
        if self.on_the_fly_projection: 
            self.projectCrs = self.canvas.mapRenderer().destinationCrs()
        else:
            self.projectCrs = None       
 
       
    def reset_values(self):

        self.current_z_value = None
        self.intersection_z_from_dem = False
        self.reset_srcpt()
        self.reset_results()
        
 
    def reset_srcpt(self):        

        self.intersection_srcpt_x = None
        self.intersection_srcpt_y = None        
        self.intersection_sourcepoint_marker = None
                
        
    def reset_results(self):

        self.intersections_x = []
        self.intersections_y = []
        self.intersections_xprt = {}        
        self.inters = None
       

    def check_z_congruence_with_dem( self ):
        
        if self.intersection_z_from_dem and float( self.Pt_z_QLineEdit.text() ) != self.current_z_value:
            self.intersection_z_from_dem = False
            self.fixz2dem_checkBox.setChecked( False )
            
        self.current_z_value = float( self.Pt_z_QLineEdit.text() )


    def reset_src_point( self ):
        
        self.intersection_resetsrcpt_pButton.setEnabled( False )
        self.reset_srcpoint_QLineEdit()                           
        self.reset_markers()
        self.reset_values() 
                                   
                    
    def setup_geologicdata_sect( self ):

        planeorientationWidget = QWidget()  
        planeorientationLayout = QGridLayout( )
        
        dip_dir_label = QLabel("Dip direction")
        dip_dir_label.setAlignment ( Qt.AlignCenter )       
        planeorientationLayout.addWidget( dip_dir_label, 0, 0, 1, 2 )

        dip_ang_label = QLabel("Dip angle")
        dip_ang_label.setAlignment( Qt.AlignCenter )       
        planeorientationLayout.addWidget( dip_ang_label, 0, 2, 1, 1 )
        
        self.DDirection_dial = QDial()
        self.DDirection_dial.setRange( 0, 360 )
        self.DDirection_dial.setPageStep( 1 )
        self.DDirection_dial.setProperty( "value", 180 )
        self.DDirection_dial.setSliderPosition( 180 )
        self.DDirection_dial.setTracking( True )
        self.DDirection_dial.setOrientation(Qt.Vertical)
        self.DDirection_dial.setWrapping(True)
        self.DDirection_dial.setNotchTarget(30.0)
        self.DDirection_dial.setNotchesVisible(True)   
        self.DDirection_dial.valueChanged[int].connect( self.update_dipdir_spinbox )    
        planeorientationLayout.addWidget( self.DDirection_dial, 1, 0, 1, 2 )        
                
        self.DAngle_verticalSlider = QSlider()
        self.DAngle_verticalSlider.setRange(0,90)
        self.DAngle_verticalSlider.setProperty("value", 45)
        self.DAngle_verticalSlider.setOrientation(Qt.Vertical)
        self.DAngle_verticalSlider.setInvertedAppearance(True)
        self.DAngle_verticalSlider.setTickPosition(QSlider.TicksBelow)
        self.DAngle_verticalSlider.setTickInterval(15)
        self.DAngle_verticalSlider.valueChanged[int].connect( self.update_dipang_spinbox )
        planeorientationLayout.addWidget( self.DAngle_verticalSlider, 1, 2, 1, 1 )

        self.DDirection_spinBox = QSpinBox()
        self.DDirection_spinBox.setRange(0,360)
        self.DDirection_spinBox.setSingleStep(1)
        self.DDirection_spinBox.valueChanged[int].connect( self.update_dipdir_slider )
        planeorientationLayout.addWidget( self.DDirection_spinBox, 2, 0, 1, 2 )        
         
        self.DAngle_spinBox = QSpinBox()
        self.DAngle_spinBox.setRange(0,90)
        self.DAngle_spinBox.setSingleStep(1)
        self.DAngle_spinBox.setProperty("value", 45) 
        self.DAngle_spinBox.valueChanged[int].connect( self.update_dipang_slider )
        planeorientationLayout.addWidget( self.DAngle_spinBox, 2, 2, 1, 1 )
 
        self.Intersection_calculate_pushButton = QPushButton( "Calculate intersection" )
        self.Intersection_calculate_pushButton.clicked[bool].connect( self.calculate_intersection )
        planeorientationLayout.addWidget( self.Intersection_calculate_pushButton, 3, 0, 1, 3 )
        
        planeorientationLayout.addWidget( QLabel("Intersection color"), 4, 0, 1, 1 )
        
        self.Intersection_color_comboBox = QComboBox()
        self.Intersection_color_comboBox.insertItems( 0, ["blue", "white", "red", "yellow", "orange", "brown", "green", "pink", "darkblue", "gray"] )

        self.Intersection_color_comboBox.currentIndexChanged[int].connect( self.plot_intersections )
                                                                  
        planeorientationLayout.addWidget( self.Intersection_color_comboBox, 4, 1, 1, 2 )                                                             
         
        self.Intersection_cancel_pushButton = QPushButton( "Cancel intersections" )
        self.Intersection_cancel_pushButton.clicked.connect( self.reset_intersections )
        planeorientationLayout.addWidget( self.Intersection_cancel_pushButton, 5, 0, 1, 3 )  
                                      
        planeorientationWidget.setLayout(planeorientationLayout)              

        return planeorientationWidget
    
        
    def setup_output_sect( self ):

        outputWidget = QWidget()  
        outputLayout = QGridLayout( )

        outputLayout.addWidget( QLabel( self.tr( "Save results in")), 0, 0, 1, 1 )
        
        self.Output_FileName_Input = QLineEdit()
        outputLayout.addWidget( self.Output_FileName_Input, 0, 1, 1, 2 )

        self.Output_Browse = QPushButton(".....")
        self.Output_Browse.clicked.connect( self.selectOutputVectorFile )
        outputLayout.addWidget( self.Output_Browse, 0, 3, 1, 1 ) 

        outputLayout.addWidget( QLabel( self.tr( "with geometry:")), 1, 0, 1, 1 )
                               
        saveGroup = QButtonGroup( outputWidget )
        
        self.Save_points_rButt = QRadioButton("points")
        self.Save_points_rButt.setChecked(True)
        saveGroup.addButton(self.Save_points_rButt, 0)
        outputLayout.addWidget( self.Save_points_rButt, 1, 1, 1, 1 )
        
        self.Save_lines_rButt = QRadioButton("lines")
        saveGroup.addButton(self.Save_lines_rButt, 1)
        outputLayout.addWidget( self.Save_lines_rButt, 1, 2, 1, 1 )        
                
        self.Load_output_checkBox = QCheckBox("load output in project")
        outputLayout.addWidget( self.Load_output_checkBox, 2, 0, 1, 2 )  
                       
        self.Save_pushButton = QPushButton("Save last intersections")
        self.Save_pushButton.clicked.connect( self.write_results )
        outputLayout.addWidget( self.Save_pushButton, 3, 0, 1, 4 )
                
        outputWidget.setLayout(outputLayout)              

        return outputWidget

                
    def set_intersection_point(self):
        
        try:
            self.intersection_PointMapTool.canvasClicked.disconnect( self.update_intersection_point_pos )
        except:
            pass            
         
        self.update_crs_settings()
                       
        self.intersection_PointMapTool = PointMapToolEmitPoint( self.canvas, self.plugin ) # mouse listener
        self.previousTool = self.canvas.mapTool() # save the standard map tool for restoring it at the end
        self.intersection_PointMapTool.canvasClicked.connect( self.update_intersection_point_pos )
        self.intersection_PointMapTool.setCursor( Qt.CrossCursor )                
        self.canvas.setMapTool( self.intersection_PointMapTool )

                
    def reset_all( self ):

        self.reset_markers() 
        self.reset_input()
        self.reset_values()


    def reset_input(self):

        self.disable_tools()
        self.reset_srcpoint_QLineEdit()        
        

    def disable_tools(self):
        
        self.intersection_definepoint_pButton.setEnabled( False )
        self.intersection_resetsrcpt_pButton.setEnabled( False )
        
        try: 
            self.intersection_PointMapTool.canvasClicked.disconnect( self.update_intersection_point_pos )
        except: 
            pass
        
        try: 
            self.disable_MapTool( self.intersection_PointMapTool )
        except: 
            pass
                        
                
    def reset_markers(self):       
        
        self.reset_intersections()
        self.remove_srcpt_marker_from_canvas()
          
        
    def reset_intersections(self):
        
        self.remove_markers_from_canvas()
        self.intersection_markers_list = []
        self.reset_results()        


    def remove_markers_from_canvas( self ):

        for mrk in self.intersection_markers_list:
            self.canvas.scene().removeItem( mrk ) 


    def remove_srcpt_marker_from_canvas(self):
        
        if self.intersection_sourcepoint_marker is not None:
            self.canvas.scene().removeItem( self.intersection_sourcepoint_marker )
        

    def refresh_raster_layer_list( self ):

        self.dem, self.grid = None, None        
        try: 
            self.dem_comboBox.currentIndexChanged[int].disconnect( self.get_dem )
        except: 
            pass                
        self.reset_all()                   
        self.rasterLayers = loaded_raster_layers()                 
        if self.rasterLayers is None or len( self.rasterLayers ) == 0:
            QMessageBox.critical( self, "Source DEMs", "No raster layer found in current project" )
            return
        self.dem_comboBox.clear()
        self.dem_comboBox.addItem( self.dem_default_text )
        for layer in self.rasterLayers: 
            self.dem_comboBox.addItem( layer.name() )            
        self.dem_comboBox.currentIndexChanged[int].connect( self.get_dem )                
        QMessageBox.information( self, "Source DEMs", "Found %d raster layers. Select one in 'Use DEM'.\n\nWarnings\nthe source DEM must have the elevations measured in same unit as the horizontal ones of the current project CRS (i.e., do not mix elevations in feet and horizontal distances in meters). Otherwise, results will be wrong." % len( self.rasterLayers ))

              
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
    
        self.intersection_definepoint_pButton.setEnabled( True )
        self.intersection_resetsrcpt_pButton.setEnabled( True )
        

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

                   
    def update_intersection_point_pos( self, qgs_point = None, button = None ): # Add point to analyze

        if self.grid is None:
            QMessageBox.critical(self, "Intersection source point", "Source DEM is not defined") 
            return

        self.intersection_resetsrcpt_pButton.setEnabled( True )
               
        if self.sender() == self.intersection_PointMapTool:
            
            self.intersection_srcpt_x = qgs_point.x()
            self.intersection_srcpt_y = qgs_point.y()
            self.Pt_x_QLineEdit.setText( str( self.intersection_srcpt_x ) )
            self.Pt_y_QLineEdit.setText( str( self.intersection_srcpt_y ) )
            
        elif self.sender() == self.Pt_x_QLineEdit:
            
            if self.Pt_x_QLineEdit.text() == '':
                QMessageBox.critical(self, "qgSurf", "Error: x value is not defined") 
                return
            try:
                self.intersection_srcpt_x = float( self.Pt_x_QLineEdit.text() )
            except:
                QMessageBox.critical( self, "qgSurf", "Error: x value is not correctly defined")
                return 
                                   
        elif self.sender() == self.Pt_y_QLineEdit:
            
            if self.Pt_y_QLineEdit.text() == '':
                QMessageBox.critical(self, "qgSurf", "Error: y value is not defined") 
                return  
            try:
                self.intersection_srcpt_y = float( self.Pt_y_QLineEdit.text() )
            except:
                QMessageBox.critical( self, "qgSurf", "Error: y value is not correctly defined")
                return            
        
        z_value_from_dem = self.update_z_value()
        if z_value_from_dem is None: 
            self.current_z_value = None
            self.Pt_z_QLineEdit.setText( "" )
        else:
            self.current_z_value = z_value_from_dem 
            self.Pt_z_QLineEdit.setText( str( self.current_z_value ) )
            self.intersection_z_from_dem = True
                           
        self.remove_markers_from_canvas(); self.remove_srcpt_marker_from_canvas()        
        self.intersection_sourcepoint_marker = self.create_marker( self.canvas, 
                                                                   self.intersection_srcpt_x, self.intersection_srcpt_y, 
                                                                   icon_type = 1, 
                                                                   icon_color = QColor( str( self.Intersection_color_comboBox.currentText() ) ) )        
        self.canvas.refresh()


    def update_z_value (self):
        """
        Update z value.
        
        """         
        
        # to prevent action when the DEM is not set              
        if self.grid is None: 
            return None 
               
        if not self.fixz2dem_checkBox.isChecked(): 
            return None

        if self.on_the_fly_projection:         
            dem_crs_source_pt_x, dem_crs_source_pt_y = self.get_dem_crs_coords( self.intersection_srcpt_x, self.intersection_srcpt_y )        
        else:
            dem_crs_source_pt_x, dem_crs_source_pt_y = self.intersection_srcpt_x, self.intersection_srcpt_y      
         
        if not self.coords_within_dem_bndr( dem_crs_source_pt_x, dem_crs_source_pt_y): 
            QMessageBox.critical( self, "Intersection source point", 
                                 "Defined point is outside source DEM extent" )                 
            return None
        
        currArrCoord = self.grid.geog2array_coord( Point_2D( dem_crs_source_pt_x, dem_crs_source_pt_y ) )        
        z = self.grid.interpolate_bilinear(currArrCoord)         
        if z is None: 
            return None
        
        return z
        

    def disable_MapTool( self, mapTool ):
                            
        try:
            if mapTool is not None: self.canvas.unsetMapTool( mapTool )
        except:
            pass                            

        try:
            if self.previousTool is not None: self.canvas.setMapTool( self.previousTool )
        except:
            pass

         
    def reset_srcpoint_QLineEdit(self):
        
        for qlineedit in ( self.Pt_x_QLineEdit, self.Pt_y_QLineEdit, self.Pt_z_QLineEdit ):
            qlineedit.clear()

        
    def update_dipdir_slider(self):
        """
        Update the value of the dip direction in the slider.""
        """        
        transformed_dipdirection = self.DDirection_spinBox.value() + 180.0
        if transformed_dipdirection > 360.0: transformed_dipdirection -= 360.0            
        self.DDirection_dial.setValue( transformed_dipdirection ) 
  
           
    def update_dipdir_spinbox(self):            
        """
        Update the value of the dip direction in the spinbox.
        """        
        real_dipdirection = self.DDirection_dial.value() - 180.0
        if real_dipdirection < 0.0: real_dipdirection += 360.0            
        self.DDirection_spinBox.setValue( real_dipdirection ) 

                 
    def update_dipang_slider(self):
        """
        Update the value of the dip angle in the slider.
        """
        
        self.DAngle_verticalSlider.setValue( self.DAngle_spinBox.value() )    
 
                  
    def update_dipang_spinbox(self):            
        """
        Update the value of the dip angle in the spinbox.
        """        
        
        self.DAngle_spinBox.setValue( self.DAngle_verticalSlider.value() ) 


    def project_coords( self, x, y, source_crs, dest_crs ):
        
        if self.on_the_fly_projection and source_crs != dest_crs:
            dest_crs_qgs_pt = project_qgs_point( qgs_point( x, y ), source_crs, dest_crs )
            return  dest_crs_qgs_pt.x(), dest_crs_qgs_pt.y() 
        else:
            return  x, y        
       

    def get_dem_crs_coords( self, x, y ):
    
        return self.project_coords( x, y, self.projectCrs, self.dem.crs() )


    def get_prj_crs_coords( self, x, y ):

        return self.project_coords( x, y, self.dem.crs(), self.projectCrs )
        
                               
    def calculate_intersection( self ):
        """
        Calculate intersection points.
        """

        # check if all input data are correct
        if self.grid is None:
            QMessageBox.information( self, "qgSurf", "Please first define a source DEM")
            return
                
        if self.Pt_x_QLineEdit.text() == '' or self.Pt_y_QLineEdit.text() == '' or self.Pt_z_QLineEdit.text() == '':
            QMessageBox.information( self, "qgSurf", "Define the location of the source point in 'Geographic parameters' section")
            return
        
        try:
            z = float( self.Pt_z_QLineEdit.text() )
        except:
            QMessageBox.information( self, "qgSurf", "z value is not correctly defined" )
            return
        
        # source point position in DEM CRS
        prj_crs_source_pt_x, prj_crs_source_pt_y = self.intersection_srcpt_x, self.intersection_srcpt_y
        if self.on_the_fly_projection:       
            dem_crs_source_pt_x, dem_crs_source_pt_y = self.get_dem_crs_coords( prj_crs_source_pt_x, prj_crs_source_pt_y ) 
        else:
            dem_crs_source_pt_x, dem_crs_source_pt_y = prj_crs_source_pt_x, prj_crs_source_pt_y
        dem_crs_source_point = Point_3D( dem_crs_source_pt_x, dem_crs_source_pt_y, z )

        # geoplane attitude in DEM CRS
        src_dip_direction, src_dip_angle = self.DDirection_spinBox.value(), self.DAngle_verticalSlider.value()
        if self.on_the_fly_projection:       
            corr_dip_direction, corr_dip_angle = self.get_corrected_plane_attitude( src_dip_direction, src_dip_angle ) 
        else:
            corr_dip_direction, corr_dip_angle = src_dip_direction, src_dip_angle      
        
        self.srcPlaneAttitude = GeolPlane( corr_dip_direction, corr_dip_angle )

        # intersection arrays       

        self.inters = Intersections() 
        self.inters.xcoords_x, self.inters.xcoords_y, \
        self.inters.ycoords_x, self.inters.ycoords_y = self.grid.intersection_with_surface('plane', dem_crs_source_point, self.srcPlaneAttitude )            
        self.inters.parameters = Intersection_Parameters(self.grid._sourcename, dem_crs_source_point, self.srcPlaneAttitude)
        self.intersections_x = list( self.inters.xcoords_x[ np.logical_not(np.isnan(self.inters.xcoords_x)) ] ) + \
                               list( self.inters.ycoords_x[ np.logical_not(np.isnan(self.inters.ycoords_y)) ] )    
        self.intersections_y = list( self.inters.xcoords_y[ np.logical_not(np.isnan(self.inters.xcoords_x)) ] ) + \
                               list( self.inters.ycoords_y[ np.logical_not(np.isnan(self.inters.ycoords_y)) ] )                          
        intersection_data = dict( x = self.intersections_x, y = self.intersections_y )          
        intersection_plane = dict( dipdir = self.inters.parameters._srcPlaneAttitude._dipdir, dipangle = self.inters.parameters._srcPlaneAttitude._dipangle )        
        intersection_point = dict( x = self.inters.parameters._srcPt._x, y = self.inters.parameters._srcPt._y, z = self.inters.parameters._srcPt._z )
        self.intersections_xprt = dict( data = intersection_data, plane = intersection_plane, point = intersection_point)

        self.plot_intersections()
        

    def get_directional_distorsion_length( self, direction_azim, s_x_dir, s_y_dir ):
        
        x = s_x_dir * cos( radians( direction_azim ) )
        y = s_y_dir * sin( radians( direction_azim ) )
        
        return sqrt( x*x + y*y )
        
        
    def get_corrected_plane_attitude( self, src_dip_direction, src_dip_angle ):
        
        # 1 - DEM center in DEM CRS
        dem_center_pt2d_dem_crs = self.grid.domain.g_horiz_center()

        # 2 - dummy distance displacement in DEM CRS
        dummy_factor = 100.0
        dem_crs_displacement_distance = self.grid.domain.g_min_size() / dummy_factor
 
        # 3 - displacement vectors in x and y dirs of DEM CRS
        dem_crs_displacement_vector_x_dir = Vector_2D( dem_crs_displacement_distance, 0 )
        dem_crs_displacement_vector_y_dir = Vector_2D( 0, dem_crs_displacement_distance )
        
        # 4 - displaced pts in x & y dirs of DEM CRS
        dem_displaced_pt2d_dem_crs_x_dir = dem_center_pt2d_dem_crs.displaced_by_vector( dem_crs_displacement_vector_x_dir )
        dem_displaced_pt2d_dem_crs_y_dir = dem_center_pt2d_dem_crs.displaced_by_vector( dem_crs_displacement_vector_y_dir ) 

        # 5 - DEM center in project CRS
        prj_crs_center_pt_x, prj_crs_center_pt_y = self.get_prj_crs_coords( dem_center_pt2d_dem_crs._x, dem_center_pt2d_dem_crs._y )

        # 6 - displaced pt coords in x' and y' dirs of Proj CRS
        prj_crs_displaced_pt2d_x_dir_x, prj_crs_displaced_pt2d_x_dir_y = self.get_prj_crs_coords( dem_displaced_pt2d_dem_crs_x_dir._x, dem_displaced_pt2d_dem_crs_x_dir._y )
        prj_crs_displaced_pt2d_y_dir_x, prj_crs_displaced_pt2d_y_dir_y = self.get_prj_crs_coords( dem_displaced_pt2d_dem_crs_y_dir._x, dem_displaced_pt2d_dem_crs_y_dir._y )
        
        # 7 - displacement distances in x' and y' dirs of Proj CRS
        prj_crs_displacement_distance_x_dir = Point_2D( prj_crs_center_pt_x, prj_crs_center_pt_y ).distance( Point_2D( prj_crs_displaced_pt2d_x_dir_x, prj_crs_displaced_pt2d_x_dir_y ))         
        prj_crs_displacement_distance_y_dir = Point_2D( prj_crs_center_pt_x, prj_crs_center_pt_y ).distance( Point_2D( prj_crs_displaced_pt2d_y_dir_x, prj_crs_displaced_pt2d_y_dir_y ))      
             
        # 8 - point displaced from DEM center along RHR strike by given amount, in project CRS
        rhr_strike = src_dip_direction - 90.0
        if rhr_strike < 0.0:
            rhr_strike += 360.0
        prj_crs_displacement_versor = versor_from_azimuth( rhr_strike )
        prj_crs_displacement_vector = prj_crs_displacement_versor.scale( prj_crs_displacement_distance_x_dir )
        prj_crs_distanced_pt2d = Point_2D( prj_crs_center_pt_x, prj_crs_center_pt_y ).displaced_by_vector(prj_crs_displacement_vector)
        
        # 9 - point displaced from DEM center along RHR strike, in DEM CRS
        dem_crs_distanced_pt_x, dem_crs_distanced_pt_y = self.get_dem_crs_coords( prj_crs_distanced_pt2d._x, prj_crs_distanced_pt2d._y )
        distanced_pt2d_dem_crs = Point_2D( dem_crs_distanced_pt_x, dem_crs_distanced_pt_y )
        
        # 10 - azimuth of segment joining DEM center with displaced point, in DEM CRS
        corr_rhr_strike = Segment_2D( dem_center_pt2d_dem_crs, distanced_pt2d_dem_crs ).azimuth_degr()
        corr_dip_direction = corr_rhr_strike + 90.0
        if corr_dip_direction > 360.0:
            corr_dip_direction -= 360.0

        ## part for dip angle correction
        direction_azim = 90.0 - corr_dip_direction

        distorsion_lenght = self.get_directional_distorsion_length( direction_azim, prj_crs_displacement_distance_x_dir, prj_crs_displacement_distance_y_dir )
        distorsion_ratio = distorsion_lenght / dem_crs_displacement_distance
        
        corr_dip_angle_degr = degrees( atan( distorsion_ratio * tan( radians( src_dip_angle ) ) ) )
   
        return corr_dip_direction, corr_dip_angle_degr

                
    def plot_intersections(self):
        
        try:
            if self.intersections_x is None or len( self.intersections_x ) == 0 or \
               self.intersections_y is None or len( self.intersections_y ) == 0:
                return
        except:
            return
        
        current_markers_list = []
        for dem_crs_x, dem_crs_y in zip( self.intersections_x, self.intersections_y ):
            if self.on_the_fly_projection:
                prj_crs_x, prj_crs_y = self.get_prj_crs_coords( dem_crs_x, dem_crs_y )
            else:
                prj_crs_x, prj_crs_y = dem_crs_x, dem_crs_y           
            marker = self.create_marker( self.canvas, prj_crs_x, prj_crs_y, pen_width= 1, icon_type = 1, icon_size = 8, 
                                         icon_color = QColor( str( self.Intersection_color_comboBox.currentText() ) ) )
            current_markers_list.append(marker)        
        self.intersection_markers_list += current_markers_list   
        self.canvas.refresh()


    def selectOutputVectorFile( self ):
            
        output_filename = QFileDialog.getSaveFileName(self, 
                                                      self.tr( "Save shapefile" ), 
                                                      "*.shp", 
                                                      "shp (*.shp *.SHP)" )        
        if not output_filename: 
            return        
        self.Output_FileName_Input.setText( output_filename ) 
                      
                
    def write_results( self ):
        """
        Write intersection results in the output shapefile.
        """
 
        # check for result existence
        
        if self.inters is None:
            QMessageBox.critical(self, "Save results", "No results available") 
            return            
            
        self.output_filename = str( self.Output_FileName_Input.text() ) 
        if self.output_filename == '':
            QMessageBox.critical( self, "Save results", "No output file defined" ) 
            return
                           
        # set output type
        if self.Save_points_rButt.isChecked(): self.result_geometry = 'points'
        else: self.result_geometry = 'lines'        
        
        # creation of output shapefile
        shape_driver = ogr.GetDriverByName( "ESRI Shapefile" )              
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
        self.plane_z = self.srcPlaneAttitude.plane_from_geo( sourcePoint )  
              
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
        if self.result_geometry == 'points': self.write_intersections_as_points()
        else: self.write_intersections_as_lines()
        QMessageBox.information(self, "Result", "Saved to shapefile: %s" % self.output_filename)

        # add theme to QGis project
        if self.Load_output_checkBox.isChecked():
            try:
                intersection_layer = QgsVectorLayer(self.output_filename, QFileInfo(self.output_filename).baseName(), "ogr")                    
                QgsMapLayerRegistry.instance().addMapLayer( intersection_layer )
            except:            
                QMessageBox.critical( self, "Result", "Unable to load layer in project" )
                return
                         
        
    def write_intersections_as_points( self ):
        """
        Write intersection results in the output shapefile.
        """
                                
        x_filtered_coord_x = self.inters.xcoords_x[ np.logical_not(np.isnan(self.inters.xcoords_x)) ] 
        x_filtered_coord_y = self.inters.xcoords_y[ np.logical_not(np.isnan(self.inters.xcoords_x)) ]            
        x_filtered_coord_z = self.plane_z( x_filtered_coord_x, x_filtered_coord_y )

        y_filtered_coord_x = self.inters.ycoords_x[ np.logical_not(np.isnan(self.inters.ycoords_y)) ] 
        y_filtered_coord_y = self.inters.ycoords_y[ np.logical_not(np.isnan(self.inters.ycoords_y)) ]             
        y_filtered_coord_z = self.plane_z( y_filtered_coord_x, y_filtered_coord_y )        
        
        intersections_x = list( x_filtered_coord_x ) + list( y_filtered_coord_x )    
        intersections_y = list( x_filtered_coord_y ) + list( y_filtered_coord_y )                                           
        intersections_z = list( x_filtered_coord_z ) + list( y_filtered_coord_z )       
         
        curr_Pt_id = 0   
        for curr_Pt in zip(intersections_x, intersections_y, intersections_z):            
            curr_Pt_id += 1
            if self.on_the_fly_projection:            
                prj_crs_x, prj_crs_y = self.get_prj_crs_coords( float(curr_Pt[0]), float(curr_Pt[1]) )
            else:
                prj_crs_x, prj_crs_y = float(curr_Pt[0]), float(curr_Pt[1])
            
            # pre-processing for new feature in output layer
            curr_Pt_geom = ogr.Geometry(ogr.wkbPoint)
            curr_Pt_geom.AddPoint( prj_crs_x, prj_crs_y, float(curr_Pt[2]) )
                
            # create a new feature
            curr_Pt_shape = ogr.Feature( self.outshape_featdef )
            curr_Pt_shape.SetGeometry( curr_Pt_geom )
            curr_Pt_shape.SetField( 'id', curr_Pt_id )
                                    
            curr_Pt_shape.SetField( 'x', prj_crs_x )
            curr_Pt_shape.SetField( 'y', prj_crs_y ) 
            curr_Pt_shape.SetField( 'z', curr_Pt[2] ) 

            if self.on_the_fly_projection:
                prj_crs_src_pt_x, prj_crs_src_pt_y = self.get_prj_crs_coords( self.intersections_xprt['point']['x'], self.intersections_xprt['point']['y'] )            
            else:
                prj_crs_src_pt_x, prj_crs_src_pt_y = self.intersections_xprt['point']['x'], self.intersections_xprt['point']['y']
                
            curr_Pt_shape.SetField('srcPt_x', prj_crs_src_pt_x)
            curr_Pt_shape.SetField('srcPt_y', prj_crs_src_pt_y) 
            curr_Pt_shape.SetField('srcPt_z', self.intersections_xprt['point']['z'])

            curr_Pt_shape.SetField('dip_dir', self.srcPlaneAttitude._dipdir)
            curr_Pt_shape.SetField('dip_ang', self.srcPlaneAttitude._dipangle)             

            # add the feature to the output layer
            self.out_layer.CreateFeature(curr_Pt_shape)            
            
            # destroy no longer used objects
            curr_Pt_geom.Destroy(); curr_Pt_shape.Destroy()
                            
        # destroy output geometry
        self.out_shape.Destroy() 


    def write_intersections_as_lines( self ):
        """
        Write intersection results in a line shapefile.
        """
                
        # create dictionary of cell with intersection points        
        self.inters.links = self.inters.get_intersections()
        self.inters.neighbours = self.inters.set_neighbours( ) 
        self.inters.define_paths( )  
        
        # networks of connected intersections
        self.inters.networks = self.inters.define_networks()   
        
        for curr_path_id, curr_path_points in self.inters.networks.iteritems():                                    
            line = ogr.Geometry( ogr.wkbLineString )            
            for curr_point_id in curr_path_points:                            
                curr_intersection = self.inters.links[ curr_point_id-1 ]                           
                i, j, direct = curr_intersection['i'], curr_intersection['j'], curr_intersection['pi_dir']                
                if direct == 'x': dem_crs_x, dem_crs_y = self.inters.xcoords_x[ i, j ], self.inters.xcoords_y[ i, j ]
                if direct == 'y': dem_crs_x, dem_crs_y = self.inters.ycoords_x[ i, j ], self.inters.ycoords_y[ i, j ]                                        
                z = self.plane_z( dem_crs_x, dem_crs_y )
                if self.on_the_fly_projection: 
                    prj_crs_x, prj_crs_y = self.get_prj_crs_coords( dem_crs_x, dem_crs_y )
                else:
                    prj_crs_x, prj_crs_y = dem_crs_x, dem_crs_y                
                line.AddPoint( prj_crs_x, prj_crs_y, z )            
                                       
            # create a new feature
            line_shape = ogr.Feature( self.outshape_featdef )
            line_shape.SetGeometry( line )   

            line_shape.SetField( 'id', curr_path_id )
            
            if self.on_the_fly_projection:
                prj_crs_src_pt_x, prj_crs_src_pt_y = self.get_prj_crs_coords( self.intersections_xprt['point']['x'], self.intersections_xprt['point']['y'] )            
            else:
                prj_crs_src_pt_x, prj_crs_src_pt_y = self.intersections_xprt['point']['x'], self.intersections_xprt['point']['y']            
                
            line_shape.SetField( 'srcPt_x', prj_crs_src_pt_x )
            line_shape.SetField( 'srcPt_y', prj_crs_src_pt_y ) 
            line_shape.SetField( 'srcPt_z', self.intersections_xprt['point']['z'] )
    
            line_shape.SetField( 'dip_dir', self.srcPlaneAttitude._dipdir )
            line_shape.SetField( 'dip_ang', self.srcPlaneAttitude._dipangle )             
    
            # add the feature to the output layer
            self.out_layer.CreateFeature( line_shape )            
            
            # destroy no longer used objects
            line.Destroy()
            line_shape.Destroy()
                            
        # destroy output geometry
        self.out_shape.Destroy() 
        
    
        
          
            
            



