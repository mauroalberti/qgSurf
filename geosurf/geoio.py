# -*- coding: utf-8 -*-


from __future__  import division

from math import *

from osgeo import gdal
from osgeo.gdalconst import *

try:
    from osgeo import ogr
except: 
    import ogr

from errors import Raster_Parameters_Errors
from spatial import *
   


def read_raster_band( raster_name ):
    """
    Read an input raster band, based on GDAL module.
    
    @param raster_name: name of the raster to be read.
    @type raster_name: QString.
    
    @return: tuple of a GDALParameters instance and a 2D numpy.array instance. 
    
    @raise IOError: unable to open or read data from raster.
    @raise TypeError: more than one band in raster.    
    """
            
    # GDAL register
    gdal.AllRegister
    
    # open raster file and check operation success 
    raster_data = gdal.Open( str( raster_name ), GA_ReadOnly )    
    if raster_data is None:
        raise IOError, 'Unable to open raster band' 

    # initialize DEM parameters
    raster_params = GDALParameters()
    
    # get driver type for current raster 
    raster_params.driverShortName = raster_data.GetDriver().ShortName

    # get current raster projection
    raster_params.projection = raster_data.GetProjection()   

    # get row and column numbers    
    raster_params.rows = raster_data.RasterYSize
    raster_params.cols = raster_data.RasterXSize
    
    # get and check number of raster bands - it must be one
    raster_bands = raster_data.RasterCount
    if raster_bands > 1:
        raise TypeError, 'More than one raster band in raster' 
    
    # set critical grid values from geotransform array
    raster_params.topLeftX = raster_data.GetGeoTransform()[0]
    raster_params.pixSizeEW = raster_data.GetGeoTransform()[1]
    raster_params.rotGT2 = raster_data.GetGeoTransform()[2]
    raster_params.topLeftY = raster_data.GetGeoTransform()[3]
    raster_params.rotGT4 = raster_data.GetGeoTransform()[4]
    raster_params.pixSizeNS = raster_data.GetGeoTransform()[5]
 
    # get single band 
    band = raster_data.GetRasterBand(1)
    
    # get no data value for current band
    try: 
        raster_params.noDataValue = band.GetNoDataValue()
    except:
        pass
    # read data from band 
    grid_values = band.ReadAsArray( 0, 0, raster_params.cols, raster_params.rows )
    if grid_values is None:
        raise IOError, 'Unable to read data from raster'
     
    # transform data into numpy array
    data = np.asarray( grid_values ) 

    # if nodatavalue exists, set null values to NaN in numpy array
    if raster_params.noDataValue is not None:
        data = np.where( abs( data - raster_params.noDataValue ) > 1e-05, data, np.NaN ) 

    return raster_params, data


def read_dem( in_dem_fn ):
    """
    Read input DEM file.

    @param  in_dem_fn: name of file to be read.
    @type  in_dem_fn:  string
    
    """
            
    # try reading DEM data
    try:
        dem_params, dem_array = read_raster_band( in_dem_fn )
        dem_params.check_params()
    except ( IOError, TypeError, Raster_Parameters_Errors ), e:                    
        raise IOError, 'Unable to read data from raster'
           
    # create current grid
    return Grid(in_dem_fn, dem_params, dem_array)
    
               
def read_line_shapefile( line_shp_path ):
    """
    Read line shapefile.

    @param  line_shp_path:  parameter to check.
    @type  line_shp_path:  QString or string
    
    """       
    # reset layer parameters 
  
    if line_shp_path is None or line_shp_path == '':            
        return False, 'No input path' 

    # open input vector layer
    shape_driver = ogr.GetDriverByName( "ESRI Shapefile" )

    line_shape = shape_driver.Open( str( line_shp_path ), 0 )

    # layer not read
    if line_shape is None: 
        return False, 'Unable to open input shapefile'
     
    # get internal layer
    lnLayer = line_shape.GetLayer(0)          
            
    # set vector layer extent   
    layer_extent = lnLayer.GetExtent()
    lineaments_extent={}
    lineaments_extent['xmin'], lineaments_extent['xmax'] = layer_extent[0], layer_extent[1]
    lineaments_extent['ymin'], lineaments_extent['ymax'] = layer_extent[2], layer_extent[3]    
                    
    lines_x, lines_y = [], []

    # start reading layer features        
    curr_line = lnLayer.GetNextFeature()
            
    # loop in layer features                 
    while curr_line:        

        line_vert_x, line_vert_y = [], []
                    
        line_geom = curr_line.GetGeometryRef()

        if line_geom is None:
            line_shape.Destroy()           
            return False, 'No geometry ref'               

        if line_geom.GetGeometryType() != ogr.wkbLineString and \
           line_geom.GetGeometryType() != ogr.wkbMultiLineString:                        
            line_shape.Destroy()           
            return False, 'Not a linestring/multilinestring'

        for i in range( line_geom.GetPointCount() ):
                            
            x, y = line_geom.GetX(i), line_geom.GetY(i)
            
            line_vert_x.append(x)
            line_vert_y.append(y)

        lines_x.append(line_vert_x)    
        lines_y.append(line_vert_y)
                    
        curr_line = lnLayer.GetNextFeature()

    line_shape.Destroy()
    
    return True, dict( extent=lineaments_extent, data=dict(x=lines_x, y=lines_y) )
       
