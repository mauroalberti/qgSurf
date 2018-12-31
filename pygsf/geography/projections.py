
from ..spatial.vectorial.vectorial import Point, Segment
from ..libs_utils.qgis.qgs_tools import qgs_project_xy


def calculate_azimuth_correction(src_pt: Point, crs):

    # Calculates dip direction correction with respect to project CRS y-axis orientation

    srcpt_prjcrs_x = src_pt.x
    srcpt_prjcrs_y = src_pt.y

    srcpt_epsg4326_lon, srcpt_epsg4326_lat = qgs_project_xy(
        x=srcpt_prjcrs_x,
        y=srcpt_prjcrs_y,
        srcCrs=crs)

    north_dummpy_pt_lon = srcpt_epsg4326_lon  # no change
    north_dummpy_pt_lat = srcpt_epsg4326_lat + (1.0 / 1200.0)  # add 3 minute-seconds (approximately 90 meters)

    dummypt_prjcrs_x, dummypt_prjcrs_y = qgs_project_xy(
        x=north_dummpy_pt_lon,
        y=north_dummpy_pt_lat,
        destCrs=crs)

    start_pt = Point(
        srcpt_prjcrs_x,
        srcpt_prjcrs_y)

    end_pt = Point(
        dummypt_prjcrs_x,
        dummypt_prjcrs_y)

    north_vector = Segment(
        start_pt=start_pt,
        end_pt=end_pt).vector()

    azimuth_correction = north_vector.azimuth

    return azimuth_correction
