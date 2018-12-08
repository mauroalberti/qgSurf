# -*- coding: utf-8 -*-


from ..spatial.rasters.geoarray import GeoArray
from ..spatial.rasters.fields import *
from ..spatial.vectorial.vectorial import Point, Segment

from ..orientations.orientations import Plane



def ij2pt(plane_clos: Callable, ij2xy: Callable, i: int, j: int) -> Point:
    """
    Return a point located onto a plane, starting by array indices.

    :param plane_clos: a closure representing the plane.
    :param ij2xy: a function converting from array coordinates to geographic coordinates.
    :param i: i index of point.
    :param j: j index of point.
    :return: Point
    """

    x, y = ij2xy(i, j)
    z = plane_clos(x, y)
    return Point(x, y, z)


def plane_slope(plane_closure: Callable, arrij2xy: Callable, i: int, j: int) -> float:
    """
    Calculates the plane slope along a gridded direction defined by its end point i, j array coordinates.
    Start point is array coordinates 0, 0.

    :param plane_closure: a closure representing the plane.
    :param arrij2xy: a function converting from array coordinates to geographic coordinates.
    :param i: i index of end point.
    :param j: j index of end point.
    :return: slope along the plane.
    :rtype: float.
    """

    start_point = ij2pt(plane_closure, arrij2xy, 0, 0)
    end_point = ij2pt(plane_closure, arrij2xy, i, j)

    return Segment(start_point, end_point).slope


def topo_plane_intersection(srcPlaneAttitude: Plane, srcPt: Point, geo_array: GeoArray, level_ndx: int=0) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculates the intersections (as points) between the grid and a planar analytical surface.

    :param srcPlaneAttitude: orientation of the surface (currently only planes).
    :type srcPlaneAttitude: class Plane.
    :param srcPt: point, expressed in geographical coordinates, that the plane must contain.
    :type srcPt: Point.
    :param geo_array: the input GeoArray storing the used grid.
    :type geo_array: GeoArray.
    :param level_ndx: the grid level to use from the provided geoarray. Default is first (index equal to zero).
    :type level_ndx: integer.

    :return: tuple of four Numpy arrays

    Examples:
    """

    # the numeric values of the grid stored in a Numpy array

    q_d = geo_array.level(
        level_ndx=level_ndx)

    # row and column numbers of the grid

    row_num, col_num = q_d.shape

    # arrays storing the geographical coordinates of the cell centers along the x- and y- axes

    x, y = geo_array.xy(level_ndx)

    # closure for the planar surface that, given (x, y), will be used to derive z

    plane_z_closure = srcPlaneAttitude.closure_plane_from_geo(srcPt)

    # plane elevations at grid cell centers

    q_p = array_from_function(
        row_num=row_num,
        col_num=col_num,
        geotransform=geo_array.gt,
        z_transfer_func=plane_z_closure)

    index_multiplier = 100  # large value to ensure correct slope values 
    
    mi_p = plane_slope(
        plane_closure=plane_z_closure, 
        arrij2xy=geo_array.ijArrToxy, 
        i=index_multiplier, 
        j=0)
    
    mj_p = plane_slope(
        plane_closure=plane_z_closure, 
        arrij2xy=geo_array.ijArrToxy, 
        i=0, 
        j=index_multiplier)

    # 2D array of DEM segment parameters

    cell_size_j, cell_size_i = geo_array.geotransf_cell_sizes()

    mj_d = grad_j(
        fld=q_d,
        cell_size_j=cell_size_j)

    mi_g = grad_iminus(
        fld=q_d,
        cell_size_i=cell_size_i)

    # 2D arrays that define denominators for intersections between local segments

    j_coords_inters = np.where(abs(mj_d - mj_p) < 1e-6, np.NaN, (q_p - q_d) / (cell_size_j*(mj_d - mj_p)))
    j_coords_inters = np.where(abs(q_d - q_p) < 1e-6, 0.0, j_coords_inters)
    j_coords_inters = np.where(0.0 <= j_coords_inters < 1.0, j_coords_inters, np.NaN)











    i_inters_denomin = np.where(mi_g != mi_p, mi_g - mi_p, np.NaN)




    j_coords_inters = np.where(j_coords_inters < x, np.NaN, j_coords_inters)
    j_coords_inters = np.where(j_coords_inters >= x + cell_size_j, np.NaN, j_coords_inters)

    coincident_y = np.where(q_d != q_p, np.NaN, y)

    i_coords_y = np.where(mi_g != mi_p, (q_p - q_d) / i_inters_denomin, coincident_y)

    # filtering out intersections outside of cell range

    i_coords_y = np.where(i_coords_y < y, np.NaN, i_coords_y)
    i_coords_y = np.where(i_coords_y >= y + cell_size_i, np.NaN, i_coords_y)

    for i in range(j_coords_inters.shape[0]):
        for j in range(j_coords_inters.shape[1]):
            if abs(j_coords_inters[i, j] - x[i, j]) < MIN_SEPARATION_THRESHOLD and abs(
                    i_coords_y[i, j] - y[i, j]) < MIN_SEPARATION_THRESHOLD:
                i_coords_y[i, j] = np.NaN

    return j_coords_inters, y, x, i_coords_y

