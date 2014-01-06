
from PyQt4.QtCore import *
from PyQt4.QtGui import *


class geosurface_displacement_Dialog( QDialog ):

    def __init__( self ):

        super( geosurface_displacement_Dialog, self ).__init__() 
  
        displLayout = QGridLayout( )                            
                        
        displLayout.addWidget( QLabel("X offset"), 0, 0, 1, 1 )             
        self.delta_x_QLineEdit = QLineEdit()
        displLayout.addWidget( self.delta_x_QLineEdit, 0, 1, 1, 1 )

        displLayout.addWidget( QLabel("Y offset"), 1, 0, 1, 1 )             
        self.delta_y_QLineEdit = QLineEdit()
        displLayout.addWidget( self.delta_y_QLineEdit, 1, 1, 1, 1 )
        
        displLayout.addWidget( QLabel("Z offset"), 2, 0, 1, 1 )             
        self.delta_z_QLineEdit = QLineEdit()
        displLayout.addWidget( self.delta_z_QLineEdit, 2, 1, 1, 1 )          

        done_QPushButton = QPushButton( "Apply" )
        done_QPushButton.clicked[bool].connect( self.displacement_done ) 
        done_QPushButton.setEnabled( True ) 
              
        displLayout.addWidget( done_QPushButton, 3, 0, 1, 2 )
                                                                         
        self.setLayout( displLayout )         
        self.adjustSize()                       
        self.setWindowTitle( 'Geosurface displacement' ) 
         
        
    def displacement_done( self, dummy_var ):        

        self.emit( SIGNAL( "update_geosurface_for_displacement" ) )                       
        self.close()
        
 

class geosurface_rotation_Dialog( QDialog ):

    def __init__( self ):

        super( geosurface_rotation_Dialog, self ).__init__() 
  
        displLayout = QGridLayout( )                            
                        
        displLayout.addWidget( QLabel("Rotation axis"), 0, 0, 1, 2 )             

        displLayout.addWidget( QLabel(" - trend"), 1, 0, 1, 1 )             
        self.axis_trend_QdSpinBox = QDoubleSpinBox()
        self.axis_trend_QdSpinBox.setMaximum( 360.0 )
        self.axis_trend_QdSpinBox.setSingleStep( 0.1 )        
        displLayout.addWidget( self.axis_trend_QdSpinBox, 1, 1, 1, 1 )

        displLayout.addWidget( QLabel(" - plunge"), 2, 0, 1, 1 )             
        self.axis_plunge_QdSpinBox = QDoubleSpinBox()
        self.axis_plunge_QdSpinBox.setMinimum( -90.0 )
        self.axis_plunge_QdSpinBox.setMaximum( 90.0 )
        self.axis_plunge_QdSpinBox.setSingleStep( 0.1 )        
        displLayout.addWidget( self.axis_plunge_QdSpinBox, 2, 1, 1, 1 )
                
        displLayout.addWidget( QLabel("Rotation angle"), 3, 0, 1, 1 )             
        self.rotation_angle_QdSpinBox = QDoubleSpinBox()
        self.rotation_angle_QdSpinBox.setMinimum( -360.0 )
        self.rotation_angle_QdSpinBox.setMaximum( 360.0 )
        self.rotation_angle_QdSpinBox.setSingleStep( 0.1 )        
        displLayout.addWidget( self.rotation_angle_QdSpinBox, 3, 1, 1, 1 )          

        done_QPushButton = QPushButton( "Apply" )
        done_QPushButton.clicked[bool].connect( self.rotation_done ) 
        done_QPushButton.setEnabled( True ) 
              
        displLayout.addWidget( done_QPushButton, 4, 0, 1, 2 )
                                                                         
        self.setLayout( displLayout )         
        self.adjustSize()                       
        self.setWindowTitle( 'Geosurface rotation' ) 
         
        
    def rotation_done( self, dummy_var ):        

        self.emit( SIGNAL( "update_geosurface_for_rotation" ) )                       
        self.close()
   
   

