
from builtins import map
from builtins import str
import os
from osgeo import ogr


from .errors import OGR_IO_Errors


def create_def_field( field_def ):
    
    fieldDef = ogr.FieldDefn( field_def['name'], field_def['ogr_type'] )
    if field_def['ogr_type'] == ogr.OFTString:
        fieldDef.SetWidth(field_def['width'] )
        
    return fieldDef
 

def create_shapefile(path, geom_type, fields_dict_list, crs = None, layer_name="layer"):
    
    """
    crs_prj4: projection in Proj4 text format
    geom_type = OGRwkbGeometryType: ogr.wkbPoint, ....  
    list of:  
        field dict: 'name', 
                    'type': ogr.OFTString,
                            ogr.wkbLineString, 
                            ogr.wkbLinearRing,
                            ogr.wkbPolygon,
                        
                    'width',    
    """
        
    driver = ogr.GetDriverByName("ESRI Shapefile")
    
    outShapefile = driver.CreateDataSource( str( path ) )
    if outShapefile is None:
        raise OGR_IO_Errors('Unable to save shapefile in provided path')

    if crs is not None:
        spatialReference = osr.SpatialReference()
        spatialReference.ImportFromProj4( crs )    
        outShapelayer = outShapefile.CreateLayer(layer_name, geom_type, spatialReference)
    else:
        outShapelayer = outShapefile.CreateLayer(layer_name, geom_type=geom_type)
        
    list(map(lambda field_def_params: outShapelayer.CreateField( create_def_field( field_def_params)), fields_dict_list))

    return outShapefile, outShapelayer


def open_shapefile( path, fields_dict_list ):
    
    driver = ogr.GetDriverByName("ESRI Shapefile")    
    
    dataSource = driver.Open( str( path ), 0 )
    
    if dataSource is None:
        raise OGR_IO_Errors('Unable to open shapefile in provided path')  
       
    point_shapelayer = dataSource.GetLayer()

    prev_solution_list = []
    in_point = point_shapelayer.GetNextFeature()
    while in_point:
        rec_id = int( in_point.GetField('id') )
        x = in_point.GetField('x')
        y = in_point.GetField('y')
        z = in_point.GetField('z')
        dip_dir = in_point.GetField('dip_dir') 
        dip_ang = in_point.GetField('dip_ang')
        descript = in_point.GetField('descript') 
        prev_solution_list.append( [ rec_id,x,y,z,dip_dir,dip_ang,descript ] )         
        in_point.Destroy()
        in_point = point_shapelayer.GetNextFeature()    
    
    #point_shapelayer.Destroy()
    dataSource.Destroy()
    
    if os.path.exists( path ):
        driver.DeleteDataSource( str( path ) )
    
    outShapefile, outShapelayer = create_shapefile( path, ogr.wkbPoint, fields_dict_list, crs = None, layer_name="layer" )
    return outShapefile, outShapelayer, prev_solution_list
        






    
    
    
    
    
        