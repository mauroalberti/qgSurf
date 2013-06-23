# -*- coding: utf-8 -*-


from math import sin, cos, tan, radians



class Axis( object ):
    """
    Structural axis,
    defined by trend and plunge (both in degrees)
    """
    
    def __init__(self, srcTrend, srcPlunge ):
        self._trend = float( srcTrend )
        self._plunge = float( srcPlunge )        
        
     
    def to_down_axis( self ): 
        
        trend = self._trend
        plunge = self._plunge
        if plunge < 0.0:
            trend += 180.0
            if trend > 360.0: trend -= 360.0
            plunge = - plunge
        
        return Axis( trend, plunge )

    def to_normal_structplane( self ):
        
        down_axis = self.to_down_axis()
        
        dipdir = down_axis._trend - 180.0
        if dipdir < 0.0: dipdir += 360.0
        dipangle = 90.0 - down_axis._plunge
        
        return StructPlane( dipdir, dipangle ) 


class StructPlane(object):
    """
    Structural plane, following geological conventions:
    dip direction and dip angle.
    
    """
    
    def __init__( self, srcDipDir, srcDipAngle ):
        """
        Class constructor
        
        @param  srcDipDir:  Dip direction of the plane (0-360�).
        @type  srcDipDir:  number or string convertible to float.
        @param  srcDipAngle:  Dip angle of the plane (0-90�).
        @type  srcDipAngle:  number or string convertible to float.
           
        @return:  StructPlane.
    
        """
        
        self._dipdir = float( srcDipDir )
        self._dipangle = float( srcDipAngle )
  

    def plane_x_coeff( self ):
        """
        Calculate the slope of a given plane along the x direction.
        The plane orientation  is expressed following the geological convention. 
               
        @return:  slope - float.    
        """ 
        return - sin( radians( self._dipdir ) ) * tan( radians( self._dipangle ) )


    def plane_y_coeff( self ):
        """
        Calculate the slope of a given plane along the y direction.
        The plane orientation  is expressed following the geological convention. 
               
        @return:  slope - float.     
        """ 
        return - cos( radians( self._dipdir ) ) * tan( radians( self._dipangle ) )

       
    def plane_from_geo( self, or_Pt ):
        """
        Closure that embodies the analytical formula for the given plane.
        This closure is used to calculate the z value from given horizontal coordinates (x, y).
    
        @param  or_Pt:  Point instance expressing a location point contained by the plane.
        @type  or_Pt:  Point.    
        
        @return:  lambda (closure) expressing an analytical formula for deriving z given x and y values.    
        """
    
        x0 =  or_Pt.x     
        y0 =  or_Pt.y
        z0 =  or_Pt.z
    
        # slope of the line parallel to the x axis and contained by the plane
        a = self.plane_x_coeff(  ) 
               
        # slope of the line parallel to the y axis and contained by the plane    
        b = self.plane_y_coeff(  )
                        
        return lambda x, y : a * ( x - x0 )  +  b * ( y - y0 )  +  z0
    
    

  
