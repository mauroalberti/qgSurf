# -*- coding: utf-8 -*-


from math import radians, sin, cos
import json

from numpy import *  # general import for compatibility with formula input

from .exceptions import *
from .vectorial import Segment
from ...mathematics.scalars import areClose
from ...mathematics.transformations import deformMatrices
from ...libs_utils.gdal.ogr import *


def formula_to_grid(array_range, array_size, formula):
    """
    Todo: check usages and correctness

    :param array_range:
    :param array_size:
    :param formula:
    :return: three lists of float values
    """

    a_min, a_max, b_max, b_min = array_range  # note: b range reversed for conventional j order in arrays
    array_rows, array_cols = array_size

    a_array = linspace(a_min, a_max, num=array_cols)
    b_array = linspace(b_max, b_min, num=array_rows)  # note: reversed for conventional j order in arrays

    try:
        a_list, b_list = [a for a in a_array for _ in b_array], [b for _ in a_array for b in b_array]
    except:
        raise AnaliticSurfaceCalcException("Error in a-b values")

    try:
        z_list = [eval(formula) for a in a_array for b in b_array]
    except:
        raise AnaliticSurfaceCalcException("Error in applying formula to a and b array values")

    return a_list, b_list, z_list


class TriangBeam(object):
    """
    represents a 'fascio', a 2D semi-infinite geometrical object,
    defined by an apex (a Point object) and two semi-infinite segments, originating
    from the apex and defined by two versors (Vect objects, with init name 'versor_1' and 'versor_2').
    Its maximum width
    """

    def __init__(self, apex_pt3d, vector_1, vector_2):
        """

        :param apex_pt3d:
        :param vector_1:
        :param vector_2:
        """
        """
        assert almost_zero(versor_1.length() - 1.0)
        assert almost_zero(versor_2.length() - 1.0)
        """

        self._apex = apex_pt3d
        self._versor_1 = vector_1.versor_full()
        self._versor_2 = vector_2.versor_full()

    def fangle_degr(self):
        """
        angle 'sotteso' by the 'fascio'
        in the 0 - 180 degrees range
        """

        return self._versor_1.angle_degr(self._versor_2)

    def point_fangles_degr(self, pt_3d):
        """

        :param pt_3d:
        :return:
        """
        """
        angles
        """

        vector_pt = Segment(self._apex, pt_3d).vector()

        angle_side_1 = self._versor_1.angle_degr(vector_pt)
        angle_side_2 = self._versor_2.angle_degr(vector_pt)

        return angle_side_1, angle_side_2

    def is_within_fascio(self, pt_3d):
        """

        :param pt_3d:
        :return:
        """

        apertura = self.fangle_degr()

        assert apertura < 180.0

        ang1, ang2 = self.point_fangles_degr(pt_3d)
        angle_sum = ang1 + ang2

        return areClose(apertura, angle_sum)


class CartesianTriangle(object):

    def __init__(self, pt_3d_1, pt_3d_2, pt_3d_3):
        """

        :param pt_3d_1:
        :param pt_3d_2:
        :param pt_3d_3:
        """

        self._pt_1 = pt_3d_1
        self._pt_2 = pt_3d_2
        self._pt_3 = pt_3d_3

    def is_pt_within(self, pt_3d):
        """

        :param pt_3d:
        :return:
        """

        def versor3d(pt_1, pt_2):
            """

            :param pt_1:
            :param pt_2:
            :return:
            """

            return Segment(pt_1, pt_2).vector().versor_full()

        def is_pt_in_fascio(pt_1, pt_2, pt_3):
            """

            :param pt_1:
            :param pt_2:
            :param pt_3:
            :return:
            """

            apex = pt_1
            versor_1 = versor3d(pt_1, pt_2)
            versor_2 = versor3d(pt_1, pt_3)

            fascio = TriangBeam(apex, versor_1, versor_2)
            if not fascio.is_within_fascio(pt_3d):
                return False
            else:
                return True

        if not (is_pt_in_fascio(self._pt_1, self._pt_2, self._pt_3) and
                    is_pt_in_fascio(self._pt_2, self._pt_1, self._pt_3)):
            return False
        else:
            return True


