# -*- coding: utf-8 -*-


import os
import sys

import webbrowser

import qgis.core as QgsCore
from PyQt4.QtCore import *
from PyQt4.QtGui import *


from matplotlib.offsetbox import AnchoredOffsetbox, AuxTransformBox, VPacker,\
     TextArea, DrawingArea
     
try:
    from osgeo import ogr
except: 
    import ogr
    
from qgSurf_mplwidget import MplWidget
from qgSurf_data import *
from qgSurf_utils import *


      
        
class qgSurfDialog( QDialog ):
    """
    Constructor
    
    """

    # static attributes
    colormaps = ["jet", "gray", "bone", "hot","autumn", "cool","copper", "hsv", "pink", "spring", "summer", "winter", "spectral", "flag", ] 
    trace_colors = [ "white", "red", "blue", "yellow", "orange", "brown",]
    original_extent = [0,100]
    
    def __init__( self ):

        super( qgSurfDialog, self ).__init__()

        self.initializations() 
                
        self.setupUI()
        
        self.linkQGIS()
        
        self.setConnections()   
        


    def initializations(self):

        # dem and map extent settings      
        self.dem_extent_x = self.dem_extent_y = qgSurfDialog.original_extent
        self.map_extent_x = self.map_extent_y = qgSurfDialog.original_extent
        
        # colormaps
        self.dem_colormap = qgSurfDialog.colormaps[0]
        self.intersection_color = qgSurfDialog.trace_colors[0]        
        
        # initialize intersection drawing
        self.valid_intersections = False
        
        # initialize spdata
        self.spdata = GeoData() 
                
             

    def setupUI( self ):
        
        self.setWindowTitle( 'qgSurf' )
        
        # set layout for dialog
        self.dialogSplitter = QSplitter( Qt.Horizontal, self )
        
        # define left widget and layout
        leftWidget = QWidget()
        leftLayout = QVBoxLayout()
        leftWidget.setLayout( leftLayout )

        # define right widget and layout        
        rightWidget = QWidget()
        rightLayout = QVBoxLayout()
        rightWidget.setLayout( rightLayout )
        
        # setup input data
        inputGroupBox = self.setupInput()
        leftLayout.addWidget(inputGroupBox)

        # setup source point
        sourcepointGroupBox = self.setupSourcePoint()
        leftLayout.addWidget( sourcepointGroupBox )        
        
        # setup plane settings
        planeGroupBox = self.setupPlane()
        leftLayout.addWidget( planeGroupBox )
        
        # setup intersection settings
        intersectionGroupBox = self.setupIntersection()
        leftLayout.addWidget( intersectionGroupBox )

        # setup output settings
        outputGroupBox = self.setupOutput()
        leftLayout.addWidget( outputGroupBox )
        
        # map
        self.mplwidget = MplWidget( self.map_extent_x, self.map_extent_y )
        rightLayout.addWidget( self.mplwidget )

        # add left and right widgets to dialog layout
        self.dialogSplitter.addWidget( leftWidget )
        self.dialogSplitter.addWidget( rightWidget )
        
        self.resize( 1150, 750 )


    def setupInput(self):        

        # input data        
        inputGroupBox = QGroupBox( "Input layers" )       
        inputLayout = QGridLayout()
        inputGroupBox.setLayout(inputLayout)
        
        inputLayout.addWidget(QLabel( "DEM" ), 0, 0)
        
        self.DEM_comboBox = QComboBox()
        inputLayout.addWidget(self.DEM_comboBox, 0, 1)
                
        self.show_DEM_checkBox = QCheckBox("show")
        self.show_DEM_checkBox.setChecked(False)
        inputLayout.addWidget(self.show_DEM_checkBox, 0, 2)

        inputLayout.addWidget( QLabel( "DEM colormap" ), 1, 0)
        
        self.DEM_cmap_comboBox = QComboBox()
        self.DEM_cmap_comboBox.addItems(qgSurfDialog.colormaps)
        inputLayout.addWidget(self.DEM_cmap_comboBox, 1, 1)

        inputLayout.addWidget( QLabel( "Lineaments" ), 2, 0)        

        self.Trace_comboBox = QComboBox()
        inputLayout.addWidget(self.Trace_comboBox, 2, 1)        

        self.show_Lineament_checkBox = QCheckBox("show")
        self.show_Lineament_checkBox.setChecked(False) 
        inputLayout.addWidget(self.show_Lineament_checkBox, 2, 2)        
        
        return inputGroupBox
    
        
    def setupSourcePoint(self):      
        
        sourcepointGroupBox = QGroupBox( "Plane source point" )
        sourcepointLayout = QGridLayout()
        sourcepointGroupBox.setLayout(sourcepointLayout)
       
        sourcepointLayout.addWidget( QLabel("X"), 0, 0 )
        self.Pt_spinBox_x = QSpinBox()
        self.Pt_spinBox_x.setRange(-1000000000, 1000000000)
        self.Pt_spinBox_x.setSingleStep(50)
        sourcepointLayout.addWidget( self.Pt_spinBox_x, 0, 1 )
        
        sourcepointLayout.addWidget( QLabel("Y"), 1, 0 )
        self.Pt_spinBox_y = QSpinBox()
        self.Pt_spinBox_y.setRange(-1000000000, 1000000000)
        self.Pt_spinBox_y.setSingleStep(50)
        sourcepointLayout.addWidget( self.Pt_spinBox_y, 1, 1 )
               
        sourcepointLayout.addWidget( QLabel("Z"), 2, 0 )
        self.Pt_spinBox_z = QSpinBox()
        self.Pt_spinBox_z.setRange(-10000000, 10000000)
        self.Pt_spinBox_z.setSingleStep(5)
        sourcepointLayout.addWidget( self.Pt_spinBox_z, 2, 1 )
        
        self.fixz2dem_checkBox = QCheckBox("fix  to DEM")
        self.fixz2dem_checkBox.setChecked(True)
        sourcepointLayout.addWidget( self.fixz2dem_checkBox, 3, 0 )
        
        self.show_SrcPt_checkBox = QCheckBox("show")
        self.show_SrcPt_checkBox.setChecked(True)
        sourcepointLayout.addWidget( self.show_SrcPt_checkBox, 3, 1 )

        return sourcepointGroupBox
        

    def setupPlane(self):

        planeGroupBox = QGroupBox("Plane orientation")
        planeGroupBox.setFixedHeight ( 230 )
        planeLayout = QGridLayout()
        planeGroupBox.setLayout(planeLayout)
        
        dip_dir_label = QLabel("Dip direction")
        dip_dir_label.setAlignment ( Qt.AlignCenter )       
        planeLayout.addWidget( dip_dir_label, 0, 0 )

        dip_ang_label = QLabel("Dip angle")
        dip_ang_label.setAlignment ( Qt.AlignCenter )       
        planeLayout.addWidget( dip_ang_label, 0, 1 )
        
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
        planeLayout.addWidget( self.DDirection_dial, 1, 0 )
        
                
        self.DAngle_verticalSlider = QSlider()
        self.DAngle_verticalSlider.setRange(0,90)
        self.DAngle_verticalSlider.setProperty("value", 45)
        self.DAngle_verticalSlider.setOrientation(Qt.Vertical)
        self.DAngle_verticalSlider.setInvertedAppearance(True)
        self.DAngle_verticalSlider.setTickPosition(QSlider.TicksBelow)
        self.DAngle_verticalSlider.setTickInterval(15)
        planeLayout.addWidget( self.DAngle_verticalSlider, 1, 1 )

        self.DDirection_spinBox = QSpinBox()
        self.DDirection_spinBox.setRange(0,360)
        self.DDirection_spinBox.setSingleStep(1)
        planeLayout.addWidget( self.DDirection_spinBox, 2, 0 )        
         
        self.DAngle_spinBox = QSpinBox()
        self.DAngle_spinBox.setRange(0,90)
        self.DAngle_spinBox.setSingleStep(1)
        self.DAngle_spinBox.setProperty("value", 45) 
        planeLayout.addWidget( self.DAngle_spinBox, 2, 1 )
                
        return planeGroupBox  

      
    def setupIntersection(self):
        
        intersectionGroupBox = QGroupBox( "Intersections" )
        intersectionLayout = QGridLayout()
        intersectionGroupBox.setLayout(intersectionLayout)      
        
        self.Intersection_color_comboBox = QComboBox(intersectionGroupBox)
        self.Intersection_color_comboBox.addItems( qgSurfDialog.trace_colors)
        intersectionLayout.addWidget( self.Intersection_color_comboBox, 0, 0 )
                
        self.Intersection_show_checkBox = QCheckBox( "show" )
        self.Intersection_show_checkBox.setChecked(True)
        intersectionLayout.addWidget( self.Intersection_show_checkBox, 0, 1 )        

        self.Intersection_calculate_pushButton = QPushButton( "Calculate" )
        intersectionLayout.addWidget( self.Intersection_calculate_pushButton, 0, 2 )
        
        return intersectionGroupBox     
 
        
    def setupOutput(self):
 
        outputGroupBox = QGroupBox( "Output" )
        outputLayout = QGridLayout()
        outputGroupBox.setLayout(outputLayout)         
               
        # load output
        self.Load_output_checkBox = QCheckBox("load output in project")
        outputLayout.addWidget( self.Load_output_checkBox, 0, 0 )

        self.Output_FileName_Input = QLineEdit()
        outputLayout.addWidget( self.Output_FileName_Input, 0, 1 )

        self.Output_Browse = QPushButton(".....")
        outputLayout.addWidget( self.Output_Browse, 0, 2 )
 
        self.Save_points_radioButton = QRadioButton("points")
        self.Save_points_radioButton.setChecked(True)
        outputLayout.addWidget( self.Save_points_radioButton, 1, 0 )
        
        self.Save_lines_radioButton = QRadioButton("lines")
        outputLayout.addWidget( self.Save_lines_radioButton, 1, 1 )
 
        self.Save_pushButton = QPushButton("Save")
        outputLayout.addWidget( self.Save_pushButton, 1, 2 )
               
        return outputGroupBox

        
    def linkQGIS(self):        
        
        # filter raster and vector layers
        curr_map_layers = QgsCore.QgsMapLayerRegistry.instance().mapLayers()
        self.mapLayers = zip(unicode(curr_map_layers.keys()), curr_map_layers.values())       
        self.rasterLayers = filter( lambda layer: layer[1].type() == QgsCore.QgsMapLayer.RasterLayer, self.mapLayers )
        self.vectorLayers = filter( lambda layer: layer[1].type() == QgsCore.QgsMapLayer.VectorLayer, self.mapLayers )
        self.linevectLayers = filter( lambda layer: layer[1].geometryType() == QgsCore.QGis.Line, self.vectorLayers )
 
        # fill layer combo boxes
        dem_default_text = '--  required  --'
        trace_default_text = '--  optional  --'
        self.DEM_comboBox.addItem(dem_default_text)
        self.Trace_comboBox.addItem(trace_default_text)     
        
        for (name,layer) in self.rasterLayers:
            self.DEM_comboBox.addItem(layer.name())
            
        for (name,layer) in self.linevectLayers:
            self.Trace_comboBox.addItem(layer.name())


    def setConnections(self):

        # DEM
        QObject.connect( self.DEM_comboBox, SIGNAL( " currentIndexChanged (int) " ), self.selected_dem )
        QObject.connect( self.show_DEM_checkBox, SIGNAL( " stateChanged (int) " ), self.redraw_map )
        
        QObject.connect( self.DEM_cmap_comboBox, SIGNAL( " currentIndexChanged (QString) " ), self.set_dem_colormap )        
        QObject.connect( self.DEM_cmap_comboBox, SIGNAL( " currentIndexChanged (QString) " ), self.redraw_map )
 
        # Lineament traces
        QObject.connect( self.Trace_comboBox, SIGNAL( " currentIndexChanged (int) " ), self.reading_traces )                
        QObject.connect( self.show_Lineament_checkBox, SIGNAL( " stateChanged (int) " ), self.redraw_map )

        # Limits
        QObject.connect( self.mplwidget.canvas, SIGNAL( " zoom_to_full_view " ), self.zoom_to_full_view )
        QObject.connect( self.mplwidget.canvas, SIGNAL( " updated_limits " ), self.update_map_limits )
                         
        # Source point
        QObject.connect( self.mplwidget.canvas, SIGNAL( " map_press " ), self.update_srcpt ) # event from matplotlib widget
                
        QObject.connect( self.Pt_spinBox_x, SIGNAL( " valueChanged (int) " ), self.set_z )
        QObject.connect( self.Pt_spinBox_y, SIGNAL( " valueChanged (int) " ), self.set_z )
        QObject.connect( self.fixz2dem_checkBox, SIGNAL( " stateChanged (int) " ), self.set_z )         
        QObject.connect( self.Pt_spinBox_z, SIGNAL( " valueChanged (int) " ), self.set_z )
                                           
        QObject.connect( self.Pt_spinBox_x, SIGNAL( " valueChanged (int) " ), self.redraw_map )
        QObject.connect( self.Pt_spinBox_y, SIGNAL( " valueChanged (int) " ), self.redraw_map ) 
        QObject.connect( self.Pt_spinBox_z, SIGNAL( " valueChanged (int) " ), self.redraw_map ) 
        QObject.connect( self.show_SrcPt_checkBox, SIGNAL( " stateChanged (int) " ), self.redraw_map )

        # Plane orientation              
        QObject.connect( self.DDirection_dial, SIGNAL( " valueChanged (int) " ), self.update_dipdir_spinbox )
        QObject.connect( self.DDirection_spinBox, SIGNAL( " valueChanged (int) " ), self.update_dipdir_slider )
               
        QObject.connect( self.DAngle_verticalSlider, SIGNAL( " valueChanged (int) " ), self.update_dipang_spinbox )
        QObject.connect( self.DAngle_spinBox, SIGNAL( " valueChanged (int) " ), self.update_dipang_slider )

        # Intersections    
        QObject.connect( self.Intersection_calculate_pushButton, SIGNAL( " clicked( bool ) " ), self.calculate_intersection )
        QObject.connect( self.Intersection_show_checkBox, SIGNAL( " stateChanged (int) " ), self.redraw_map )
        
        QObject.connect( self.Intersection_color_comboBox, SIGNAL( " currentIndexChanged (QString) " ), self.set_intersection_colormap )  
        QObject.connect( self.Intersection_color_comboBox, SIGNAL( " currentIndexChanged (QString) " ), self.redraw_map )     
          
        # Write result
        QObject.connect( self.Output_Browse, SIGNAL( "clicked()" ), self.selectOutputVectorFile )
        QObject.connect( self.Save_pushButton, SIGNAL( " clicked() " ), self.write_results )
 
      
    def set_dem_colormap(self):
        
        self.dem_colormap = str( self.DEM_cmap_comboBox.currentText() )
        

    def set_intersection_colormap(self):
        
        self.intersection_color = str( self.Intersection_color_comboBox.currentText() )


    def update_map_limits(self, limits ):
    
        self.map_extent_x = limits[0]
        self.map_extent_y = limits[1]
                         
        
    def redraw_map( self ):            
        """
        Draw map content.
               
        """  
              
        self.mplwidget.canvas.ax.cla()
        
        # show DEM
        if self.spdata.dem is not None and self.show_DEM_checkBox.isChecked(): # DEM check is on                
                 
                dem_extent = self.dem_extent_x + self.dem_extent_y                       
                self.mplwidget.canvas.ax.imshow(
                                                self.spdata.dem.data, 
                                                extent = dem_extent,  
                                                cmap = self.dem_colormap,
                                                )
   
        # show lineaments
        if self.spdata.traces.lines_x is not None and self.spdata.traces.lines_y is not None \
           and self.show_Lineament_checkBox.isChecked(): # Lineament check is on 

            try:
                for currLine_x, currLine_y in zip(self.fault_lines_x, self.fault_lines_y):                                
                    self.mplwidget.canvas.ax.plot(currLine_x, currLine_y,'-')
            except:
                pass
         
        # show intersections
        if self.Intersection_show_checkBox.isChecked() and self.valid_intersections == True:
                        
            intersections_x = list( self.spdata.inters.xcoords_x[ np.logical_not(np.isnan(self.spdata.inters.xcoords_x)) ] ) + \
                              list( self.spdata.inters.ycoords_x[ np.logical_not(np.isnan(self.spdata.inters.ycoords_y)) ] )
        
            intersections_y = list( self.spdata.inters.xcoords_y[ np.logical_not(np.isnan(self.spdata.inters.xcoords_x)) ] ) + \
                              list( self.spdata.inters.ycoords_y[ np.logical_not(np.isnan(self.spdata.inters.ycoords_y)) ] )
                        
            self.mplwidget.canvas.ax.plot( intersections_x, intersections_y,  "w+",  ms=2,  mec=self.intersection_color,  mew=2 )
                                
            legend_text = "Plane dip dir., angle: (%d, %d)\nSource point x, y, z: (%d, %d, %d)" % \
                (self.spdata.inters.parameters._srcPlaneAttitude._dipdir, self.spdata.inters.parameters._srcPlaneAttitude._dipangle, \
                 self.spdata.inters.parameters._srcPt.x, self.spdata.inters.parameters._srcPt.y, self.spdata.inters.parameters._srcPt.z) 
                                             
            at = AnchoredText(legend_text,
                          loc=2, frameon=True)  
            
            at.patch.set_boxstyle("round,pad=0.,rounding_size=0.2")
            at.patch.set_alpha(0.5)
            self.mplwidget.canvas.ax.add_artist(at) 

        # show source point          
        if self.show_SrcPt_checkBox.isChecked(): 
            self.mplwidget.canvas.ax.plot( self.Pt_spinBox_x.value(), self.Pt_spinBox_y.value(), "ro")                                        

        self.mplwidget.canvas.ax.set_xlim( self.map_extent_x ) 
        self.mplwidget.canvas.ax.set_ylim( self.map_extent_y ) 
        self.mplwidget.canvas.draw()         
 
            
    def zoom_to_full_view( self ):
        """
        Update map view to the DEM extent or otherwise, if available, to the shapefile extent.
                
        """      
       
        try:
            self.map_extent_x = [ self.spdata.dem.domain.g_llcorner().x, self.spdata.dem.domain.g_trcorner().x ]
            self.map_extent_y = [ self.spdata.dem.domain.g_llcorner().y, self.spdata.dem.domain.g_trcorner().y ]
        except:
            try:
                self.map_extent_x = self.lnLayer.GetExtent()[:2]               
                self.map_extent_y = self.lnLayer.GetExtent()[2:]   
            except:
                self.map_extent_x = qgSurfDialog.original_extent               
                self.map_extent_y = qgSurfDialog.original_extent
        finally:
            self.redraw_map( )



    def selected_dem( self, ndx_DEM_file ): 
        
        # no DEM layer defined  
        if ndx_DEM_file == 0:
            return         
         
        # get DEM full name 
        dem_name = self.rasterLayers[ndx_DEM_file -1][1].source()  
        
        try:
            self.spdata.dem = self.spdata.read_dem( dem_name )
        except:
            QMessageBox.critical( self, "DEM", "Unable to read file" )
            return
        
        self.dem_extent_x = [ self.spdata.dem.domain.g_llcorner().x, self.spdata.dem.domain.g_trcorner().x ]
        self.dem_extent_y = [ self.spdata.dem.domain.g_llcorner().y, self.spdata.dem.domain.g_trcorner().y ]
            
        self.map_extent_x = [ self.spdata.dem.domain.g_llcorner().x, self.spdata.dem.domain.g_trcorner().x ]
        self.map_extent_y = [ self.spdata.dem.domain.g_llcorner().y, self.spdata.dem.domain.g_trcorner().y ]

        # set intersection validity to False
        self.valid_intersections = False        
             
        # set DEM visibility on        
        if self.show_DEM_checkBox.checkState() == 2:
            self.redraw_map()
        else: 
            self.show_DEM_checkBox.setCheckState( 2 )


           
    def reading_traces( self, ndx_Traces_file ):
                
        # no trace layer defined
        if ndx_Traces_file == 0: 
            return
         
        # get traces full name 
        traces_name = self.linevectLayers[ ndx_Traces_file -1 ][ 1 ].source()              
        
        # open input vector layer
        shape_driver = ogr.GetDriverByName( "ESRI Shapefile" )

        in_shape = shape_driver.Open( str( traces_name ), 0 )

        # layer not read
        if in_shape is None: 
            QMessageBox.critical( self, 
                                  "Lineament traces", 
                                  "Unable to open shapefile" 
                                )
          
        # get internal layer
        self.lnLayer = in_shape.GetLayer(0) 
         
        # set vector layer extent   
        vectlayer_extent_x = self.lnLayer.GetExtent()[:2]
        vectlayer_extent_y = self.lnLayer.GetExtent()[2:]
        
        if self.dem_extent_x == qgSurfDialog.original_extent and \
           self.dem_extent_y == qgSurfDialog.original_extent:
            self.map_extent_x = vectlayer_extent_x
            self.map_extent_y = vectlayer_extent_y
                    
        # initialize lists storing line coordinates
        self.fault_lines_x = []
        self.fault_lines_y = []
                                 
        # start reading layer features              
        curr_line = self.lnLayer.GetNextFeature()
        
        # loop in layer features       
        while curr_line:        
                    
            line_vert_x = []
            line_vert_y = []
                        
            line_geom = curr_line.GetGeometryRef()
            
            for i in range( line_geom.GetPointCount() ):
                                
                x, y = line_geom.GetX(i), line_geom.GetY(i)
                            
                line_vert_x.append(x)
                line_vert_y.append(y)                
                                
            self.fault_lines_x.append(line_vert_x)    
            self.fault_lines_y.append(line_vert_y)
                        
            curr_line = self.lnLayer.GetNextFeature()
                    
        in_shape.Destroy()
        
        # set layer visibility on        
        if self.show_Lineament_checkBox.checkState() == 2:
            self.redraw_map()
        else:
            self.show_Lineament_checkBox.setCheckState( 2 ) 
                
 
 
    def update_srcpt (self, pos_values):
        """
        Update the source point position from user input (click event in map).
          
        @param pos_values: location of clicked point.
        @type: list of two float values.      
        """         
        x = pos_values[0]
        y = pos_values[1]
        
        self.Pt_spinBox_x.setValue(int(x))
        self.Pt_spinBox_y.setValue(int(y))
        
        # set intersection validity to False
        self.valid_intersections = False



    def set_z (self):
        """
        Update z value.
        
        """ 
        
        # set intersection validity to False
        self.valid_intersections = False        
        
        if self.spdata.dem is None: return
        
        if self.fixz2dem_checkBox.isChecked():    
   
            curr_x = self.Pt_spinBox_x.value()
            curr_y = self.Pt_spinBox_y.value()
            
            if curr_x <= self.spdata.dem.domain.g_llcorner().x or curr_x >= self.spdata.dem.domain.g_trcorner().x or \
               curr_y <= self.spdata.dem.domain.g_llcorner().y or curr_y >= self.spdata.dem.domain.g_trcorner().y:
                return
           
            curr_point = Point( curr_x, curr_y )
            currArrCoord = self.spdata.dem.geog2array_coord(curr_point)
    
            z = floor(self.spdata.dem.interpolate_bilinear(currArrCoord))
    
            self.Pt_spinBox_z.setValue(int(z))        
  
      
      
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

               
       
    def calculate_intersection( self ):
        """
        Calculate intersection points.
        """                
                      
        curr_x = self.Pt_spinBox_x.value()
        curr_y = self.Pt_spinBox_y.value()
        curr_z = self.Pt_spinBox_z.value()
                
        self.srcPt = Point(curr_x, curr_y, curr_z)

        srcDipDir = self.DDirection_spinBox.value()
        srcDipAngle = self.DAngle_verticalSlider.value()

        self.srcPlaneAttitude = StructPlane( srcDipDir, srcDipAngle )

        # intersection arrays
        self.spdata.set_intersections_default()
        
        intersection_results = self.spdata.dem.intersection_with_surface('plane', self.srcPt, self.srcPlaneAttitude )
        
        self.spdata.inters.xcoords_x = intersection_results[0]
        self.spdata.inters.xcoords_y = intersection_results[1]
        self.spdata.inters.ycoords_x = intersection_results[2]
        self.spdata.inters.ycoords_y = intersection_results[3]
            
        self.spdata.inters.parameters = Intersection_Parameters(self.spdata.dem._sourcename, self.srcPt, self.srcPlaneAttitude)
        
        self.valid_intersections = True

        self.redraw_map( )

        
    def selectOutputVectorFile( self ):
            
        output_filename = QFileDialog.getSaveFileName( 
                                                              self, 
                                                              self.tr( "Save shapefile" ), 
                                                              "*.shp", 
                                                              "shp (*.shp *.SHP)" )
        
        if output_filename.isEmpty():
            return
        self.Output_FileName_Input.setText( output_filename ) 
            
                
        
    def write_results(self):
        """
        Write intersection results in the output shapefile.
        """
 
        # check for result existence        
        if self.spdata.inters.xcoords_x == [] and \
           self.spdata.inters.xcoords_y == [] and \
           self.spdata.inters.ycoords_x == [] and \
           self.spdata.inters.ycoords_y == [] :
            QMessageBox.critical(self, "Save results", "No results available") 
            return

        self.output_filename = str( self.Output_FileName_Input.text() ) 
        if self.output_filename == '':
            QMessageBox.critical(self, "Save results", "No output file defined") 
            return
                           
        # set output type
        if self.Save_points_radioButton.isChecked():
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
        self.srcPt = self.spdata.inters.parameters._srcPt
        self.srcPlaneAttitude = self.spdata.inters.parameters._srcPlaneAttitude
        self.plane_z = plane_from_geo( self.srcPt, self.srcPlaneAttitude )  
              
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
                intersection_layer = QgsCore.QgsVectorLayer(self.output_filename, QFileInfo(self.output_filename).baseName(), "ogr")                    
                QgsCore.QgsMapLayerRegistry.instance().addMapLayer( intersection_layer )
            except:            
                QMessageBox.critical( self, "Result", "Unable to load layer in project" )
                return
        
                         
        
    def write_intersections_as_points(self):
        """
        Write intersection results in the output shapefile.
        """
                                
        x_filtered_coord_x = self.spdata.inters.xcoords_x[ np.logical_not(np.isnan(self.spdata.inters.xcoords_x)) ] 
        x_filtered_coord_y = self.spdata.inters.xcoords_y[ np.logical_not(np.isnan(self.spdata.inters.xcoords_x)) ]            
        x_filtered_coord_z = self.plane_z( x_filtered_coord_x, x_filtered_coord_y )

        y_filtered_coord_x = self.spdata.inters.ycoords_x[ np.logical_not(np.isnan(self.spdata.inters.ycoords_y)) ] 
        y_filtered_coord_y = self.spdata.inters.ycoords_y[ np.logical_not(np.isnan(self.spdata.inters.ycoords_y)) ]             
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

            curr_Pt_shape.SetField('srcPt_x', self.srcPt.x)
            curr_Pt_shape.SetField('srcPt_y', self.srcPt.y) 
            curr_Pt_shape.SetField('srcPt_z', self.srcPt.z)

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
        self.spdata.inters.links = self.spdata.get_intersections()
        self.spdata.inters.neighbours = self.spdata.set_neighbours( ) 
        self.spdata.define_paths( )  
        
        # networks of connected intersections
        self.spdata.inters.networks = self.spdata.define_networks()   
        
        for curr_path_id, curr_path_points in self.spdata.inters.networks.iteritems():
                                    
            line = ogr.Geometry(ogr.wkbLineString)
            
            for curr_point_id in curr_path_points:  
                          
                curr_intersection = self.spdata.inters.links[curr_point_id-1]
                           
                i, j, direct = curr_intersection['i'], curr_intersection['j'], curr_intersection['pi_dir']
                
                if direct == 'x': x, y = self.spdata.inters.xcoords_x[i,j], self.spdata.inters.xcoords_y[i,j]
                if direct == 'y': x, y = self.spdata.inters.ycoords_x[i,j], self.spdata.inters.ycoords_y[i,j] 
                                       
                z = self.plane_z(x,y)
 
                line.AddPoint(x,y,z)            
                                       
            # create a new feature
            line_shape = ogr.Feature(self.outshape_featdef)
            line_shape.SetGeometry(line)   

            line_shape.SetField('id', curr_path_id)
            line_shape.SetField('srcPt_x', self.srcPt.x)
            line_shape.SetField('srcPt_y', self.srcPt.y) 
            line_shape.SetField('srcPt_z', self.srcPt.z)
    
            line_shape.SetField('dip_dir', self.srcPlaneAttitude._dipdir)
            line_shape.SetField('dip_ang', self.srcPlaneAttitude._dipangle)             
    
            # add the feature to the output layer
            self.out_layer.CreateFeature(line_shape)            
            
            # destroy no longer used objects
            line.Destroy()
            line_shape.Destroy()
                            
        # destroy output geometry
        self.out_shape.Destroy() 


         
class AnchoredText(AnchoredOffsetbox):
    """
    Creation of an info box in the plot
    
    """
    def __init__(self, s, loc, pad=0.4, borderpad=0.5, prop=None, frameon=True):

        self.txt = TextArea( s, minimumdescent=False )

        super(AnchoredText, self).__init__(loc, pad=pad, borderpad=borderpad,
                                           child=self.txt,
                                           prop=prop,
                                           frameon=frameon)


            
 