class geosurface_scaling_Dialog( QDialog ):

    def __init__( self ):

        super( geosurface_scaling_Dialog, self ).__init__() 
  
        scalingLayout = QGridLayout( )                            

        scalingLayout.addWidget( QLabel("Scale factors"), 0, 0, 1, 2 )
                                
        scalingLayout.addWidget( QLabel("X"), 1, 0, 1, 1 )             
        self.scale_x_QLineEdit = QLineEdit()
        scalingLayout.addWidget( self.scale_x_QLineEdit, 1, 1, 1, 1 )

        scalingLayout.addWidget( QLabel("Y"), 2, 0, 1, 1 )             
        self.scale_y_QLineEdit = QLineEdit()
        scalingLayout.addWidget( self.scale_y_QLineEdit, 2, 1, 1, 1 )
        
        scalingLayout.addWidget( QLabel("Z"), 3, 0, 1, 1 )             
        self.scale_z_QLineEdit = QLineEdit()
        scalingLayout.addWidget( self.scale_z_QLineEdit, 3, 1, 1, 1 )          

        done_QPushButton = QPushButton( "Apply" )
        done_QPushButton.clicked[bool].connect( self.scaling_done ) 
        done_QPushButton.setEnabled( True ) 
              
        scalingLayout.addWidget( done_QPushButton, 4, 0, 1, 2 )
                                                                         
        self.setLayout( scalingLayout )         
        self.adjustSize()                       
        self.setWindowTitle( 'Geosurface scaling' ) 
         
 
    def scaling_done( self, dummy_var ):        

        self.emit( SIGNAL( "update_geosurface_for_scaling" ) )                       
        self.close()
 
 
class geosurface_horiz_shear_Dialog( QDialog ):
     
    def __init__( self ):

        super( geosurface_horiz_shear_Dialog, self ).__init__() 
  
        simpleshear_horizLayout = QGridLayout( )                            
                    
        simpleshear_horizLayout.addWidget( QLabel("Psi angle (degr.)"), 0, 0, 1, 1 )             
        self.phi_QLineEdit = QLineEdit()
        simpleshear_horizLayout.addWidget( self.phi_QLineEdit, 0, 1, 1, 1 )

        simpleshear_horizLayout.addWidget( QLabel("Alpha angle (degr.)"), 1, 0, 1, 1 )             
        self.alpha_QLineEdit = QLineEdit()
        simpleshear_horizLayout.addWidget( self.alpha_QLineEdit, 1, 1, 1, 1 )

        done_QPushButton = QPushButton( "Apply" )
        done_QPushButton.clicked[bool].connect( self.horiz_shear_done ) 
        done_QPushButton.setEnabled( True ) 
              
        simpleshear_horizLayout.addWidget( done_QPushButton, 2, 0, 1, 2 )
                                                                         
        self.setLayout( simpleshear_horizLayout )         
        self.adjustSize()                       
        self.setWindowTitle( 'Geosurface simple shear (horiz.)' ) 
         
 
    def horiz_shear_done( self, dummy_var ):        

        self.emit( SIGNAL( "update_geosurface_for_horiz_shear" ) )                       
        self.close()
        
             
class geosurface_vert_shear_Dialog( QDialog ):
     
    def __init__( self ):

        super( geosurface_vert_shear_Dialog, self ).__init__() 
  
        simpleshear_vertLayout = QGridLayout( )                            
                    
        simpleshear_vertLayout.addWidget( QLabel("Psi angle (degr.)"), 0, 0, 1, 1 )             
        self.phi_QLineEdit = QLineEdit()
        simpleshear_vertLayout.addWidget( self.phi_QLineEdit, 0, 1, 1, 1 )

        simpleshear_vertLayout.addWidget( QLabel("Alpha angle (degr.)"), 1, 0, 1, 1 )             
        self.alpha_QLineEdit = QLineEdit()
        simpleshear_vertLayout.addWidget( self.alpha_QLineEdit, 1, 1, 1, 1 )

        done_QPushButton = QPushButton( "Apply" )
        done_QPushButton.clicked[bool].connect( self.vert_shear_done ) 
        done_QPushButton.setEnabled( True ) 
              
        simpleshear_vertLayout.addWidget( done_QPushButton, 2, 0, 1, 2 )
                                                                         
        self.setLayout( simpleshear_vertLayout )         
        self.adjustSize()                       
        self.setWindowTitle( 'Geosurface simple shear (vert.)' ) 
         
 
    def vert_shear_done( self, dummy_var ):        

        self.emit( SIGNAL( "update_geosurface_for_vert_shear" ) )                       
        self.close()
        
                   
        