class AnalyticGeosurface(object):

    def __init__(self, analytical_params, geogr_params, deform_params):
        """

        :param analytical_params:
        :param geogr_params:
        :param deform_params:
        """

        self.analytical_params = analytical_params
        self.geographical_params = geogr_params
        self.deformational_params = deform_params

        # extract array params
        self.anal_param_values = self.get_analytical_param_values()
        array_range, array_size, formula = self.anal_param_values
        a_min, a_max, b_min, b_max = array_range
        a_range, b_range = a_max - a_min, b_max - b_min

        # calculate array from formula
        try:
            self.X, self.Y, self.Z = formula_to_grid(array_range, array_size, formula)
        except AnaliticSurfaceCalcException as msg:
            raise AnaliticSurfaceCalcException(msg)

        # calculate geographic transformations to surface
        self.geographical_values = self.get_geographical_param_values()
        (geog_x_min, geog_y_min), (area_height, area_width), area_rot_ang_deg = self.geographical_values
        geog_scale_matr = geographic_scale_matrix(a_range, b_range, area_height, area_width)
        geogr_rot_matrix = geographic_rotation_matrix(area_rot_ang_deg)

        self.geographic_transformation_matrix = dot(geogr_rot_matrix, geog_scale_matr)

        self.geographic_offset_matrix = geographic_offset(self.geographic_transformation_matrix,
                                                          array([a_min, b_min, 0.0]),
                                                          array([geog_x_min, geog_y_min, 0.0]))

        # apply total transformations to grid points
        self.deformations = deformMatrices(self.deformational_params)

    def geosurface_center(self):
        """

        :return:
        """

        array_range, _, _ = self.anal_param_values
        a_min, a_max, b_min, b_max = array_range

        x = (a_min + a_max) / 2.0
        y = (b_min + b_max) / 2.0
        z = (min(self.Z) + max(self.Z)) / 2.0

        return self.transform_loc(x, y, z)

    def geosurface_XYZ(self):
        """

        :return:
        """

        geosurface_X = []
        geosurface_Y = []
        geosurface_Z = []

        for x, y, z in zip(self.X, self.Y, self.Z):
            pt = self.transform_loc(x, y, z)
            geosurface_X.append(pt[0])
            geosurface_Y.append(pt[1])
            geosurface_Z.append(pt[2])

        return geosurface_X, geosurface_Y, geosurface_Z

    def get_analytical_param_values(self):
        """

        :return:
        """

        try:
            a_min = float(self.analytical_params['a min'])
            a_max = float(self.analytical_params['a max'])
            grid_cols = int(self.analytical_params['grid cols'])

            b_min = float(self.analytical_params['b min'])
            b_max = float(self.analytical_params['b max'])
            grid_rows = int(self.analytical_params['grid rows'])

            formula = str(self.analytical_params['formula'])
        except:
            raise AnaliticSurfaceIOException("Analytical value error")

        if a_min >= a_max or b_min >= b_max:
            raise AnaliticSurfaceIOException("Input a and b value error")

        if grid_cols <= 0 or grid_rows <= 0:
            raise AnaliticSurfaceIOException("Raster column/row value error")

        if formula == '':
            raise AnaliticSurfaceIOException("Input analytical formula error")

        return (a_min, a_max, b_min, b_max), (grid_rows, grid_cols), formula

    def get_geographical_param_values(self):
        """

        :return:
        """

        try:
            geog_x_min = float(self.geographical_params['geog x min'])
            geog_y_min = float(self.geographical_params['geog y min'])
            grid_height = float(self.geographical_params['grid height'])
            grid_width = float(self.geographical_params['grid width'])
            grid_rot_angle_degr = float(self.geographical_params['grid rot angle degr'])
        except:
            raise AnaliticSurfaceIOException("Input geographic value error")

        return (geog_x_min, geog_y_min), (grid_height, grid_width), grid_rot_angle_degr

    def transform_loc(self, x, y, z):
        """

        :param x:
        :param y:
        :param z:
        :return:
        """

        pt = dot(self.geographic_transformation_matrix, array([x, y, z])) + self.geographic_offset_matrix
        for deformation in self.deformations:
            if deformation['increment'] == 'additive':
                pt = pt + deformation['matrix']
            elif deformation['increment'] == 'multiplicative':
                pt = pt - deformation['shift_pt']
                pt = dot(deformation['matrix'], pt)
                pt = pt + deformation['shift_pt']
        return pt


def geographic_scale_matrix(a_range, b_range, grid_height, grid_width):
    """

    :param a_range:
    :param b_range:
    :param grid_height:
    :param grid_width:
    :return:
    """

    assert a_range > 0.0
    assert b_range > 0.0
    assert grid_height > 0.0
    assert grid_width > 0.0

    sx = grid_width / a_range
    sy = grid_height / b_range
    sz = 1

    return array([(sx, 0.0, 0.0), (0.0, sy, 0.0), (0.0, 0.0, sz)])


