# -*- coding: utf-8 -*-


from ..defaults.typing import Tuple

from ..mathematics.defaults import *

from ..spatial.rasters.geoarray import GeoArray
from ..spatial.rasters.fields import *
from ..spatial.vectorial.vectorial import Point

from ..orientations.orientations import Plane


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

    # grid cell sizes along x- and y-directions

    cell_size_x = geo_array.cellsize_x
    cell_size_y = geo_array.cellsize_y

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

    """
    # 2D array of DEM segment parameters

    grid_m_along_x = grad_x(
        fld=q_d,
        cell_size_x=cell_size_x)

    grid_q_along_x = q_d - grid_m_along_x * x

    grid_m_along_y = grad_y(
        fld=q_d,
        cell_size_y=cell_size_y)

    grid_q_along_y = q_d - grid_m_along_y * y
    """

    # closures to compute the geographic coordinates (in x- and y-) of a cell center
    # the grid coordinates of the cell center are expressed by i and j

    #closure_grid_coord_to_geogr_coord_x = lambda j: geo_array.domain.llcorner.x + cell_size_x * (0.5 + j)
    #closure_grid_coord_to_geogr_coord_y = lambda i: geo_array.domain.trcorner.y - cell_size_y * (0.5 + i)

    """
    # 2D arrays of plane segment parameters

    plane_m_along_x = srcPlaneAttitude.slope_x_dir()
    plane_q_along_x = np.fromfunction(
        lambda i, j: plane_z_closure(0, closure_grid_coord_to_geogr_coord_y(i)),
        (row_num, 1))

    # 2D array of plane segment parameters

    plane_m_along_y = srcPlaneAttitude.slope_y_dir()
    plane_q_along_y = np.fromfunction(
        lambda i, j: plane_z_closure(closure_grid_coord_to_geogr_coord_x(j), 0),
        (1, col_num))
    """

    # 2D arrays that define denominators for intersections between local segments

    x_inters_denomin = np.where(grid_m_along_x != plane_m_along_x, grid_m_along_x - plane_m_along_x, np.NaN)

    coincident_x = np.where(grid_q_along_x != plane_q_along_x, np.NaN, ycoords_x)

    xcoords_x = np.where(grid_m_along_x != plane_m_along_x, (plane_q_along_x - grid_q_along_x) / x_inters_denomin, coincident_x)
    xcoords_x = np.where(xcoords_x < ycoords_x, np.NaN, xcoords_x)
    xcoords_x = np.where(xcoords_x >= ycoords_x + cell_size_x, np.NaN, xcoords_x)

    y_inters_denomin = np.where(grid_m_along_y != plane_m_along_y, grid_m_along_y - plane_m_along_y, np.NaN)
    coincident_y = np.where(grid_q_along_y != plane_q_along_y, np.NaN, xcoords_y)

    ycoords_y = np.where(grid_m_along_y != plane_m_along_y, (plane_q_along_y - grid_q_along_y) / y_inters_denomin, coincident_y)

    # filtering out intersections outside of cell range

    ycoords_y = np.where(ycoords_y < xcoords_y, np.NaN, ycoords_y)
    ycoords_y = np.where(ycoords_y >= xcoords_y + cell_size_y, np.NaN, ycoords_y)

    for i in range(xcoords_x.shape[0]):
        for j in range(xcoords_x.shape[1]):
            if abs(xcoords_x[i, j] - ycoords_x[i, j]) < MIN_SEPARATION_THRESHOLD and abs(
                    ycoords_y[i, j] - xcoords_y[i, j]) < MIN_SEPARATION_THRESHOLD:
                ycoords_y[i, j] = np.NaN

    return xcoords_x, xcoords_y, ycoords_x, ycoords_y

