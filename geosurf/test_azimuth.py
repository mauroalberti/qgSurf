
from __future__  import division

from math import sqrt, floor, ceil, pi, sin, cos, tan, radians, asin, acos, atan, atan2, degrees


import numpy as np

class Point_2D( object ):
    
    def __init__(self, x = np.nan, y = np.nan ):
        
        self._x = x
        self._y = y
    

    def copy(self):
        
        return Point_2D( self._x, self._y )
    
    
    def distance(self, another ):
        
        return sqrt( (self._x - another._x)**2 + (self._y - another._y)**2 )
    
    
    def to_3D( self, z = 0.0 ):
        
        return Point_3D( self._x, self._y, z )
    

    def displaced_by_vector(self, displacement_vector ):
        
        return Point_2D( self._x + displacement_vector._x , self._y + displacement_vector._y )
        

    def is_coincident_with( self, another, tolerance = 1.0e-7 ):
        
        if self.distance(another) > tolerance:
            return False
        else:
            return True


    def azimuth_degr( self ):
        
        pt_atan2 = atan2( self._y, self._x )
        
        az = degrees( pi/2.0 - pt_atan2 )
        if az < 0:
            az = 360.0 + az
            
        return az        



if __name__ == "__main__":
    
    test_values = [ Point_2D(1,1), Point_2D(1000,1000), Point_2D(-1000,-1000), Point_2D(1000,-1000), Point_2D(-1000,1000) ]
    
    for test_value in test_values:
        print test_value.azimuth_degr()
        
        
        