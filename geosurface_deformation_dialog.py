# -*- coding: utf-8 -*-


import json

from PyQt4.QtCore import *
from PyQt4.QtGui import *

###import matplotlib.pyplot as plt
###from mpl_toolkits.mplot3d import Axes3D

from qgis.core import *
from qgis.gui import *
 
from geosurf.surfaces import calculate_geosurface
from geosurf.visualization import view_surface
from geosurf.export import save_surface_vtk, save_surface_grass, save_surface_gas
from geosurf.errors import AnaliticSurfaceIOException, AnaliticSurfaceCalcException
  
from geosurface_deformation_windows import geosurface_displacement_Dialog, geosurface_rotation_Dialog 
from geosurface_deformation_windows import geosurface_scaling_Dialog, geosurface_horiz_shear_Dialog, geosurface_vert_shear_Dialog
        
        
class geosurface_deformation_Dialog( QDialog ):


    def __init__( self ):

        super( geosurface_deformation_Dialog, self ).__init__() 
                            
        self.setup_gui() 


    def setup_gui( self ):

        dialog_layout = QVBoxLayout()
        main_widget = QTabWidget()
        
        main_widget.addTab( self.setup_main_tab(), 
                            "3D surface deformation" ) 
                           
        main_widget.addTab( self.setup_help_tab(), 
                            "Help" ) 
                            
        dialog_layout.addWidget( main_widget )                                     
        self.setLayout( dialog_layout )                    
        self.adjustSize()                       
        self.setWindowTitle( 'qgSurf - deformation of geosurfaces' )        
 

    def setup_main_tab( self ):
        
        simulWidget = QWidget()  
        simulLayout = QGridLayout( )

        simulToolBox = QToolBox()

        simulToolBox.addItem( self.setup_input_tb(), 
                                 "Input geosurface" )         
        simulToolBox.addItem( self.setup_deformation_tb(), 
                                 "Apply deformation" )
        simulToolBox.addItem( self.setup_visualization_tb(), 
                                 "Visualization" )
        simulToolBox.addItem( self.setup_output_tb(), 
                                 "Output" )
                
        simulLayout.addWidget( simulToolBox, 0, 0, 1, 2 )
                                                           
        simulWidget.setLayout(simulLayout)  
                
        return simulWidget 


    def setup_input_tb( self ):

        inputformWidget = QWidget()  
        inputformLayout = QGridLayout( ) 
      
        input_browse_QPushButton = QPushButton("Source file ...")
        input_browse_QPushButton.clicked.connect( self.select_input_file )
        inputformLayout.addWidget( input_browse_QPushButton, 0, 0, 1, 1 )
        
        self.input_filename_QLineEdit = QLineEdit()
        inputformLayout.addWidget( self.input_filename_QLineEdit, 0, 1, 1, 2 )
        
        load_geosurface_QPushButton = QPushButton( "Load geosurface" )
        load_geosurface_QPushButton.clicked[bool].connect( self.load_geosurface ) 
        load_geosurface_QPushButton.setEnabled( True )       
        inputformLayout.addWidget( load_geosurface_QPushButton, 2, 0, 1, 3 )
                
        inputformWidget.setLayout( inputformLayout )
        
        return inputformWidget
    
            
    def setup_deformation_tb( self ):        

        deformationWidget = QWidget()  
        deformationLayout = QGridLayout( ) 

        displacement_QPushButton = QPushButton( "Displacement" )
        displacement_QPushButton.clicked[bool].connect( self.do_displacement ) 
        displacement_QPushButton.setEnabled( True )       
        deformationLayout.addWidget( displacement_QPushButton, 0, 0, 1, 1 )

        rotation_QPushButton = QPushButton( "Rotation" )
        rotation_QPushButton.clicked[bool].connect( self.do_rotation ) 
        rotation_QPushButton.setEnabled( True )       
        deformationLayout.addWidget( rotation_QPushButton, 1, 0, 1, 1 )
                    
        scaling_QPushButton = QPushButton( "Scaling" )
        scaling_QPushButton.clicked[bool].connect( self.do_scaling ) 
        scaling_QPushButton.setEnabled( True )       
        deformationLayout.addWidget( scaling_QPushButton, 2, 0, 1, 1 )                    
                    
        hor_shear_QPushButton = QPushButton( "Simple shear (horizontal)" )
        hor_shear_QPushButton.clicked[bool].connect( self.do_horiz_shear ) 
        hor_shear_QPushButton.setEnabled( True )       
        deformationLayout.addWidget( hor_shear_QPushButton, 3, 0, 1, 1 )

        vert_shear_QPushButton = QPushButton( "Simple shear (vertical)" )
        vert_shear_QPushButton.clicked[bool].connect( self.do_vert_shear ) 
        vert_shear_QPushButton.setEnabled( True )       
        deformationLayout.addWidget( vert_shear_QPushButton, 4, 0, 1, 1 )
                                                            
        deformationWidget.setLayout( deformationLayout )
        
        return deformationWidget

        
    def setup_visualization_tb( self ):
        
        visualWidget = QWidget()  
        visualLayout = QGridLayout() 
        
        self.view_in_geosurface_QPushButton = QPushButton( "Plot input geosurface" )
        self.view_in_geosurface_QPushButton.clicked[bool].connect( self.view_geosurface ) 
        self.view_in_geosurface_QPushButton.setEnabled( True )       
        visualLayout.addWidget( self.view_in_geosurface_QPushButton, 0, 0, 1, 1 )         
        
        self.view_curr_geosurface_QPushButton = QPushButton( "Plot deformed surface" )
        self.view_curr_geosurface_QPushButton.clicked[bool].connect( self.view_geosurface ) 
        self.view_curr_geosurface_QPushButton.setEnabled( True )       
        visualLayout.addWidget( self.view_curr_geosurface_QPushButton, 1, 0, 1, 1 )                
        
        visualWidget.setLayout( visualLayout )
        
        return visualWidget
    
    
    def setup_output_tb( self ):
 
        outputWidget = QWidget()  
        outputLayout = QGridLayout( ) 

        outputLayout.addWidget( QLabel("Format: "), 0, 0, 1, 1 )

        self.save_as_grass_QRadioButton = QRadioButton( "Grass")
        self.save_as_grass_QRadioButton.setChecked ( True )
        outputLayout.addWidget( self.save_as_grass_QRadioButton, 0, 1, 1, 1 )
                         
        self.save_as_vtk_QRadioButton = QRadioButton( "VTK")
        outputLayout.addWidget( self.save_as_vtk_QRadioButton, 0, 2, 1, 1 )
        
        self.save_as_gas_QRadioButton = QRadioButton( "Gas (json)")
        outputLayout.addWidget( self.save_as_gas_QRadioButton, 0, 3, 1, 1 )
                      
        simulation_output_browse_QPushButton = QPushButton("Save as ...")
        simulation_output_browse_QPushButton.clicked.connect( self.select_output_file )
        outputLayout.addWidget( simulation_output_browse_QPushButton, 1, 0, 1, 1 )

        self.simulation_outputfilename_QLineEdit = QLineEdit()
        outputLayout.addWidget( self.simulation_outputfilename_QLineEdit, 1, 1, 1, 3 )
            
        self.save_surface_pButton = QPushButton( "Save surface" )
        self.save_surface_pButton.clicked[bool].connect( self.save_surface ) 
        self.save_surface_pButton.setEnabled( True )       
        outputLayout.addWidget( self.save_surface_pButton, 2, 0, 1, 4 )        
        
        outputWidget.setLayout( outputLayout )
        
        return outputWidget       
        

    def setup_help_tab( self ):
        
        helpWidget = QWidget()  
        helpLayout = QVBoxLayout( )
        
        htmlText = """
        <h3>Geosurface deformation help</h3>        
        
        Temporary help:
        see post "Creating and deforming analytical surfaces in Quantum GIS: experimental tools in qgSurf plugin" 
        in blog gisoftw.blogspot.com
        
        
        """
        
        helpQTextBrowser = QTextBrowser( helpWidget )        
        helpQTextBrowser.insertHtml( htmlText ) 
        helpLayout.addWidget( helpQTextBrowser )
        helpWidget.setLayout(helpLayout)  
                
        return helpWidget                 
        

    def select_input_file( self ):
            
        short_txt = "*.json"
        long_txt = "json (*.json *.JSON)"            
                                 
        input_filename = QFileDialog.getOpenFileName(self, 
                                                      self.tr( "Open file: " ), 
                                                      short_txt, 
                                                      long_txt )        
        if not input_filename:
            return

        self.input_filename_QLineEdit.setText( input_filename ) 
 
 
    def get_analytical_params( self, analytical_surface_dict ):

        try:       
            a_min = float( analytical_surface_dict['a min'] ) 
            a_max = float( analytical_surface_dict['a max'] )      
            grid_cols = int( analytical_surface_dict['grid cols'] )                                       
                   
            b_min = float( analytical_surface_dict['b min'] )      
            b_max = float( analytical_surface_dict['b max'] )
            grid_rows = int( analytical_surface_dict['grid rows'] ) 
            
            formula = str( analytical_surface_dict['formula'] )           
        except:
            raise AnaliticSurfaceIOException, "Check input analytical values"                     

        if a_min >= a_max or b_min >= b_max:
            raise AnaliticSurfaceIOException, "Check input a and b values" 

        if grid_cols <= 0 or grid_rows <= 0:
            raise AnaliticSurfaceIOException, "Check input grid column and row values"                 
        
        if formula == '':
            raise AnaliticSurfaceIOException, "Check input analytical formula"
        
        return (a_min,a_max,b_min,b_max), (grid_rows,grid_cols), formula        


    def get_geographical_params( self, geographic_params_dict ):
     
        try:            
            geog_x_min = float( geographic_params_dict['geog x min'] )        
            geog_y_min = float( geographic_params_dict['geog y min'] )        
            grid_length = float( geographic_params_dict['grid length'] )
            grid_width = float( geographic_params_dict['grid width'] )
            grid_rot_angle_degr = float( geographic_params_dict['grid rot angle degr'] )
        except:
            raise AnaliticSurfaceIOException, "Check input geographic values"            

        return (geog_x_min,geog_y_min), (grid_length,grid_width), grid_rot_angle_degr
                 

    def load_geosurface(self):
        
        input_gas_filepath = self.input_filename_QLineEdit.text()
        
        try:
            with open( input_gas_filepath, 'r' ) as infile:             
                input_geosurface = json.load( infile )
        except:
            QMessageBox.critical( self, "Surface import", "Check input file name" )
            return            
            
        self.source_analytical_params = input_geosurface['analytical surface']
        self.source_geographical_params = input_geosurface['geographical params']
        try:
            self.deformational_params = input_geosurface['deformational params']
        except:
            self.deformational_params = []
        
        try:
            self.current_analytical_params = self.get_analytical_params( self.source_analytical_params )
        except AnaliticSurfaceIOException, msg:
            QMessageBox.critical( self, "Surface import", str(msg) )
            return

        try:
            self.current_geographical_params = self.get_geographical_params( self.source_geographical_params )
        except AnaliticSurfaceIOException, msg:
            QMessageBox.critical( self, "Surface import", str(msg) )
            return

        try:
            self.input_geosurface = self.update_geosurface( self.current_analytical_params,
                                                            self.current_geographical_params,
                                                            self.deformational_params )
        except AnaliticSurfaceCalcException, msg:
            QMessageBox.critical( self, "Surface import", str(msg) )
        else:
            QMessageBox.information( self, "Surface load", "Done" ) 

        self.current_geosurface = None
        

    def update_geosurface(self, analytical_params, geographic_params, deformational_params):
                 
        try:               
            return calculate_geosurface( analytical_params, 
                                         geographic_params,
                                         deformational_params )
        except AnaliticSurfaceCalcException, msg:
            raise AnaliticSurfaceCalcException, msg
   

    def test_input_geosurface( self, header ):

        try:
            self.input_geosurface
            return True
        except:
            QMessageBox.critical( self, header,"No geosurface is loaded" )
            return False
            
        
    def do_displacement( self ):
        
        if not self.test_input_geosurface("Displacement"):  return
        
        self.displacement_window = geosurface_displacement_Dialog( )       
        QObject.connect( self.displacement_window, SIGNAL( "update_geosurface_for_displacement" ), self.update_displacement )
        self.displacement_window.show()
                          

    def do_rotation( self ):

        if not self.test_input_geosurface("Rotation"):  return        
            
        self.rotation_window = geosurface_rotation_Dialog( )       
        QObject.connect( self.rotation_window, SIGNAL( "update_geosurface_for_rotation" ), self.update_rotation )
        self.rotation_window.show()
        

    def do_scaling( self ):
        
        if not self.test_input_geosurface("Scaling"):  return        
           
        self.scaling_window = geosurface_scaling_Dialog( )       
        QObject.connect( self.scaling_window, SIGNAL( "update_geosurface_for_scaling" ), self.update_scaling )
        self.scaling_window.show()
        


    def do_horiz_shear( self ):
        
        if not self.test_input_geosurface("Simple shear (horizontal)"):  return        
         
        self.horiz_shear_window = geosurface_horiz_shear_Dialog( )       
        QObject.connect( self.horiz_shear_window, SIGNAL( "update_geosurface_for_horiz_shear" ), self.update_horiz_shear )
        self.horiz_shear_window.show()
        

    def do_vert_shear( self ):
        
        if not self.test_input_geosurface("Simple shear (vertical)"):  return        
         
        self.vert_shear_window = geosurface_vert_shear_Dialog( )       
        QObject.connect( self.vert_shear_window, SIGNAL( "update_geosurface_for_vert_shear" ), self.update_vert_shear )
        self.vert_shear_window.show()


    def update_displacement( self ):

        try:
            delta_x = float( self.displacement_window.delta_x_QLineEdit.text() )
            delta_y = float( self.displacement_window.delta_y_QLineEdit.text() )
            delta_z = float( self.displacement_window.delta_z_QLineEdit.text() )
        except:
            QMessageBox.critical( self, "Displacement", "Error in input values" )
            return             
                
        self.deformational_params.append( {'type':'displacement', 
                                           'parameters': {'delta_x' : delta_x, 'delta_y' : delta_y, 'delta_z' : delta_z } } )

        try:
            self.current_geosurface = self.update_geosurface( self.current_analytical_params,
                                                              self.current_geographical_params,
                                                              self.deformational_params )
        except AnaliticSurfaceCalcException, msg:
            QMessageBox.critical( self, "Surface displacement", str(msg) )
        else:
            QMessageBox.information( self, "Surface displacement", "Done" ) 


    def update_rotation( self ):
        
        try:
            rot_axis_trend = float( self.rotation_window.axis_trend_QdSpinBox.value() )
            rot_axis_plunge = float( self.rotation_window.axis_plunge_QdSpinBox.value() )
            rot_angle_degr = float( self.rotation_window.rotation_angle_QdSpinBox.value() )
        except:
            QMessageBox.critical( self, "Rotation", "Error in input values" )
            return          
        
        self.deformational_params.append( {'type':'rotation', 
                                           'parameters': {'rotation axis trend' : rot_axis_trend, 
                                                          'rotation axis plunge' : rot_axis_plunge, 
                                                          'rotation angle' : rot_angle_degr } } )

        try:
            self.current_geosurface = self.update_geosurface( self.current_analytical_params,
                                                              self.current_geographical_params,
                                                              self.deformational_params )
        except AnaliticSurfaceCalcException, msg:
            QMessageBox.critical( self, "Surface rotation", str(msg) )
        else:
            QMessageBox.information( self, "Surface rotation", "Done" ) 
        
 
    def update_scaling( self ):
        
        try:
            scale_factor_x = float( self.scaling_window.scale_x_QLineEdit.text() )
            scale_factor_y = float( self.scaling_window.scale_y_QLineEdit.text() )
            scale_factor_z = float( self.scaling_window.scale_z_QLineEdit.text() )
        except:
            QMessageBox.critical( self, "Scaling", "Error in input values" )
            return          
        
        if scale_factor_x == 0.0 or scale_factor_y == 0.0 or scale_factor_z == 0.0:
            QMessageBox.critical( self, "Scaling", "Input value(s) cannot be zero" )
            return
                
        self.deformational_params.append( {'type':'scaling', 
                                           'parameters': {'x factor' : scale_factor_x, 
                                                          'y factor' : scale_factor_y, 
                                                          'z factor' : scale_factor_z } } )

        try:
            self.current_geosurface = self.update_geosurface( self.current_analytical_params,
                                                              self.current_geographical_params,
                                                              self.deformational_params )
        except AnaliticSurfaceCalcException, msg:
            QMessageBox.critical( self, "Surface scaling", str(msg) )
        else:
            QMessageBox.information( self, "Surface scaling", "Done" ) 
            

    def update_horiz_shear( self ):
        
        try:
            phi_angle_degr = float( self.horiz_shear_window.phi_QLineEdit.text() )
            alpha_angle_degr = float( self.horiz_shear_window.alpha_QLineEdit.text() )
        except:
            QMessageBox.critical( self, "Simple shear (horizontal)", "Error in input values" )
            return          
        
        self.deformational_params.append( {'type':'simple shear - horizontal', 
                                           'parameters': {'phi angle (degr.)' : phi_angle_degr, 
                                                          'alpha angle (degr.)' : alpha_angle_degr } } )

        try:
            self.current_geosurface = self.update_geosurface( self.current_analytical_params,
                                                              self.current_geographical_params,
                                                              self.deformational_params )
        except AnaliticSurfaceCalcException, msg:
            QMessageBox.critical( self, "Surface simple shear (horiz.)", str(msg) )
        else:
            QMessageBox.information( self, "Surface simple shear (horiz.)", "Done" ) 
 
 
    def update_vert_shear( self ):
        
        try:
            phi_angle_degr = float( self.vert_shear_window.phi_QLineEdit.text() )
            alpha_angle_degr = float( self.vert_shear_window.alpha_QLineEdit.text() )
        except:
            QMessageBox.critical( self, "Simple shear (vertical)", "Error in input values" )
            return          
        
        self.deformational_params.append( {'type':'simple shear - vertical', 
                                           'parameters': {'phi angle (degr.)' : phi_angle_degr, 
                                                          'alpha angle (degr.)' : alpha_angle_degr } } )

        try:
            self.current_geosurface = self.update_geosurface( self.current_analytical_params,
                                                              self.current_geographical_params,
                                                              self.deformational_params )
        except AnaliticSurfaceCalcException, msg:
            QMessageBox.critical( self, "Surface simple shear (vert.)", str(msg) )
        else:
            QMessageBox.information( self, "Surface simple shear (vert.)", "Done" ) 

    
    def view_geosurface( self ):
 
        try:        
            if self.sender() == self.view_in_geosurface_QPushButton:
                geosurface = self.input_geosurface
            elif self.sender() == self.view_curr_geosurface_QPushButton:
                geosurface = self.current_geosurface
        except:
            QMessageBox.critical( self, "Surface deformation", "Geological surface not yet defined" )

        if geosurface:
            try:          
                view_surface( geosurface )
            except:
                QMessageBox.critical( self, "Surface view", "Unable to create plot. Try exporting as VTK/Grass and using Paraview or Grass for visualization" )                
        else:
            QMessageBox.critical( self, "Surface deformation", "Geological surface not yet defined" )
        
                
    def select_output_file( self ):
            
        if self.save_as_vtk_QRadioButton.isChecked():
            short_txt = "*.vtk"
            long_txt = "vtk (*.vtk *.VTK)"
        elif self.save_as_grass_QRadioButton.isChecked():
            short_txt = "*.txt"
            long_txt = "txt (*.txt *.TXT)"
        elif self.save_as_gas_QRadioButton.isChecked():
            short_txt = "*.json"
            long_txt = "json (*.json *.JSON)"             
                                 
        output_filename = QFileDialog.getSaveFileName(self, 
                                                      self.tr( "Save as" ), 
                                                      short_txt, 
                                                      long_txt )        
        if output_filename:
            self.simulation_outputfilename_QLineEdit.setText( output_filename )  


    def save_surface( self ):
        
        try:
            self.current_geosurface
        except AttributeError:
            QMessageBox.critical( self, "Surface saving", "Geosurface is not yet defined" )
            return            
  
        geodata = self.current_geosurface, self.current_analytical_params[1]        
        if self.save_as_vtk_QRadioButton.isChecked():
            save_function = save_surface_vtk
        elif self.save_as_grass_QRadioButton.isChecked():
            save_function = save_surface_grass            
        elif self.save_as_gas_QRadioButton.isChecked():
            save_function = save_surface_gas
            geodata = {'analytical surface': self.source_analytical_params,
                       'geographical params': self.source_geographical_params,
                       'deformational params': self.deformational_params }
                 
        try:   
            save_function( self.simulation_outputfilename_QLineEdit.text(), geodata )
        except:
            QMessageBox.critical( self, "Surface saving", "Error in saving data" )
        else:        
            QMessageBox.information( self, "Surface saving", "Done" )           
            
            