def geographic_rotation_matrix(grid_rot_angle_degr):
    """

    :param grid_rot_angle_degr:
    :return:
    """

    grid_rot_angle_rad = radians(grid_rot_angle_degr)
    sin_rot_angle = sin(grid_rot_angle_rad)
    cos_rot_angle = cos(grid_rot_angle_rad)

    return array([(cos_rot_angle, -sin_rot_angle, 0.0),
                     (sin_rot_angle, cos_rot_angle, 0.0),
                     (0.0, 0.0, 1.0)])


def geographic_offset(transformation_matrix, llc_point_matr, llc_point_geog):
    """

    :param transformation_matrix:
    :param llc_point_matr:
    :param llc_point_geog:
    :return:
    """

    return llc_point_geog - dot(transformation_matrix, llc_point_matr)


def geosurface_export_vtk(output_filepath, geodata):
    """

    :param output_filepath:
    :param geodata:
    :return:
    """

    geosurface_XYZ, grid_dims = geodata
    X, Y, Z = geosurface_XYZ

    X_arr = array(X, dtype=float)
    Y_arr = array(Y, dtype=float)
    Z_arr = array(Z, dtype=float)

    n_points = size(X_arr)

    n_rows, n_cols = grid_dims

    with open(output_filepath, 'w') as outfile:

        outfile.write('# vtk DataFile Version 2.0\n')
        outfile.write('Geosurface - qgSurf vers. 0.3.0\n')
        outfile.write('ASCII\n')
        outfile.write('\nDATASET POLYDATA\n')

        outfile.write('POINTS %d float\n' % n_points)
        for n in range(n_points):
            outfile.write('%.4f %.4f %.4f\n' % (X_arr[n], Y_arr[n], Z_arr[n]))

        outfile.write('\n')

        outfile.write('TRIANGLE_STRIPS %d %d\n' % (n_cols - 1, (n_cols - 1) * (1 + n_rows * 2)))

        num_points_strip = n_rows * 2
        for l in range(n_cols - 1):
            triangle_strip_string = "%d " % num_points_strip
            for p in range(n_rows):
                triangle_strip_string += "%d %d " % ((l + 1) * n_rows + p, l * n_rows + p)
            triangle_strip_string += "\n"
            outfile.write(triangle_strip_string)

    return True


def geosurface_export_grass(output_filepath, geodata):
    """

    :param output_filepath:
    :param geodata:
    :return:
    """
    # Save in Grass format

    geosurface_XYZ, grid_dims = geodata
    X, Y, Z = geosurface_XYZ

    X_arr = array(X, dtype=float)
    Y_arr = array(Y, dtype=float)
    Z_arr = array(Z, dtype=float)

    n_rows, n_cols = grid_dims

    with open(output_filepath, 'w') as outfile:
        outfile.write('VERTI:\n')
        for l in range(n_cols - 1):
            for p in range(n_rows - 1):
                start_point_ndx = l * n_rows + p
                forward_line_point_ndx = start_point_ndx + n_rows
                outfile.write('F 4\n')
                outfile.write(
                    ' %.4f %.4f %.4f\n' % (X_arr[start_point_ndx], Y_arr[start_point_ndx], Z_arr[start_point_ndx]))
                outfile.write(' %.4f %.4f %.4f\n' % (
                    X_arr[start_point_ndx + 1], Y_arr[start_point_ndx + 1], Z_arr[start_point_ndx + 1]))
                outfile.write(' %.4f %.4f %.4f\n' % (
                    X_arr[forward_line_point_ndx], Y_arr[forward_line_point_ndx], Z_arr[forward_line_point_ndx]))
                outfile.write(
                    ' %.4f %.4f %.4f\n' % (X_arr[start_point_ndx], Y_arr[start_point_ndx], Z_arr[start_point_ndx]))
                outfile.write('F 4\n')
                outfile.write(' %.4f %.4f %.4f\n' % (
                    X_arr[forward_line_point_ndx], Y_arr[forward_line_point_ndx], Z_arr[forward_line_point_ndx]))
                outfile.write(' %.4f %.4f %.4f\n' % (
                    X_arr[start_point_ndx + 1], Y_arr[start_point_ndx + 1], Z_arr[start_point_ndx + 1]))
                outfile.write(' %.4f %.4f %.4f\n' % (
                    X_arr[forward_line_point_ndx + 1], Y_arr[forward_line_point_ndx + 1],
                    Z_arr[forward_line_point_ndx + 1]))
                outfile.write(' %.4f %.4f %.4f\n' % (
                    X_arr[forward_line_point_ndx], Y_arr[forward_line_point_ndx], Z_arr[forward_line_point_ndx]))

    return True


