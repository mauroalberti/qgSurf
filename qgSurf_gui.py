

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import resources

from bestfitplane_dialog import bestfitplane_QWidget
from plane_geoprocess_dialog import plane_geoprocess_QWidget
from geosurface_simulation_dialog import geosurface_simulation_Dialog
from geosurface_deformation_dialog import geosurface_deformation_Dialog
from about_dialog import about_Dialog



class qgSurf_gui(object):    

    def __init__( self, interface ):

        self.interface = interface
        self.main_window = self.interface.mainWindow()
        self.canvas = self.interface.mapCanvas()


    def initGui( self ):

        self.bestfitplane_processing = QAction( QIcon( ":/plugins/qgSurf/icons/bestfitplane.png" ), "Best fit plane", self.main_window )
        self.bestfitplane_processing.setWhatsThis( "Best fit plane from points" )                   
        self.bestfitplane_processing.triggered.connect( self.run_bestfitplane_processing )
        self.interface.addPluginToMenu( "&qgSurf", self.bestfitplane_processing )
        
        self.plane_geoprocessing = QAction( QIcon( ":/plugins/qgSurf/icons/qgsurf.png" ), "DEM-plane intersection", self.main_window )
        self.plane_geoprocessing.setWhatsThis( "Geoprocessing of planar surfaces" )                   
        self.plane_geoprocessing.triggered.connect( self.run_plane_geoprocessing )
        self.interface.addPluginToMenu( "&qgSurf", self.plane_geoprocessing )

        self.geosurface_simulation = QAction( QIcon( ":/plugins/qgSurf/icons/sin_m.png" ), "Geosurface simulation", self.main_window )
        self.geosurface_simulation.setWhatsThis( "Simulation of analytical geosurfaces" )                   
        self.geosurface_simulation.triggered.connect( self.run_geosurface_simulation )
        self.interface.addPluginToMenu( "&qgSurf", self.geosurface_simulation )

        self.geosurface_deformation = QAction( QIcon( ":/plugins/qgSurf/icons/sin_def_m.png" ), "Geosurface deformation", self.main_window )
        self.geosurface_deformation.setWhatsThis( "Simulation of analytical geosurfaces" )                   
        self.geosurface_deformation.triggered.connect( self.run_geosurface_deformation )
        self.interface.addPluginToMenu( "&qgSurf", self.geosurface_deformation )
        
        self.qgsurf_about = QAction( QIcon( ":/plugins/qgSurf/icons/about.png" ), "About", self.main_window )
        self.qgsurf_about.setWhatsThis( "qgSurf about" )                   
        self.qgsurf_about.triggered.connect( self.run_qgsurf_about )
        self.interface.addPluginToMenu( "&qgSurf", self.qgsurf_about )

        
    def remove_bfp_markers_from_canvas( self ):        

        for mrk in self.bestfitplane_Qwidget.bestfitplane_point_markers:
            self.canvas.scene().removeItem( mrk ) 
        
        
    def run_bestfitplane_processing(self):

        bestfitplane_DockWidget = QDockWidget( 'Best fit plane', self.interface.mainWindow() )        
        bestfitplane_DockWidget.setAttribute(Qt.WA_DeleteOnClose)
        bestfitplane_DockWidget.setAllowedAreas( Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea )        
        self.bestfitplane_Qwidget = bestfitplane_QWidget( self.canvas, self.bestfitplane_processing )        
        bestfitplane_DockWidget.setWidget( self.bestfitplane_Qwidget )
        bestfitplane_DockWidget.destroyed.connect(self.remove_bfp_markers_from_canvas)        
        self.interface.addDockWidget( Qt.RightDockWidgetArea, bestfitplane_DockWidget )
   

    def remove_int_markers_from_canvas( self ):

        for mrk in self.planeProcess_Qwidget.intersection_markers_list:
            self.canvas.scene().removeItem( mrk )

        if self.planeProcess_Qwidget.intersection_sourcepoint_marker is not None:
            self.canvas.scene().removeItem( self.planeProcess_Qwidget.intersection_sourcepoint_marker )            
                
                           
    def run_plane_geoprocessing(self):
     
        plane_geoprocessing_DockWidget = QDockWidget( 'DEM-plane intersection', self.interface.mainWindow() )        
        plane_geoprocessing_DockWidget.setAttribute(Qt.WA_DeleteOnClose)
        plane_geoprocessing_DockWidget.setAllowedAreas( Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea )        
        self.planeProcess_Qwidget = plane_geoprocess_QWidget( self.canvas, self.plane_geoprocessing )        
        plane_geoprocessing_DockWidget.setWidget( self.planeProcess_Qwidget ) 
        plane_geoprocessing_DockWidget.destroyed.connect(self.remove_int_markers_from_canvas )       
        self.interface.addDockWidget( Qt.RightDockWidgetArea, plane_geoprocessing_DockWidget )


    def run_geosurface_simulation(self):
     
        geosurface_simulation_dlg = geosurface_simulation_Dialog( )
        geosurface_simulation_dlg.show()
        geosurface_simulation_dlg.exec_()        


    def run_geosurface_deformation(self):
     
        geosurface_deformation_dlg = geosurface_deformation_Dialog( )
        geosurface_deformation_dlg.show()
        geosurface_deformation_dlg.exec_()
        
        
    def run_qgsurf_about(self):
     
        qgsurf_about_dlg = about_Dialog( )
        qgsurf_about_dlg.show()
        qgsurf_about_dlg.exec_()
        
                
    def unload(self):

        self.interface.removePluginMenu( "&qgSurf", self.bestfitplane_processing )
        self.interface.removePluginMenu( "&qgSurf", self.plane_geoprocessing )
        self.interface.removePluginMenu( "&qgSurf", self.geosurface_simulation )
        self.interface.removePluginMenu( "&qgSurf", self.qgsurf_about )


        

