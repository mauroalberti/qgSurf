# -*- coding: utf-8 -*-


from math import floor
import numpy as np

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

from qgs_tools.tools import get_current_raster_layers, project_point, \
     make_qgs_point
from qgs_tools.ptmaptool import PointMapToolEmitPoint
    
try:
    from osgeo import ogr
except: 
    import ogr

from geosurf.geoio import read_dem
from geosurf.spatial import Point, Vector
from geosurf.svd import xyz_svd 
        

class bestfitplane_QWidget( QWidget ):
    """
    Constructor
    
    """

    line_colors = [ "white", "red", "blue", "yellow", "orange", "brown",]
    dem_default_text = '--  required  --'


    def __init__( self, canvas, plugin ):

        super( bestfitplane_QWidget, self ).__init__()         
        self.canvas, self.plugin = canvas, plugin       
        self.initialize_parameters()                 
        self.setup_gui() 


    def update_crs_settings( self ):

        self.get_on_the_fly_projection()
        if self.on_the_fly_projection: self.get_current_canvas_crs()        
        
        
    def get_on_the_fly_projection( self ):
        
        self.on_the_fly_projection = True if self.canvas.hasCrsTransformEnabled() else False
       
        
    def get_current_canvas_crs( self ):        
                
        self.projectCrs = self.canvas.mapRenderer().destinationCrs()

            
    def initialize_parameters(self):
 
        self.previousTool = None        
        self.grid = None
        self.input_points = None
        self.bestfitplane_point_markers = []         

        
    def setup_gui( self ):

        dialog_layout = QVBoxLayout()
        main_widget = QTabWidget()        
        main_widget.addTab( self.setup_fplane_tab(), "Processing" )         
        main_widget.addTab( self.setup_help_tab(), "Help" )                             
        dialog_layout.addWidget( main_widget )                                     
        self.setLayout( dialog_layout )                    
        self.adjustSize()                       
        self.setWindowTitle( 'qgSurf - best fit plane' )        


    def setup_fplane_tab( self ):
        
        plansurfaceWidget = QWidget()  
        plansurfaceLayout = QVBoxLayout( )        
        plansurfaceLayout.addWidget( self.setup_source_dem() )         
        plansurfaceLayout.addWidget( self.setup_bfp_calc_tab() )                                       
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


    def setup_help_tab( self ):
        
        helpWidget = QWidget()  
        helpLayout = QVBoxLayout( )        
        htmlText = """
This module allows to calculate the best-fit plane give a DEM and a set of points.

<h4>Loading of DEM data</h4>
<b>a)</b> Load in the QGis project the required DEM(s) layers and whatsoever vector or image layers needed for your analysis.
<br /><b>b)</b> Use "Get current raster layers" in qgSurf plugin: this will allow the plugin to know which raster layers are currently loaded.
<br /><b>c)</b> From the "Use DEM" combo box, choose the DEM to use.

<h4>Best-fit plane calculation</h4>
The algorithm is based on the application of singular value decomposition (SVD) techniques to derive the eigenvectors of a set of measures. 
<br />The best-fit plane processing sequence is:
<br /><b>d)</b> from the "Best-fit-plane calculation", press "Define points in map": this will allow you to define in the canvas at least three, 
and possibly more points, whose coordinates will be listed in the plugin widget.
<br /><b>e)</b> having defined at least three points on the map, you can calculate the best-fit plane by pressing "Calculate best-fit-plane": 
a message box will report the dip direction and dip angle of the calculated plane.
<br /><b>f)</b> you can add even more points and recalculate the best-fit plane; otherwise, 
if you want to start a new analysis on the same DEM, go to <b>e)</b>, or if you want to use another DEM, 
go to <b>c)</b> if it is already loaded in the project, or load it in the project and then go to <b>b)</b>.

<h4>Known limitations</h4>
- The project CRS must be set to a planar projection if the analyzed DEM is in polar coordinates (i.e., latitude and longitude).
Rotation angles for input rasters (DEM) are not supported. Errors could be silent, so please check this detail with QGis or other tools.
  
<h4>Known bugs</h4>
- Very large DEM can originate memory errors. Please resize your DEM to a smaller extent or resample it to a larger cell size.
<br />- If you try to define source points outside DEM extent (for instance, because you have on-the-fly reprojection to a project CRS different from that of the DEM), 
a message warning can be repeated more that once.

        """
        
        helpQTextBrowser = QTextBrowser( helpWidget )        
        helpQTextBrowser.insertHtml( htmlText ) 
        helpLayout.addWidget( helpQTextBrowser )
        helpWidget.setLayout(helpLayout)                  
        return helpWidget 
        

    def setup_bfp_calc_tab( self ):        
        
        planecalcWidget = QWidget()  
        planecalcLayout = QGridLayout( )        

        planecalcLayout.addWidget(QLabel( "Source points" ), 2, 0, 1, 2)
        self.bestfitplane_definepoints_pButton = QPushButton( "Define points in map" )
        self.bestfitplane_definepoints_pButton.clicked.connect( self.set_bfp_points )
        self.bestfitplane_definepoints_pButton.setEnabled( False )
        planecalcLayout.addWidget( self.bestfitplane_definepoints_pButton, 3, 0, 1, 2 )
        
        self.bestfitplane_src_points_ListWdgt = QListWidget()
        planecalcLayout.addWidget( self.bestfitplane_src_points_ListWdgt, 4, 0, 1, 2 )
        
        self.bestfitplane_calculate_pButton = QPushButton( "Calculate best-fit-plane" )
        self.bestfitplane_calculate_pButton.clicked.connect( self.calculate_bestfitplane )
        self.bestfitplane_calculate_pButton.setEnabled( False )
        planecalcLayout.addWidget( self.bestfitplane_calculate_pButton, 5, 0, 1, 2 )               
        
        planecalcWidget.setLayout(planecalcLayout)
        
        return planecalcWidget            


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
        QMessageBox.information( self, "Source DEMs", "Found %d raster layers. Select one in 'Use DEM' (below). Warning: when using DEMs in lat-long, set the project CRS to a planar projection, with horizontal distances and heights in the same units (e.g., meters)." % len( self.rasterLayers ))

              
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
       
        curr_point = Point( float( dem_crs_coord_x), float( dem_crs_coord_y) )        
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
        normal_vector = Vector( normal[0], normal[1], normal[2])
        normal_axis = normal_vector.to_axis()
        self.bestfitplane = normal_axis.to_normal_geolplane()        
        QMessageBox.information( self, "Best fit geological plane", 
                                 "Dip direction: %.1f - dip angle: %.1f" %( self.bestfitplane._dipdir, self.bestfitplane._dipangle ))

    
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
        

    def selectOutputVectorFile( self ):
            
        output_filename = QFileDialog.getSaveFileName(self, 
                                                      self.tr( "Save shapefile" ), 
                                                      "*.shp", 
                                                      "shp (*.shp *.SHP)" )        
        if not output_filename: 
            return        
        self.Output_FileName_Input.setText( output_filename ) 

        
        