def geosurface_export_esri_generate(output_filepath, geodata):
    """

    :param output_filepath:
    :param geodata:
    :return:
    """

    # Save geosurface (GAS) in Esri generate  format

    geosurface_XYZ, grid_dims = geodata
    X, Y, Z = geosurface_XYZ

    X_arr = array(X, dtype=float)
    Y_arr = array(Y, dtype=float)
    Z_arr = array(Z, dtype=float)

    n_rows, n_cols = grid_dims

    progr_id = 0
    with open(output_filepath, 'w') as outfile:
        outfile.write('VERTI:\n')
        for l in range(n_cols - 1):
            for p in range(n_rows - 1):
                start_point_ndx = l * n_rows + p
                forward_line_point_ndx = start_point_ndx + n_rows
                progr_id += 1
                outfile.write('%d\n' % progr_id)
                outfile.write(
                    ' %.4f %.4f %.4f\n' % (X_arr[start_point_ndx], Y_arr[start_point_ndx], Z_arr[start_point_ndx]))
                outfile.write(' %.4f %.4f %.4f\n' % (
                    X_arr[start_point_ndx + 1], Y_arr[start_point_ndx + 1], Z_arr[start_point_ndx + 1]))
                outfile.write(' %.4f %.4f %.4f\n' % (
                    X_arr[forward_line_point_ndx], Y_arr[forward_line_point_ndx], Z_arr[forward_line_point_ndx]))
                outfile.write(
                    ' %.4f %.4f %.4f\n' % (X_arr[start_point_ndx], Y_arr[start_point_ndx], Z_arr[start_point_ndx]))
                outfile.write('END\n')
                progr_id += 1
                outfile.write('%d\n' % progr_id)
                outfile.write(' %.4f %.4f %.4f\n' % (
                    X_arr[forward_line_point_ndx], Y_arr[forward_line_point_ndx], Z_arr[forward_line_point_ndx]))
                outfile.write(' %.4f %.4f %.4f\n' % (
                    X_arr[start_point_ndx + 1], Y_arr[start_point_ndx + 1], Z_arr[start_point_ndx + 1]))
                outfile.write(' %.4f %.4f %.4f\n' % (
                    X_arr[forward_line_point_ndx + 1], Y_arr[forward_line_point_ndx + 1],
                    Z_arr[forward_line_point_ndx + 1]))
                outfile.write(' %.4f %.4f %.4f\n' % (
                    X_arr[forward_line_point_ndx], Y_arr[forward_line_point_ndx], Z_arr[forward_line_point_ndx]))
                outfile.write('END\n')
        outfile.write('END\n')

    return True


def geosurface_save_gas(output_filepath, geodata):
    """

    :param output_filepath:
    :param geodata:
    :return:
    """

    with open(output_filepath, 'w') as outfile:
        json.dump(geodata, outfile)

    return True


def geosurface_export_xyz( xyz_file_path, geodata, ):

    geosurface_XYZ, _ = geodata
    X, Y, Z = geosurface_XYZ
    assert len(X) == len(Y)
    assert len(X) == len(Z)

    rec_values_list2 = zip( X, Y, Z )

    with open( xyz_file_path, "w") as ofile:
        for line in rec_values_list2:
            ofile.write( ",".join([str(val) for val in line ])+"\n")

    return True


def geosurface_read_gas_input(infile_path):
    """

    :param infile_path:
    :return:
    """

    try:
        with open(infile_path, 'r') as infile:
            input_geosurface = json.load(infile)
    except:
        raise AnaliticSurfaceIOException("Check input file name")

    src_analytical_params = input_geosurface['analytical surface']
    src_geographical_params = input_geosurface['geographical params']
    try:
        src_deformational_params = input_geosurface['deformational params']
    except:
        src_deformational_params = []

    return src_analytical_params, src_geographical_params, src_deformational_params


def try_geosurface_export_shapefile_pt3d(shapefile_path, geodata, fields_dict_list, crs=None):
    """

    :param shapefile_path:
    :param geodata:
    :param fields_dict_list:
    :param crs:
    :return:
    """

    shapefile_create(shapefile_path,
         ogr.wkbPoint25D,
         fields_dict_list,
         crs)

    field_list = [field_dict["name"] for field_dict in fields_dict_list]

    geosurface_XYZ, _ = geodata
    X, Y, Z = geosurface_XYZ

    ids = range(len(X))

    rec_values_list2 = zip(ids, X, Y, Z)
    success, msg = try_write_point_shapefile(shapefile_path, field_list, rec_values_list2)

    return success, msg