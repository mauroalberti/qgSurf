# -*- coding: utf-8 -*-

import os
from math import floor
import numpy as np

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
#import qgis.core as QgsCore
from qgis.gui import *

from qgs_tools.ptmaptool import PointMapTool
    
try:
    from osgeo import ogr
except: 
    import ogr

from geosurf import geoio, spatial, utils
from geosurf.intersections import * 

        
class qgSurfDialog( QDialog ):
    """
    Constructor
    
    """

    colormaps = ["jet", "gray", "bone", "hot","autumn", "cool","copper", "hsv", "pink", "spring", "summer", "winter", "spectral", "flag", ] 
    line_colors = [ "white", "red", "blue", "yellow", "orange", "brown",]


    def __init__( self, canvas, plugin ):

        super( qgSurfDialog, self ).__init__() 

        QObject.connect( self, SIGNAL( " rejected ( ) " ), self.onClose )
        
        self.canvas = canvas
        self.plugin = plugin   
            
        self.initialize_parameters()                 
        self.setup_commandwin_gui() 
                
        self.setWindowFlags( Qt.WindowStaysOnTopHint )       

    
    def get_layers_from_qgis(self):        

        curr_map_layers = QgsMapLayerRegistry.instance().mapLayers()
        mapLayers = zip(unicode(curr_map_layers.keys()), curr_map_layers.values())       
        rasterLayers = filter( lambda layer: layer[1].type() == QgsMapLayer.RasterLayer, mapLayers )
        vectorLayers = filter( lambda layer: layer[1].type() == QgsMapLayer.VectorLayer, mapLayers )
        pointvectLayers = filter( lambda layer: layer[1].geometryType() == QGis.Point, vectorLayers )
        return rasterLayers, pointvectLayers


    def initialize_parameters(self):
                
        self.dem = self.input_points = None
        self.sourcePointTool = None
        self.marker = None 
        self.inters_mrk_list = None
        self.intersections = self.valid_intersections = False
        self.intersection_color = qgSurfDialog.line_colors[0]
        self.current_directory = os.path.dirname( __file__ )
        self.rasterLayers, self.pointvectLayers = self.get_layers_from_qgis()
                

    def setup_commandwin_gui( self ):

        self.dialog_layout = QVBoxLayout()
        self.main_widget = QTabWidget()        
        self.setup_geographicdata_tab()
        self.setup_geologicdata_tab()
        self.setup_output_tab() 
        self.setup_about_tab()       
        self.dialog_layout.addWidget( self.main_widget )                             
        self.setLayout( self.dialog_layout )            
        self.adjustSize()               
        self.setWindowTitle( 'qgSurf' )   


    def setup_geographicdata_tab(self):        
        
        inputWidget = QWidget()  
        inputLayout = QGridLayout( )
        
        inputLayout.addWidget(QLabel( "Source DEM" ), 0, 0, 1, 2)        
        dem_default_text = '--  required  --'
        self.DEM_comboBox = QComboBox()
        self.DEM_comboBox.addItem(dem_default_text)
        for (name,layer) in self.rasterLayers:
            self.DEM_comboBox.addItem(layer.name())
        QObject.connect( self.DEM_comboBox, SIGNAL( " currentIndexChanged (int) " ), self.get_dem )
        inputLayout.addWidget(self.DEM_comboBox, 1, 0, 1, 2)
        
        inputLayout.addWidget( QLabel( "Source point" ), 2, 0, 1, 1) 
        
        self.defineSrcPoint_pushButton = QPushButton( "Set source point in map" )
        self.defineSrcPoint_pushButton.setEnabled( False )
        inputLayout.addWidget( self.defineSrcPoint_pushButton, 2, 1, 1, 1 )        
                       
        inputLayout.addWidget( QLabel("X"), 3, 0, 1, 1 )
        self.Pt_x_spinBox = QSpinBox()
        self.Pt_x_spinBox.setRange(-1000000000, 1000000000)
        self.Pt_x_spinBox.setSingleStep(50)
        #QObject.connect( self.Pt_x_spinBox, SIGNAL( " valueChanged (int) " ), self.set_z )
        inputLayout.addWidget( self.Pt_x_spinBox, 3, 1, 1, 1 )  
              
        inputLayout.addWidget( QLabel("Y"), 4, 0, 1, 1 )
        self.Pt_y_spinBox = QSpinBox()
        self.Pt_y_spinBox.setRange(-1000000000, 1000000000)
        self.Pt_y_spinBox.setSingleStep(50)
        #QObject.connect( self.Pt_y_spinBox, SIGNAL( " valueChanged (int) " ), self.set_z )
        inputLayout.addWidget( self.Pt_y_spinBox, 4, 1, 1, 1 ) 
                      
        inputLayout.addWidget( QLabel("Z"), 5, 0, 1, 1 )
        self.Pt_z_spinBox = QSpinBox()
        self.Pt_z_spinBox.setRange(-10000000, 10000000)
        self.Pt_z_spinBox.setSingleStep(5)
        #QObject.connect( self.Pt_z_spinBox, SIGNAL( " valueChanged (int) " ), self.set_z )
        inputLayout.addWidget( self.Pt_z_spinBox, 5, 1, 1, 1 ) 
               
        self.fixz2dem_checkBox = QCheckBox("fix z value to DEM")
        self.fixz2dem_checkBox.setChecked(True)
        QObject.connect( self.fixz2dem_checkBox, SIGNAL( " stateChanged (int) " ), self.set_z )
        inputLayout.addWidget( self.fixz2dem_checkBox, 6, 0, 1, 1 )        
        
        inputWidget.setLayout(inputLayout)              
        self.main_widget.addTab( inputWidget, "Geographic data" )              


                
    def setup_geologicdata_tab(self):

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
        QObject.connect( self.DDirection_dial, SIGNAL( " valueChanged (int) " ), self.update_dipdir_spinbox )    
        planeorientationLayout.addWidget( self.DDirection_dial, 1, 0, 1, 2 )        
                
        self.DAngle_verticalSlider = QSlider()
        self.DAngle_verticalSlider.setRange(0,90)
        self.DAngle_verticalSlider.setProperty("value", 45)
        self.DAngle_verticalSlider.setOrientation(Qt.Vertical)
        self.DAngle_verticalSlider.setInvertedAppearance(True)
        self.DAngle_verticalSlider.setTickPosition(QSlider.TicksBelow)
        self.DAngle_verticalSlider.setTickInterval(15)
        QObject.connect( self.DAngle_verticalSlider, SIGNAL( " valueChanged (int) " ), self.update_dipang_spinbox )
        planeorientationLayout.addWidget( self.DAngle_verticalSlider, 1, 2, 1, 1 )

        self.DDirection_spinBox = QSpinBox()
        self.DDirection_spinBox.setRange(0,360)
        self.DDirection_spinBox.setSingleStep(1)
        QObject.connect( self.DDirection_spinBox, SIGNAL( " valueChanged (int) " ), self.update_dipdir_slider )
        planeorientationLayout.addWidget( self.DDirection_spinBox, 2, 0, 1, 2 )        
         
        self.DAngle_spinBox = QSpinBox()
        self.DAngle_spinBox.setRange(0,90)
        self.DAngle_spinBox.setSingleStep(1)
        self.DAngle_spinBox.setProperty("value", 45) 
        QObject.connect( self.DAngle_spinBox, SIGNAL( " valueChanged (int) " ), self.update_dipang_slider )
        planeorientationLayout.addWidget( self.DAngle_spinBox, 2, 2, 1, 1 )
 
        self.Intersection_calculate_pushButton = QPushButton( "Calculate intersection" )
        QObject.connect( self.Intersection_calculate_pushButton, SIGNAL( " clicked( bool ) " ), self.calculate_intersection )
        planeorientationLayout.addWidget( self.Intersection_calculate_pushButton, 3, 0, 1, 3 )
                                       
        planeorientationWidget.setLayout(planeorientationLayout)              
        self.main_widget.addTab( planeorientationWidget, "Geological data" ) 

        
    def setup_output_tab(self):

        outputWidget = QWidget()  
        outputLayout = QGridLayout( )
               
        self.Save_pushButton = QPushButton("Save intersections")
        QObject.connect( self.Save_pushButton, SIGNAL( " clicked() " ), self.write_results )
        outputLayout.addWidget( self.Save_pushButton, 0, 0, 1, 2 )
        
        self.Output_FileName_Input = QLineEdit()
        outputLayout.addWidget( self.Output_FileName_Input, 1, 0, 1, 1 )

        self.Output_Browse = QPushButton(".....")
        QObject.connect( self.Output_Browse, SIGNAL( "clicked()" ), self.selectOutputVectorFile )
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
        self.main_widget.addTab( outputWidget, "Output" ) 


    def setup_about_tab(self):
        
        aboutWidget = QWidget()  
        aboutLayout = QVBoxLayout( )
        
        htmlText = """
        <h3>qgSurf release 0.2.0 (2013-04-03, experimental)</h3>
        Created by M. Alberti. 
        <br />Licensed under the terms of GNU GPL 3.
        <br />Plugin for determining the topographic intersection of geological planes. 
        <br /><br />For info see www.malg.eu.        
        """
        
        aboutQTextBrowser = QTextBrowser( aboutWidget )        
        aboutQTextBrowser.insertHtml( htmlText ) 
        aboutLayout.addWidget( aboutQTextBrowser )  
        aboutWidget.setLayout(aboutLayout)              
        self.main_widget.addTab( aboutWidget, "About" ) 
        
              
    def get_dem( self, ndx_DEM_file ): 
        
        self.reset_all_markers()
                        
        # no DEM layer defined  
        if ndx_DEM_file == 0:
            self.dem = None
            self.disableSrcPointDef()
            self.disableSrcPointMaptool()
            self.resetSrcPointSpinBoxes()           
            return
        
        dem_name = self.rasterLayers[ndx_DEM_file-1][1].source()          
        try:
            self.dem = geoio.read_dem( dem_name )               
        except:
            QMessageBox.critical( self, "DEM", "Unable to read file" )
            self.dem = None
            return
        if self.dem is None: QMessageBox.critical( self, "DEM", "DEM was not read" )

        # activate point definition in QgsCanvas        
        self.enableSrcPointButton()
        
        # set intersection validity to False
        self.valid_intersections = False        

        
    """               
    def get_points( self, ndx_input_points ):
        
        return
 
        # no trace layer defined
        if ndx_input_points == 0: 
            self.input_points = None
            #self.show_Lineament_checkBox.setCheckState( 0 )
            #self.draw_map()
            return       
         
        # get input point full name 
        input_points_name = self.pointvectLayers[ ndx_input_points - 1 ][ 1 ].source()  

        try:
            success, answer = geoio.read_line_shapefile( input_points_name )
        except:
            QMessageBox.critical( self, "Input points", "Unable to read shapefile" )
            self.input_points = None
            #self.show_Lineament_checkBox.setCheckState( 0 )
            #self.draw_map()
            return
        else:        
            if not success:
                QMessageBox.critical( self, "Input points", answer )
                self.input_points = None
                #self.show_Lineament_checkBox.setCheckState( 0 )
                #self.draw_map()
                return

        self.input_points = dict( extent=answer['extent'], data=answer['data'] )

        
        # set layer visibility on and draw the map        
        #self.draw_map()
    """


    def enableSrcPointButton( self ):
        
        self.defineSrcPoint_pushButton.setEnabled( True )
        QObject.connect( self.defineSrcPoint_pushButton, SIGNAL( " clicked( bool ) " ), self.activateMapTool )
       
                
    def activateMapTool(self):
                
        self.sourcePointTool = PointMapTool( self.canvas, self.plugin ) # mouse listener
        self.previousTool = self.canvas.mapTool() # save the standard map tool for restoring it at the end
        QObject.connect( self.sourcePointTool, SIGNAL("leftClicked"), self.set_srcPoint_from_map )
        self.sourcePointTool.setCursor( Qt.CrossCursor )        
        self.canvas.setMapTool( self.sourcePointTool )
        QMessageBox.information( self, "Source point", "Now you can define the source point in the map" )


    def set_srcPoint_from_map( self, position ): # Add point to analyze
        
        self.reset_all_markers()
                
        mapPos = self.canvas.getCoordinateTransform().toMapCoordinates( position["x"], position["y"] )
        self.marker = QgsVertexMarker( self.canvas )
        self.marker.setIconType( 1 )
        self.marker.setIconSize( 18 )
        self.marker.setPenWidth( 2 )    

        self.marker.setCenter(QgsPoint( mapPos.x(), mapPos.y() ))
        self.canvas.refresh()
        
        self.update_srcpt( mapPos.x(), mapPos.y() )      
        
        
    def update_srcpt ( self, x, y ):
        """
        Update the source point position from user input (click event in map).
  
        """         
        
        self.Pt_x_spinBox.setValue(int(x))
        self.Pt_y_spinBox.setValue(int(y))
        self.set_z()


    def set_z (self):
        """
        Update z value.
        
        """         
        # set intersection validity to False
        self.valid_intersections = False        
        
        if self.dem is None: return
        
        if self.fixz2dem_checkBox.isChecked():    

            curr_x = self.Pt_x_spinBox.value()
            curr_y = self.Pt_y_spinBox.value()
            
            if curr_x <= self.dem.xmin or curr_x >= self.dem.xmax or \
               curr_y <= self.dem.ymin or curr_y >= self.dem.ymax:
                return
           
            curr_point = spatial.Point( curr_x, curr_y )
            currArrCoord = self.dem.geog2array_coord(curr_point)
            
            z = floor(self.dem.interpolate_bilinear(currArrCoord))            
            self.Pt_z_spinBox.setValue(int(z))  
                        
            
    def disableSrcPointDef(self):
        
        self.defineSrcPoint_pushButton.setEnabled( False )
        QObject.disconnect( self.defineSrcPoint_pushButton, SIGNAL( " clicked( bool ) " ), self.activateMapTool )
        
    
    def disableSrcPointMaptool(self):
        
        QObject.disconnect( self.sourcePointTool, SIGNAL("leftClicked"), self.set_srcPoint_from_map) 
        self.canvas.unsetMapTool(self.sourcePointTool)
        self.canvas.setMapTool(self.previousTool)
        
        self.canvas.scene().removeItem(self.marker)
        
      
    def resetSrcPointSpinBoxes(self):
        
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
 
        # set intersection validity to False
        self.valid_intersections = False        
  
           
    def update_dipdir_spinbox(self):            
        """
        Update the value of the dip direction in the spinbox.
        """        
        transformed_dipdirection = self.DDirection_dial.value()
        real_dipdirection = transformed_dipdirection - 180.0
        if real_dipdirection < 0.0:
            real_dipdirection = real_dipdirection + 360.0
            
        self.DDirection_spinBox.setValue( real_dipdirection ) 
        
        # set intersection validity to False
        self.valid_intersections = False

                 
    def update_dipang_slider(self):
        """
        Update the value of the dip angle in the slider.
        """
        self.DAngle_verticalSlider.setValue( self.DAngle_spinBox.value() )    
                  
        # set intersection validity to False
        self.valid_intersections = False
 
                  
    def update_dipang_spinbox(self):            
        """
        Update the value of the dip angle in the spinbox.
        """        
        self.DAngle_spinBox.setValue( self.DAngle_verticalSlider.value() ) 

        # set intersection validity to False
        self.valid_intersections = False

               
    def set_intersection_colormap(self):
        
        self.intersection_color = str( self.Intersection_color_comboBox.currentText() )


    def reset_srcPt_marker(self):

        if self.marker is not None:
            self.canvas.scene().removeItem( self.marker )
                    

    def reset_inters_markers(self):

        if self.inters_mrk_list is not None and len(self.inters_mrk_list)>0:
            for mrk in self.inters_mrk_list:
                self.canvas.scene().removeItem( mrk )          
        
        
    def reset_all_markers(self):
        
        self.reset_srcPt_marker()
        self.reset_inters_markers()
      
               
    def calculate_intersection( self ):
        """
        Calculate intersection points.
        """                

        self.reset_inters_markers()
                    
        sourcePoint = spatial.Point(self.Pt_x_spinBox.value(), 
                           self.Pt_y_spinBox.value(), 
                           self.Pt_z_spinBox.value())

        srcDipDir = self.DDirection_spinBox.value()
        srcDipAngle = self.DAngle_verticalSlider.value()

        self.srcPlaneAttitude = spatial.StructPlane( srcDipDir, srcDipAngle )

        # intersection arrays
        
        self.inters = Intersections()
        
        intersection_results = self.dem.intersection_with_surface('plane', 
                                                                         sourcePoint,  
                                                                         self.srcPlaneAttitude )
        
        self.inters.xcoords_x = intersection_results[0]
        self.inters.xcoords_y = intersection_results[1]
        self.inters.ycoords_x = intersection_results[2]
        self.inters.ycoords_y = intersection_results[3]
            
        self.inters.parameters = Intersection_Parameters(self.dem._sourcename, sourcePoint, self.srcPlaneAttitude)


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
        
        intersection_color = self.intersection_color
        
        self.intersections = dict(data=intersection_data,
                                  plane=intersection_plane,
                                  point=intersection_point,
                                  color=intersection_color)
                
        self.valid_intersections = True

        self.plot_intersections()
        
        
    def plot_intersections(self):
        
        self.inters_mrk_list = []
        for x, y in zip( self.intersections_x, self.intersections_y ): 
            marker = QgsVertexMarker( self.canvas )
            marker.setIconType( 1 )
            marker.setColor( QColor(0, 0, 255 ) )
            marker.setIconSize( 8 )
            marker.setPenWidth( 1 )
            marker.setCenter( QgsPoint( x, y) )
            self.inters_mrk_list.append(marker)
            
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
        if self.inters.xcoords_x == [] and \
           self.inters.xcoords_y == [] and \
           self.inters.ycoords_x == [] and \
           self.inters.ycoords_y == [] :
            QMessageBox.critical(self, "Save results", "No results available") 
            return

        self.output_filename = str( self.Output_FileName_Input.text() ) 
        if self.output_filename == '':
            QMessageBox.critical(self, "Save results", "No output file defined") 
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
        self.plane_z = spatial.plane_from_geo( sourcePoint, self.srcPlaneAttitude )  
              
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
        
    
    def onClose(self):
             
        self.reset_all_markers()


     
 