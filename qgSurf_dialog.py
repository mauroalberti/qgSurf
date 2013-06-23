# -*- coding: utf-8 -*-

import os
from math import floor
import numpy as np

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

from qgs_tools.ptmaptool import PointMapTool
    
try:
    from osgeo import ogr
except: 
    import ogr

from geosurf.geoio import read_dem
from geosurf.spatial import Point, Vector
from geosurf.struct_geol import StructPlane
from geosurf.intersections import Intersection_Parameters, Intersections
from geosurf.svd import xyz_svd 

        
class qgSurfDialog( QDialog ):
    """
    Constructor
    
    """

    line_colors = [ "white", "red", "blue", "yellow", "orange", "brown",]


    def __init__( self, canvas, plugin ):

        super( qgSurfDialog, self ).__init__() 

        QObject.connect( self, 
                         SIGNAL( " rejected ( ) " ), 
                         self.onPluginClose )
        
        self.canvas = canvas
        self.plugin = plugin   
            
        self.initialize_parameters()                 
        self.setup_commandwin_gui() 
                
        self.setWindowFlags( Qt.WindowStaysOnTopHint )


    def set_bestfitplane_points(self):

        try:
            QObject.disconnect( self.bestfitplane_PointMapTool, 
                 SIGNAL("leftClicked"), 
                 self.set_bestfitplane_points_from_map )
        except:
            pass
                    
        self.bestfitplane_reset_point_values()  
              
        self.bestfitplane_PointMapTool = PointMapTool( self.canvas, self.plugin ) # mouse listener
        self.previousTool = self.canvas.mapTool() # save the standard map tool for restoring it at the end
        QObject.connect( self.bestfitplane_PointMapTool, 
                         SIGNAL("leftClicked"), 
                         self.set_bestfitplane_points_from_map )
        self.bestfitplane_PointMapTool.setCursor( Qt.CrossCursor )        
        self.canvas.setMapTool( self.bestfitplane_PointMapTool )

                
    def set_intersection_point(self):
        
        try:
            QObject.disconnect( self.intersection_PointMapTool, 
                             SIGNAL("leftClicked"), 
                             self.update_intersection_point_pos )
        except:
            pass            
                
        self.intersection_PointMapTool = PointMapTool( self.canvas, self.plugin ) # mouse listener
        self.previousTool = self.canvas.mapTool() # save the standard map tool for restoring it at the end
        QObject.connect( self.intersection_PointMapTool, 
                         SIGNAL("leftClicked"), 
                         self.update_intersection_point_pos )
        self.intersection_PointMapTool.setCursor( Qt.CrossCursor )
                
        self.canvas.setMapTool( self.intersection_PointMapTool )


    def remove_markers_from_canvas ( self, marker_list ):
        
        if marker_list is not None and len( marker_list ) > 0:
            for mrk in marker_list:
                self.canvas.scene().removeItem( mrk )         


    def bestfitplane_reset_all(self):
        
        self.bestfitplane_reset_point_values()        
        self.bestfitplane_disable_tools()


    def bestfitplane_reset_point_values(self):

        self.bestfitplane_reset_point_inputs()  
        self.bestfitplane_reset_point_markers()


    def bestfitplane_reset_point_inputs( self ):

        self.bestfitplane_src_points_ListWdgt.clear()
        self.bestfitplane_points = []  
        
        
    def bestfitplane_reset_point_markers( self ):

        self.remove_markers_from_canvas( self.bestfitplane_point_markers ) 
        self.bestfitplane_point_markers = []          


    def bestfitplane_disable_tools( self ):

        self.bestfitplane_definepoints_pButton.setEnabled( False )
        self.bestfitplane_calculate_pButton.setEnabled( False )
        """
        self.bestfitplane_saveresults_pButton.setEnabled( False )  
        """ 
        try:
            QObject.disconnect( self.bestfitplane_PointMapTool, 
                                SIGNAL("leftClicked"), 
                                self.set_bestfitplane_points_from_map )
        except:
            pass
        try:
            self.disable_MapTool( self.bestfitplane_PointMapTool )
        except:
            pass         
        
                
    def intersection_reset_all( self ):
        
        self.intersection_reset_init_values()
        self.intersection_reset_input()
        self.intersection_reset_all_markers()
        
        
    def intersection_reset_init_values(self):

        self.current_z_value = None
        self.intersection_z_from_dem = False
        self.intersections = False
        self.intersection_srcpt_x = None
        self.intersection_srcpt_y = None
        self.intersections_x = None
        self.intersections_y = None
        

    def intersection_reset_input(self):

        self.intersection_disable_tools()
        self.intersection_reset_srcpoint_SpinBoxes()        
        

    def intersection_disable_tools(self):
        
        self.intersection_definepoint_pButton.setEnabled( False )
        self.intersection_resetsrcpt_pButton.setEnabled( False )
        try:
            QObject.disconnect( self.intersection_PointMapTool, 
                             SIGNAL("leftClicked"), 
                             self.update_intersection_point_pos )
        except:
            pass
        try:
            self.disable_MapTool( self.intersection_PointMapTool )
        except:
            pass                
                
    def intersection_reset_all_markers(self):       
        
        self.remove_markers_from_canvas( self.intersection_markers_list )
        self.intersection_reset_srcpoint_marker()
          
        
    def intersection_reset_inters_markers(self):
        
        self.remove_markers_from_canvas( self.intersection_markers_list )


    def intersection_reset_srcpoint_marker(self):
        
        if self.intersection_sourcepoint_marker is not None:
            self.canvas.scene().removeItem( self.intersection_sourcepoint_marker )

              
    def initialize_parameters(self):

        self.intersection_reset_init_values()        
        
        self.dem_default_text = '--  required  --'                    
        self.previousTool = None        
        self.source_dem = self.input_points = None
        self.bestfitplane_point_markers = []
        self.intersection_PointMapTool = None
        self.intersection_sourcepoint_marker = None 
        self.intersection_markers_list = []

  
    def get_layers_from_qgis(self):        

        curr_map_layers = QgsMapLayerRegistry.instance().mapLayers()
        mapLayers = zip(unicode(curr_map_layers.keys()), curr_map_layers.values())       
        rasterLayers = filter( lambda layer: layer[1].type() == QgsMapLayer.RasterLayer, mapLayers )
        vectorLayers = filter( lambda layer: layer[1].type() == QgsMapLayer.VectorLayer, mapLayers )
        pointvectLayers = filter( lambda layer: layer[1].geometryType() == QGis.Point, vectorLayers )
        return rasterLayers, pointvectLayers
             

    def setup_commandwin_gui( self ):

        dialog_layout = QVBoxLayout()
        main_widget = QTabWidget()
        
        main_widget.addTab( self.setup_processing_tab(), 
                            "Processing" )                    
        main_widget.addTab( self.setup_help_tab(), 
                            "Help" ) 
        main_widget.addTab( self.setup_about_tab(), 
                            "About" )
                            
        dialog_layout.addWidget( main_widget )                                     
        self.setLayout( dialog_layout )                    
        self.adjustSize()                       
        self.setWindowTitle( 'qgSurf' )   


    def setup_processing_tab( self ):
        
        processingWidget = QWidget()  
        processingLayout = QVBoxLayout( )
        
        processingLayout.addWidget( self.setup_source_dem() ) 
        
        processingLayout.addWidget( self.setup_processing_subtabs() )
                                       
        processingWidget.setLayout(processingLayout)  
                
        return processingWidget 


    def setup_source_dem( self ):

        sourcedemWidget = QWidget()  
        sourcedemLayout = QGridLayout( )

        sourcedemLayout.addWidget(QLabel( "Source DEM" ), 0, 0, 1, 3)
        
        self.raster_refreshlayers_pButton = QPushButton( "Get current raster layers" )
        QObject.connect( self.raster_refreshlayers_pButton, 
                         SIGNAL( " clicked( bool ) " ), 
                         self.refresh_raster_layer_list ) 
        self.raster_refreshlayers_pButton.setEnabled( True )       
        sourcedemLayout.addWidget( self.raster_refreshlayers_pButton, 1, 0, 1, 3 )
                
        sourcedemLayout.addWidget(QLabel( "Use DEM" ), 2, 0, 1, 1)        
        self.dem_comboBox = QComboBox()
        self.dem_comboBox.addItem(self.dem_default_text)
        
        """""
        QObject.connect( self.dem_comboBox, 
                         SIGNAL( " currentIndexChanged (int) " ), 
                         self.get_dem )
        """""
        sourcedemLayout.addWidget(self.dem_comboBox, 2, 1, 1, 2)
        
        sourcedemWidget.setLayout( sourcedemLayout )
        
        return sourcedemWidget
      
      
    def setup_processing_subtabs(self):  

        processingsTabWidget = QTabWidget()

        processingsTabWidget.addTab( self.setup_bestfitplane_calc_tab(), 
                                 "Best-fit-plane calculation" )         
        processingsTabWidget.addTab( self.setup_intersection_tab(), 
                                 "Plane-DEM intersection" ) 

        return processingsTabWidget


    def setup_intersection_tab( self ):  

        intersectionWidget = QWidget() 
        intersectionLayout = QVBoxLayout()
 
        intersection_toolbox = QToolBox()

        intersection_toolbox.addItem ( self.setup_geographicdata_sect(), 
                                       'Geographic parameters' )
        intersection_toolbox.addItem ( self.setup_geologicdata_sect(), 
                                       'Geological parameters' )
        intersection_toolbox.addItem ( self.setup_output_sect(), 
                                       'Output' )

        # widget final setup                
        intersectionLayout.addWidget( intersection_toolbox )
        intersectionWidget.setLayout( intersectionLayout )
        
        return intersectionWidget 
 

    def setup_help_tab( self ):
        
        helpWidget = QWidget()  
        helpLayout = QVBoxLayout( )
        
        htmlText = """
        <h3>Help</h3>
This plugin allows to calculate the best-fit plane give a DEM and a set of points, or alternatively, given a geological plane, a DEM and a point, 
to calculate the intersections of the plane with the DEM.
<h4>Known limitations</h4>
- This plugin does not handle on-the-fly reprojection. So if you need to use it, make sure that you set the 
project projection to be the same as that of the DEM
<br />- Rotation angles for input rasters (DEM) is not supported. Errors could be silent, so please check this detail with QGis or other tools.
  
<h4>Known bugs</h4>
- Very large DEM can originate memory errors. Please resize your DEM to a smaller extent or resample it to a larger cell size.
<br />- If you try to define source points outside DEM extent (for instance, because you have on-the-fly reprojection to a project CRS different from that of the DEM), 
a message warning can be repeated more that once.

<h4>Loading of DEM data</h4>
<br /><b>a)</b> Load in the QGis project the required DEM(s) layers and whatsoever vector or image layers needed for your analysis
<br /><b>b)</b> Use "Get current raster layers" in qgSurf plugin: this will allow the plugin to know which raster layers are currently loaded
<br /><b>c)</b> From the "Use DEM" combo box, choose the required DEM and make sure that the QGis project and the DEM have the same projection

<h4>Best-fit plane calculation</h4>
The basis of the algorithm is the application of singular value decomposition to derive the eigenvectors of a set of measures. 
<br />The best-fit plane processing sequence is:
<br /><b>d)</b> from the "Best-fit-plane calculation", press "Define points in map": this will allow you to define in the canvas at least three, 
and possibly more points, whose coordinates will be listed in the plugin widget.
<br /><b>e)</b> with at least three points defined, you can calculate the best-fit plane by pressing "Calculate best-fit-plane": a message box will report the dip direction and dip angle of the calculated plane
<br /><b>f)</b> you can add even more points and again calculate the best-fit plane; otherwise, 
if you want to start a new analysis on the same DEM, go to <b>e)</b>, or if you want to use another DEM, 
go to <b>c)</b> if it is already loaded in the project, or load it in the project and then go to <b>b)</b>
 
<h4>Plane-DEM intersection</h4>
<b>g)</b> You have to define the source point in the map, with "Set source point in map" in the "Plane-DEM intersection" tab, "Geographic parameters" section. 
You can erase it with "Reset source point" or put a new one by simply clicking in the map
<br /><b>h)</b> In the X, Y and Z spinboxes, you will see the coordinates of the source point. You can modify them within the spinboxes themselves.
You can also use Z values not fixed to the DEM surfaces.
<br /><b>i)</b> In the "Geological parameters" section, you can set the dip direction and the dip angle, and then calculate the
theoretical intersections by pressing "Calculate intersection".
<br /><b>j)</b> You can change the last intersection color by choosing a color from the "Intersection color" combo box, and delete all the intersections
with "Cancel intersections"
<br /><b>k)</b> In the "Output" section, you can save the last intersections as a point or line shapefile, also loading it 
within the current project
        """
        
        helpQTextBrowser = QTextBrowser( helpWidget )        
        helpQTextBrowser.insertHtml( htmlText ) 
        helpLayout.addWidget( helpQTextBrowser )
        helpWidget.setLayout(helpLayout)  
                
        return helpWidget 
        
        
    def setup_about_tab( self ):
        
        aboutWidget = QWidget()  
        aboutLayout = QVBoxLayout( )
        
        htmlText = """
        <h3>qgSurf release 0.2.1 (2013-06-23)</h3>
        Created by M. Alberti (www.malg.eu).
        <br /><br />Plugin for the processing geological planes and topography.  
        <br /><br />Licensed under the terms of GNU GPL 3.
        """
        
        aboutQTextBrowser = QTextBrowser( aboutWidget )        
        aboutQTextBrowser.insertHtml( htmlText ) 
        aboutLayout.addWidget( aboutQTextBrowser )  
        aboutWidget.setLayout(aboutLayout)
        
        return aboutWidget              

               
    def setup_geographicdata_sect( self ):        
        
        inputWidget = QWidget()  
        inputLayout = QGridLayout( )
                
        #inputLayout.addWidget( QLabel( "Source point" ), 0, 0, 1, 1) 
        
        self.intersection_definepoint_pButton = QPushButton( "Set source point in map" )
        QObject.connect( self.intersection_definepoint_pButton, 
                         SIGNAL( " clicked( bool ) " ), 
                         self.set_intersection_point ) 
        #self.intersection_definepoint_pButton.setEnabled( False )       
        inputLayout.addWidget( self.intersection_definepoint_pButton, 0, 0, 1, 3 )        

        self.intersection_resetsrcpt_pButton = QPushButton( "Reset source point" )
        QObject.connect( self.intersection_resetsrcpt_pButton, 
                         SIGNAL( " clicked( bool ) " ), 
                         self.intersection_reset_src_point ) 
        #self.intersection_resetsrcpt_pButton.setEnabled( False )       
        inputLayout.addWidget( self.intersection_resetsrcpt_pButton, 1, 0, 1, 3 )        

         
        #inputLayout.setRowStretch ( 0, 4 )
                      
        inputLayout.addWidget( QLabel("X"), 2, 0, 1, 1 )
        self.Pt_x_spinBox = QSpinBox()
        self.Pt_x_spinBox.setRange(-1000000000, 1000000000)
        self.Pt_x_spinBox.setSingleStep(50)
        QObject.connect( self.Pt_x_spinBox, 
                         SIGNAL( " valueChanged (int) " ), 
                         self.update_intersection_point_pos )
        inputLayout.addWidget( self.Pt_x_spinBox, 2, 1, 1, 2 )  
              
        inputLayout.addWidget( QLabel("Y"), 3, 0, 1, 1 )
        self.Pt_y_spinBox = QSpinBox()
        self.Pt_y_spinBox.setRange(-1000000000, 1000000000)
        self.Pt_y_spinBox.setSingleStep(50)
        QObject.connect( self.Pt_y_spinBox, 
                         SIGNAL( " valueChanged (int) " ), 
                         self.update_intersection_point_pos )
        inputLayout.addWidget( self.Pt_y_spinBox, 3, 1, 1, 2 ) 
                      
        inputLayout.addWidget( QLabel("Z"), 4, 0, 1, 1 )
        self.Pt_z_spinBox = QSpinBox()
        self.Pt_z_spinBox.setRange(-10000000, 10000000)
        self.Pt_z_spinBox.setSingleStep(5)
        QObject.connect( self.Pt_z_spinBox, 
                         SIGNAL( " valueChanged (int) " ), 
                         self.check_z_congruence_with_dem )
        inputLayout.addWidget( self.Pt_z_spinBox, 4, 1, 1, 2 ) 
               
        self.fixz2dem_checkBox = QCheckBox("fix z value to DEM")
        self.fixz2dem_checkBox.setChecked(True)
        QObject.connect( self.fixz2dem_checkBox, 
                         SIGNAL( " stateChanged (int) " ), 
                         self.intersection_set_z_from_dem )
        inputLayout.addWidget( self.fixz2dem_checkBox, 5, 0, 1, 3 )        
        
        self.intersection_reset_input()
        
        inputWidget.setLayout(inputLayout) 
        
        return inputWidget


    def check_z_congruence_with_dem( self ):
        
        if self.intersection_z_from_dem and \
           self.Pt_z_spinBox.value() != self.current_z_value:
            self.intersection_z_from_dem = False
            self.fixz2dem_checkBox.setChecked( False )
        self.current_z_value = self.Pt_z_spinBox.value()


    def intersection_reset_src_point( self ):
                    
        self.intersection_reset_init_values()
        
        self.intersection_resetsrcpt_pButton.setEnabled( False )
        self.intersection_reset_srcpoint_SpinBoxes()  
                           
        self.intersection_reset_all_markers()
                            
                    
    def setup_geologicdata_sect( self ):

        planeorientationWidget = QWidget()  
        planeorientationLayout = QGridLayout( )
        
        dip_dir_label = QLabel("Dip direction")
        dip_dir_label.setAlignment ( Qt.AlignCenter )       
        planeorientationLayout.addWidget( dip_dir_label, 0, 0, 1, 2 )

        dip_ang_label = QLabel("Dip angle")
        dip_ang_label.setAlignment ( Qt.AlignCenter )       
        planeorientationLayout.addWidget( dip_ang_label, 0, 2, 1, 1 )
        
        self.DDirection_dial = QDial()
        self.DDirection_dial.setRange(0,360)
        self.DDirection_dial.setPageStep(1)
        self.DDirection_dial.setProperty("value", 180)
        self.DDirection_dial.setSliderPosition(180)
        self.DDirection_dial.setTracking(True)
        self.DDirection_dial.setOrientation(Qt.Vertical)
        self.DDirection_dial.setWrapping(True)
        self.DDirection_dial.setNotchTarget(30.0)
        self.DDirection_dial.setNotchesVisible(True)   
        QObject.connect( self.DDirection_dial, 
                         SIGNAL( " valueChanged (int) " ), 
                         self.update_dipdir_spinbox )    
        planeorientationLayout.addWidget( self.DDirection_dial, 1, 0, 1, 2 )        
                
        self.DAngle_verticalSlider = QSlider()
        self.DAngle_verticalSlider.setRange(0,90)
        self.DAngle_verticalSlider.setProperty("value", 45)
        self.DAngle_verticalSlider.setOrientation(Qt.Vertical)
        self.DAngle_verticalSlider.setInvertedAppearance(True)
        self.DAngle_verticalSlider.setTickPosition(QSlider.TicksBelow)
        self.DAngle_verticalSlider.setTickInterval(15)
        QObject.connect( self.DAngle_verticalSlider, 
                         SIGNAL( " valueChanged (int) " ), 
                         self.update_dipang_spinbox )
        planeorientationLayout.addWidget( self.DAngle_verticalSlider, 1, 2, 1, 1 )

        self.DDirection_spinBox = QSpinBox()
        self.DDirection_spinBox.setRange(0,360)
        self.DDirection_spinBox.setSingleStep(1)
        QObject.connect( self.DDirection_spinBox, 
                         SIGNAL( " valueChanged (int) " ), 
                         self.update_dipdir_slider )
        planeorientationLayout.addWidget( self.DDirection_spinBox, 2, 0, 1, 2 )        
         
        self.DAngle_spinBox = QSpinBox()
        self.DAngle_spinBox.setRange(0,90)
        self.DAngle_spinBox.setSingleStep(1)
        self.DAngle_spinBox.setProperty("value", 45) 
        QObject.connect( self.DAngle_spinBox, 
                         SIGNAL( " valueChanged (int) " ), 
                         self.update_dipang_slider )
        planeorientationLayout.addWidget( self.DAngle_spinBox, 2, 2, 1, 1 )
 
        self.Intersection_calculate_pushButton = QPushButton( "Calculate intersection" )
        QObject.connect( self.Intersection_calculate_pushButton, 
                         SIGNAL( " clicked( bool ) " ), 
                         self.calculate_intersection )
        planeorientationLayout.addWidget( self.Intersection_calculate_pushButton, 3, 0, 1, 3 )
        
        planeorientationLayout.addWidget( QLabel("Intersection color"), 4, 0, 1, 1 )
        
        self.Intersection_color_comboBox = QComboBox()
        self.Intersection_color_comboBox.insertItems( 0, ["blue",
                                                          "white",                                                          
                                                          "red",
                                                          "yellow",
                                                          "orange",
                                                          "brown",
                                                          "green",
                                                          "pink",
                                                          "darkblue",
                                                          "gray"] )

        QObject.connect( self.Intersection_color_comboBox, 
                         SIGNAL( " currentIndexChanged (int) " ), 
                         self.plot_intersections )
                                                                  
        planeorientationLayout.addWidget( self.Intersection_color_comboBox, 4, 1, 1, 2 )                                                             
         
        self.Intersection_cancel_pushButton = QPushButton( "Cancel intersections" )
        QObject.connect( self.Intersection_cancel_pushButton, 
                         SIGNAL( " clicked( bool ) " ), 
                         self.intersection_reset_inters_markers )
        planeorientationLayout.addWidget( self.Intersection_cancel_pushButton, 5, 0, 1, 3 )  
                                      
        planeorientationWidget.setLayout(planeorientationLayout)              

        return planeorientationWidget
    
        
    def setup_output_sect( self ):

        outputWidget = QWidget()  
        outputLayout = QGridLayout( )
               
        self.Save_pushButton = QPushButton("Save last intersections")
        QObject.connect( self.Save_pushButton, 
                         SIGNAL( " clicked() " ), 
                         self.write_results )
        outputLayout.addWidget( self.Save_pushButton, 0, 0, 1, 2 )
        
        self.Output_FileName_Input = QLineEdit()
        outputLayout.addWidget( self.Output_FileName_Input, 1, 0, 1, 1 )

        self.Output_Browse = QPushButton(".....")
        QObject.connect( self.Output_Browse, 
                         SIGNAL( "clicked()" ), 
                         self.selectOutputVectorFile )
        outputLayout.addWidget( self.Output_Browse, 1, 1, 1, 1 )        

        saveGroup = QButtonGroup( outputWidget )

        self.Save_points_rButt = QRadioButton("points")
        self.Save_points_rButt.setChecked(True)
        saveGroup.addButton(self.Save_points_rButt, 0)
        outputLayout.addWidget( self.Save_points_rButt, 2, 0, 1, 1 )
        
        self.Save_lines_rButt = QRadioButton("lines")
        saveGroup.addButton(self.Save_lines_rButt, 1)
        outputLayout.addWidget( self.Save_lines_rButt, 2, 1, 1, 1 )        
                
        self.Load_output_checkBox = QCheckBox("load output in project")
        outputLayout.addWidget( self.Load_output_checkBox, 3, 0, 1, 2 )
                
        outputWidget.setLayout(outputLayout)              

        return outputWidget


    def setup_bestfitplane_calc_tab( self ):        
        
        planecalcWidget = QWidget()  
        planecalcLayout = QGridLayout( )        

        planecalcLayout.addWidget(QLabel( "Source points" ), 2, 0, 1, 2)
        self.bestfitplane_definepoints_pButton = QPushButton( "Define points in map" )
        QObject.connect( self.bestfitplane_definepoints_pButton, 
                         SIGNAL( " clicked( bool ) " ), 
                         self.set_bestfitplane_points )
        self.bestfitplane_definepoints_pButton.setEnabled( False )
        planecalcLayout.addWidget( self.bestfitplane_definepoints_pButton, 3, 0, 1, 2 )
        
        self.bestfitplane_src_points_ListWdgt = QListWidget()
        planecalcLayout.addWidget( self.bestfitplane_src_points_ListWdgt, 4, 0, 1, 2 )
        
        self.bestfitplane_calculate_pButton = QPushButton( "Calculate best-fit-plane" )
        QObject.connect( self.bestfitplane_calculate_pButton, 
                         SIGNAL( " clicked( bool ) " ), 
                         self.calculate_bestfitplane )
        self.bestfitplane_calculate_pButton.setEnabled( False )
        planecalcLayout.addWidget( self.bestfitplane_calculate_pButton, 5, 0, 1, 2 )               

        """
        self.bestfitplane_saveresults_pButton = QPushButton( "Save results" )
        QObject.connect( self.bestfitplane_saveresults_pButton, 
                         SIGNAL( " clicked( bool ) " ), 
                         self.save_bestfitplane_results )
        self.bestfitplane_saveresults_pButton.setEnabled( False )
        planecalcLayout.addWidget( self.bestfitplane_saveresults_pButton, 6, 0, 1, 2 )               
        """
        
        planecalcWidget.setLayout(planecalcLayout)
        
        return planecalcWidget            


    def refresh_raster_layer_list( self ):

        self.source_dem = None

        try:
            QObject.disconnect( self.dem_comboBox, 
                                SIGNAL( " currentIndexChanged (int) " ), 
                                self.get_dem )
        except:
            pass
                
        self.intersection_reset_all()
        self.bestfitplane_reset_all()

        #self.remove_markers_from_canvas( self.intersection_markers_list )
        #self.intersection_reset_srcpoint_marker()
                    
        self.rasterLayers, _ = self.get_layers_from_qgis()                
        if self.rasterLayers is None or len( self.rasterLayers ) == 0:
            QMessageBox.critical( self, "Source DEMs", "No raster layer found in current project" )
            return

        self.dem_comboBox.clear()
        self.dem_comboBox.addItem( self.dem_default_text )
        for ( _,layer ) in self.rasterLayers:
            self.dem_comboBox.addItem( layer.name() )
            
        QObject.connect( self.dem_comboBox, 
                 SIGNAL( " currentIndexChanged (int) " ), 
                 self.get_dem )
                
        QMessageBox.information( self, 
                                 "Source DEMs", 
                                 "Found %d raster layers. Select one in 'Use DEM' (below)" % len( self.rasterLayers ))

              
    def get_dem( self, ndx_DEM_file = 0 ): 
        
        self.source_dem = None
        
        self.intersection_reset_all()
        self.bestfitplane_reset_all()
        
        if self.rasterLayers is None or len( self.rasterLayers ) == 0:
            return
                                
        # no DEM layer defined  
        if ndx_DEM_file == 0:  
            return
        
        dem_name = self.rasterLayers[ndx_DEM_file-1][1].source()          
        try:
            self.source_dem = read_dem( dem_name )               
        except:
            QMessageBox.critical( self, "DEM", "Unable to read file" )
            return
        
        if self.source_dem is None: 
            QMessageBox.critical( self, "DEM", "DEM was not read" )
            return
 
        QMessageBox.information( self, "On-the-fly projection warning", "Be sure that current DEM and project use same projection" )
                   
        self.intersection_definepoint_pButton.setEnabled( True )
        self.intersection_resetsrcpt_pButton.setEnabled( True )
        self.bestfitplane_definepoints_pButton.setEnabled( True )
        

    def set_bestfitplane_points_from_map( self, position ): # Add point to analyze
        
        mapPos = self.canvas.getCoordinateTransform().toMapCoordinates( position["x"], position["y"] )
        if mapPos.x() <= self.source_dem.xmin or mapPos.x() >= self.source_dem.xmax or \
           mapPos.y() <= self.source_dem.ymin or mapPos.y() >= self.source_dem.ymax:
            return        
        
        marker = QgsVertexMarker( self.canvas )
        marker.setIconType( 2 )
        marker.setIconSize( 18 )
        marker.setPenWidth( 2 )
        marker.setColor( QColor( 'limegreen' ) )
        marker.setCenter(QgsPoint( mapPos.x(), mapPos.y() ))        
        self.bestfitplane_point_markers.append( marker )        
        self.canvas.refresh()
        
        self.add_bestfitplane_point( mapPos.x(), mapPos.y() )  
        
        
    def add_bestfitplane_point( self, x, y ):
       
        curr_point = Point( x, y )
        currArrCoord = self.source_dem.geog2array_coord(curr_point)        
        z = floor(self.source_dem.interpolate_bilinear(currArrCoord)) 
        
        self.bestfitplane_points.append( [x, y, z] )        
        self.bestfitplane_src_points_ListWdgt.addItem( "%.3f %.3f %.3f" % (x, y, z) )
        
        if self.bestfitplane_src_points_ListWdgt.count () >= 3:
            self.bestfitplane_calculate_pButton.setEnabled( True )

     
    def calculate_bestfitplane(self):        

        xyz_list = self.bestfitplane_points
        
        xyz_array = np.array( xyz_list, dtype=np.float64)
        self.xyz_mean = np.mean( xyz_array, axis=0 )

        svd = xyz_svd( xyz_array-self.xyz_mean )
        if svd['result'] == None:
            QMessageBox.critical( self, 
                                  "Best fit plane", 
                                  "Unable to calculate result")
            return        

        _, _, eigenvectors = svd['result']   
                           
        lowest_eigenvector = eigenvectors[ -1, : ]  # Solution is last row
        normal = lowest_eigenvector[ : 3 ] / np.linalg.norm( lowest_eigenvector[ : 3 ] )
        
        normal_vector = Vector( normal[0], normal[1], normal[2])
        normal_axis = normal_vector.to_axis()
        self.bestfitplane = normal_axis.to_normal_structplane()
        
        QMessageBox.information( self, "Best fit geological plane", 
                                 "Dip direction: %.1f - dip angle: %.1f" %( self.bestfitplane._dipdir, self.bestfitplane._dipangle ))


        """
        self.bestfitplane_saveresults_pButton.setEnabled( True )
        """
                   
    def update_intersection_point_pos( self, position = None ): # Add point to analyze

        if self.source_dem is None:
            QMessageBox.critical(self, 
                                 "Intersection source point", 
                                 "Source DEM is not defined") 
            return

        self.intersection_resetsrcpt_pButton.setEnabled( True )
                
        if self.sender() == self.intersection_PointMapTool:
            mapPos = self.canvas.getCoordinateTransform().toMapCoordinates( position["x"], position["y"] )
            self.Pt_x_spinBox.setValue( int( mapPos.x() ) )
            self.Pt_y_spinBox.setValue( int( mapPos.y() ) )
        elif self.sender() == self.Pt_x_spinBox or \
             self.sender() == self.Pt_y_spinBox:        
            if self.Pt_x_spinBox.text() == '' or self.Pt_y_spinBox.text() == '':
                return            
            if self.sender() == self.Pt_x_spinBox and self.intersection_srcpt_x == self.Pt_x_spinBox.value():                    
                return
            if self.sender() == self.Pt_y_spinBox and self.intersection_srcpt_y == self.Pt_y_spinBox.value():
                return

        self.intersection_srcpt_x = self.Pt_x_spinBox.value()
        self.intersection_srcpt_y = self.Pt_y_spinBox.value()
        self.intersection_set_z_from_dem()
        
        self.remove_markers_from_canvas( self.intersection_markers_list )
        self.intersection_reset_srcpoint_marker()                        
        self.intersection_sourcepoint_marker = QgsVertexMarker( self.canvas )
        self.intersection_sourcepoint_marker.setIconType( 1 )
        self.intersection_sourcepoint_marker.setIconSize( 18 )
        self.intersection_sourcepoint_marker.setPenWidth( 2 ) 
        self.intersection_sourcepoint_marker.setCenter(QgsPoint( self.intersection_srcpt_x, 
                                                                 self.intersection_srcpt_y ))
        self.canvas.refresh()


    def intersection_set_z_from_dem (self):
        """
        Update z value.
        
        """         
                
        if self.source_dem is None: return
        
        if self.fixz2dem_checkBox.isChecked():    

            curr_x = self.Pt_x_spinBox.value()
            curr_y = self.Pt_y_spinBox.value()
            
            if curr_x <= self.source_dem.xmin or curr_x >= self.source_dem.xmax or \
               curr_y <= self.source_dem.ymin or curr_y >= self.source_dem.ymax:
                QMessageBox.critical(self, 
                                     "Intersection source point", 
                                     "Defined point is outside source DEM extent")                 
                return
           
            curr_point = Point( curr_x, curr_y )
            currArrCoord = self.source_dem.geog2array_coord(curr_point)
            
            z = floor(self.source_dem.interpolate_bilinear(currArrCoord)) 
            
            if z is not None:
                self.current_z_value = int( z )           
                self.Pt_z_spinBox.setValue( self.current_z_value )
                self.intersection_z_from_dem = True  
        
        
    def disable_bestfitplane_points_definition(self):
        
        self.bestfitplane_definepoints_pButton.setEnabled( False )

        self.disable_bestfitplane_points_MapTool()
        for marker in self.bestfitplane_point_markers:        
            self.canvas.scene().removeItem( marker )
        self.bestfitplane_point_markers = []
        self.bestfitplane_src_points_ListWdgt.clear()
        
           
    def disable_MapTool( self, mapTool ):
                            
        try:
            if mapTool is not None:                   
                self.canvas.unsetMapTool( mapTool )
        except:
            pass                            

        try:
            if self.previousTool is not None:                            
                self.canvas.setMapTool( self.previousTool )
        except:
            pass


    def disable_bestfitplane_points_MapTool( self ):
        
        self.disable_MapTool( self.bestfitplane_PointMapTool )
        
              
    def intersection_reset_srcpoint_SpinBoxes(self):
        
        self.Pt_x_spinBox.clear()
        self.Pt_y_spinBox.clear()
        self.Pt_z_spinBox.clear()
        
        
    def update_dipdir_slider(self):
        """
        Update the value of the dip direction in the slider.""
        """
        
        real_dipdirection = self.DDirection_spinBox.value()
        transformed_dipdirection = real_dipdirection + 180.0
        if transformed_dipdirection > 360.0:
            transformed_dipdirection = transformed_dipdirection - 360            
        self.DDirection_dial.setValue( transformed_dipdirection ) 
  
           
    def update_dipdir_spinbox(self):            
        """
        Update the value of the dip direction in the spinbox.
        """        
        transformed_dipdirection = self.DDirection_dial.value()
        real_dipdirection = transformed_dipdirection - 180.0
        if real_dipdirection < 0.0:
            real_dipdirection = real_dipdirection + 360.0
            
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
        
                       
    def calculate_intersection( self ):
        """
        Calculate intersection points.
        """
        
        # self.intersection_reset_all_markers()
        # self.remove_markers_from_canvas( self.intersection_markers_list )
        
        if self.source_dem is None:
            QMessageBox.information( self, 
                                     "Intersection calculation", 
                                     "Please first select a DEM")
            return

                
        if self.Pt_x_spinBox.text() == '' or \
           self.Pt_y_spinBox.text() == '' or \
           self.Pt_z_spinBox.text() == '':
            QMessageBox.information( self, 
                                     "Intersection calculation", 
                                     "Define the location of the source point in 'Geographic parameters' section")
            return
                                                          
        sourcePoint = Point(self.Pt_x_spinBox.value(), 
                           self.Pt_y_spinBox.value(), 
                           self.Pt_z_spinBox.value())

        srcDipDir = self.DDirection_spinBox.value()
        srcDipAngle = self.DAngle_verticalSlider.value()

        self.srcPlaneAttitude = StructPlane( srcDipDir, srcDipAngle )

        # intersection arrays
        
        self.inters = Intersections()
        
        intersection_results = self.source_dem.intersection_with_surface('plane', 
                                                                         sourcePoint,  
                                                                         self.srcPlaneAttitude )
        
        self.inters.xcoords_x = intersection_results[0]
        self.inters.xcoords_y = intersection_results[1]
        self.inters.ycoords_x = intersection_results[2]
        self.inters.ycoords_y = intersection_results[3]
            
        self.inters.parameters = Intersection_Parameters(self.source_dem._sourcename, sourcePoint, self.srcPlaneAttitude)


        self.intersections_x = list( self.inters.xcoords_x[ np.logical_not(np.isnan(self.inters.xcoords_x)) ] ) + \
                          list( self.inters.ycoords_x[ np.logical_not(np.isnan(self.inters.ycoords_y)) ] )
    
        self.intersections_y = list( self.inters.xcoords_y[ np.logical_not(np.isnan(self.inters.xcoords_x)) ] ) + \
                          list( self.inters.ycoords_y[ np.logical_not(np.isnan(self.inters.ycoords_y)) ] )
                          
        intersection_data = dict( x=self.intersections_x, y=self.intersections_y ) 
         
        intersection_plane = dict( dipdir=self.inters.parameters._srcPlaneAttitude._dipdir, 
                                   dipangle= self.inters.parameters._srcPlaneAttitude._dipangle )
        
        intersection_point = dict( x=self.inters.parameters._srcPt.x, 
                                   y=self.inters.parameters._srcPt.y, 
                                   z=self.inters.parameters._srcPt.z )

        self.intersections = dict(data=intersection_data,
                                  plane=intersection_plane,
                                  point=intersection_point)

        self.plot_intersections()
        
        
    def plot_intersections(self):
        
        try:
            if self.intersections_x is None or len( self.intersections_x ) == 0 or \
               self.intersections_y is None or len( self.intersections_y ) == 0:
                return
        except:
            return
        
        current_markers_list = []
        for x, y in zip( self.intersections_x, self.intersections_y ): 
            marker = QgsVertexMarker( self.canvas )
            marker.setIconType( 1 )
            marker.setColor( QColor( str( self.Intersection_color_comboBox.currentText() ) ) )
            marker.setIconSize( 8 )
            marker.setPenWidth( 1 )
            marker.setCenter( QgsPoint( x, y) )
            current_markers_list.append(marker)
        
        self.intersection_markers_list += current_markers_list   
        self.canvas.refresh()


    def selectOutputVectorFile( self ):
            
        output_filename = QFileDialog.getSaveFileName(self, 
                                                      self.tr( "Save shapefile" ), 
                                                      "*.shp", 
                                                      "shp (*.shp *.SHP)" )        
        if output_filename.isEmpty():
            return
        self.Output_FileName_Input.setText( output_filename ) 
                
        
    def write_results( self ):
        """
        Write intersection results in the output shapefile.
        """
 
        # check for result existence
        try:        
            if self.inters.xcoords_x == [] and \
               self.inters.xcoords_y == [] and \
               self.inters.ycoords_x == [] and \
               self.inters.ycoords_y == [] :
                QMessageBox.critical(self, 
                                     "Save results", 
                                     "No results available") 
                return
        except:
                QMessageBox.critical(self, 
                                     "Save results", 
                                     "No results available") 
                return
            
        self.output_filename = str( self.Output_FileName_Input.text() ) 
        if self.output_filename == '':
            QMessageBox.critical(self, 
                                 "Save results", 
                                 "No output file defined") 
            return
                           
        # set output type
        if self.Save_points_rButt.isChecked():
            self.result_geometry = 'points'
        else:
            self.result_geometry = 'lines'        
        
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
        if self.result_geometry == 'points':
            self.write_intersections_as_points()
        else:
            self.write_intersections_as_lines() 

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
            
            # pre-processing for new feature in output layer
            curr_Pt_geom = ogr.Geometry(ogr.wkbPoint)
            curr_Pt_geom.AddPoint(float(curr_Pt[0]), float(curr_Pt[1]), float(curr_Pt[2]))
                
            # create a new feature
            curr_Pt_shape = ogr.Feature(self.outshape_featdef)
            curr_Pt_shape.SetGeometry(curr_Pt_geom)
            curr_Pt_shape.SetField('id', curr_Pt_id)                                       
            curr_Pt_shape.SetField('x', curr_Pt[0])
            curr_Pt_shape.SetField('y', curr_Pt[1]) 
            curr_Pt_shape.SetField('z', curr_Pt[2]) 

            curr_Pt_shape.SetField('srcPt_x', self.intersections['point']['x'])
            curr_Pt_shape.SetField('srcPt_y', self.intersections['point']['y']) 
            curr_Pt_shape.SetField('srcPt_z', self.intersections['point']['z'])

            curr_Pt_shape.SetField('dip_dir', self.srcPlaneAttitude._dipdir)
            curr_Pt_shape.SetField('dip_ang', self.srcPlaneAttitude._dipangle)             

            # add the feature to the output layer
            self.out_layer.CreateFeature(curr_Pt_shape)            
            
            # destroy no longer used objects
            curr_Pt_geom.Destroy()
            curr_Pt_shape.Destroy()
                            
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
                
                if direct == 'x': x, y = self.inters.xcoords_x[ i, j ], self.inters.xcoords_y[ i, j ]
                if direct == 'y': x, y = self.inters.ycoords_x[ i, j ], self.inters.ycoords_y[ i, j ] 
                                       
                z = self.plane_z( x, y )
 
                line.AddPoint( x, y, z )            
                                       
            # create a new feature
            line_shape = ogr.Feature( self.outshape_featdef )
            line_shape.SetGeometry( line )   

            line_shape.SetField( 'id', curr_path_id )
            line_shape.SetField( 'srcPt_x', self.intersections['point']['x'] )
            line_shape.SetField( 'srcPt_y', self.intersections['point']['y'] ) 
            line_shape.SetField( 'srcPt_z', self.intersections['point']['z'] )
    
            line_shape.SetField( 'dip_dir', self.srcPlaneAttitude._dipdir )
            line_shape.SetField( 'dip_ang', self.srcPlaneAttitude._dipangle )             
    
            # add the feature to the output layer
            self.out_layer.CreateFeature( line_shape )            
            
            # destroy no longer used objects
            line.Destroy()
            line_shape.Destroy()
                            
        # destroy output geometry
        self.out_shape.Destroy() 
        
    
    """
    def save_bestfitplane_results( self ):
        
        pass
    """    
        
           
    def onPluginClose(self):

        self.intersection_reset_all()
        self.bestfitplane_reset_all()

