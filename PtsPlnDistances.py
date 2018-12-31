# -*- coding: utf-8 -*-

"""
/***************************************************************************
 qgSurf - plugin for Quantum GIS

 Processing of geological planes and surfaces

                              -------------------
        begin                : 2011-12-21
        copyright            : (C) 2011-2019 by Mauro Alberti
        email                : alberti.m65@gmail.com

 ***************************************************************************/

# licensed under the terms of GNU GPL 3

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 3 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from builtins import str
from builtins import zip
from builtins import range

import os

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *

from osgeo import ogr

from .config.general_params import *

from .auxiliary_windows.distances import DistancesSrcPtLyrDlg, tFieldUndefined
from .pygsf.spatial.vectorial.vectorial import Point
from .pygsf.orientations.orientations import Plane as GPlane
from .pygsf.libs_utils.gdal.ogr import shapefile_create, try_write_pt_shapefile

from .pygsf.libs_utils.qgis.qgs_tools import lyr_attrs, loaded_point_layers, get_project_crs
from .pygsf.geography.projections import calculate_azimuth_correction


def get_distances_input_params(dialog):

    def parse_field_choice(val, choose_message):

        if val == choose_message:
            return None
        else:
            return val

    plyr = dialog.point_layer

    plyr_id_name_field = parse_field_choice(
        dialog.cmbIdSrcFld.currentText(),
        tFieldUndefined)
    if not plyr_id_name_field:
        return False, "Incorrect id field choice"

    plyr_x_name_field = parse_field_choice(
        dialog.cmbXSrcFld.currentText(),
        tFieldUndefined)
    if not plyr_x_name_field:
        return False, "Incorrect x field choice"

    plyr_y_name_field = parse_field_choice(
        dialog.cmbYSrcFld.currentText(),
        tFieldUndefined)
    if not plyr_y_name_field:
        return False, "Incorrect y field choice"

    plyr_z_name_field = parse_field_choice(
        dialog.cmbZSrcFld.currentText(),
        tFieldUndefined)
    if not plyr_z_name_field:
        return False, "Incorrect z field choice"

    # geological plane parameters section

    gplane_dipdir = dialog.spnTargetAttDipDir.value()
    gplane_dipangle = dialog.spnTargetAttDipAng.value()

    try:
        gplane_srcpt_x_coord = float(dialog.qlndtXPlaneSrcFld.text())
        gplane_srcpt_y_coord = float(dialog.qlndtYPlaneSrcFld.text())
        gplane_srcpt_z_coord = float(dialog.qlndtZPlaneSrcFld.text())
    except:
        return False, "Incorrect source point coordinates"

    # output shapefile

    output_shapefile_path = dialog.lnedtOutFilename.text()
    if not output_shapefile_path:
        return False, "Missing output shapefile path"

    # returning parameters

    return True, dict(
        point_layer=plyr,
        point_layer_flds=(plyr_id_name_field, plyr_x_name_field, plyr_y_name_field, plyr_z_name_field),
        gplane_params=dict(
            pl_attitude=(gplane_dipdir, gplane_dipangle),
            src_pt=(gplane_srcpt_x_coord, gplane_srcpt_y_coord, gplane_srcpt_z_coord)),
        output_shapefile_path=output_shapefile_path)


class PtsPlnDistancesWidget(QWidget):

    sgnWindowClosed = pyqtSignal()

    def __init__(self, canvas, plugin_name):

        super(PtsPlnDistancesWidget, self).__init__()
        self.mapCanvas = canvas
        self.pluginName = plugin_name

        self.pointLayer = None
        self.pointLayerFields = []
        self.distancesAnalysisParams = None

        self.setup_gui()

    def setup_gui(self): 

        self.layout = QVBoxLayout()
        
        self.layout.addWidget(self.setup_inputdata())
        self.layout.addWidget(self.setup_processing())
        self.layout.addWidget(self.setup_help())

        self.setLayout(self.layout)
        self.setWindowTitle("{} - points distances to geological plane".format(self.pluginName))
        self.adjustSize()

    def setup_inputdata(self):
        
        grpInput = QGroupBox("Define params")
        
        layout = QVBoxLayout() 
        
        self.pshDefinePointLayer = QPushButton(self.tr("I/O params"))
        self.pshDefinePointLayer.clicked.connect(self.user_define_distances_inparams)
        layout.addWidget(self.pshDefinePointLayer)
        
        grpInput.setLayout(layout)
        
        return grpInput

    def setup_processing(self):
        
        grpProcessing = QGroupBox("Processing")
        
        layout = QGridLayout()

        self.pshCalculateAngles = QPushButton(self.tr("Calculate"))
        self.pshCalculateAngles.clicked.connect(self.calculate_distances)
        layout.addWidget(self.pshCalculateAngles, 0, 0, 1, 1)

        grpProcessing.setLayout(layout)
        
        return grpProcessing

    def setup_help(self):

        group_box = QGroupBox("Help")

        layout = QVBoxLayout()

        self.pshHelp = QPushButton(self.tr("Open help"))
        self.pshHelp.clicked.connect(self.open_help)
        layout.addWidget(self.pshHelp)

        group_box.setLayout(layout)

        return group_box

    def user_define_distances_inparams(self):

        self.distancesAnalysisParams = None

        if len(loaded_point_layers()) == 0:
            self.warn("No available point layers")
            return

        dialog = DistancesSrcPtLyrDlg()
        if dialog.exec_():
            success, cntnt = get_distances_input_params(dialog)
        else:
            self.warn("No input data defined")
            return

        if not success:
            self.warn(cntnt)
            return
        else:
            structural_input_params = cntnt

        self.pointLayer = structural_input_params["point_layer"]
        self.pointLayerFields = structural_input_params["point_layer_flds"]
        self.gPlaneAttitude = structural_input_params["gplane_params"]["pl_attitude"]
        self.gPlaneSrcPt = structural_input_params["gplane_params"]["src_pt"]
        self.outputShapefilePath = structural_input_params["output_shapefile_path"]

        self.info("Now results can be calculated")

    def calculate_distances(self):

        if not self.pointLayer or \
            not self.pointLayerFields:
            self.warn("Input data are not defined")
            return

        # get input point layer data

        point_layer_data = lyr_attrs(
            layer=self.pointLayer,
            fields=self.pointLayerFields)

        len_data = len(point_layer_data)

        if len_data == 0:
            self.warn("No data to calculate")
            return

        cartplane_srcpt = Point(*self.gPlaneSrcPt)
        projectCrs = get_project_crs(self.mapCanvas)

        geoplane_dipdir, geoplane_dipangle = self.gPlaneAttitude

        azimuth_correction = calculate_azimuth_correction(
            src_pt=cartplane_srcpt,
            crs=projectCrs)
        print("Azimuth correction: {}".format(azimuth_correction))

        geoplane_dipdir_corrected = (geoplane_dipdir + azimuth_correction) % 360.0
        prj_corrected_geolplane = GPlane(geoplane_dipdir_corrected, geoplane_dipangle)

        cartplane = prj_corrected_geolplane.toCPlane(cartplane_srcpt)

        ltAttributes = []
        ltfGeometries = []
        for pt_data in point_layer_data:

            id, x, y, z = pt_data
            pt = Point(x, y, z)
            distance = cartplane.pointDistance(pt)
            ltAttributes.append((id, x, y, z, distance))
            ltfGeometries.append((x, y, z))

        fields_dict_list = [dict(name='id', ogr_type="ogr.OFTInteger"),
                            dict(name='x', ogr_type="ogr.OFTReal"),
                            dict(name='y', ogr_type="ogr.OFTReal"),
                            dict(name='z', ogr_type="ogr.OFTReal"),
                            dict(name='distance', ogr_type="ogr.OFTReal")]

        ltFieldsNames = [field_dict["name"] for field_dict in fields_dict_list]

        out_shape_pth = self.outputShapefilePath
        shapefile_datasource, point_shapelayer = shapefile_create(
            path=out_shape_pth,
            geom_type=ogr.wkbPoint25D,
            fields_dict_list=fields_dict_list)

        if not shapefile_datasource or not point_shapelayer:
            self.warn("Unable to create output shapefile {}".format(out_shape_pth))
            return

        success, msg = try_write_pt_shapefile(
            point_layer=point_shapelayer,
            geoms=ltfGeometries,
            field_names=ltFieldsNames,
            attrs=ltAttributes)

        try:
            del point_shapelayer
            del shapefile_datasource
        except:
            pass

        if success:
            self.info("Results written in output shapefile {}".format(out_shape_pth))
        else:
            self.warn(msg)

    def info(self, msg):
        
        QMessageBox.information(self, self.pluginName, msg)

    def warn(self, msg):
    
        QMessageBox.warning(self, self.pluginName, msg)

    def closeEvent(self, event):

        settings = QSettings(settings_name, plugin_nm)

        settings.setValue("PtsPlnDistancesWidget/size", self.size())
        settings.setValue("PtsPlnDistancesWidget/position", self.pos())

        self.sgnWindowClosed.emit()

    def open_help(self):

        dialog = HelpDialog(self.pluginName)
        dialog.exec_()


class HelpDialog(QDialog):

    def __init__(self, plugin_name, parent=None):
        super(HelpDialog, self).__init__(parent)

        layout = QVBoxLayout()

        # About section

        helpTextBrwsr = QTextBrowser(self)

        url_path = "file:///{}/help/help_pts_plane_dists.html".format(os.path.dirname(__file__))
        helpTextBrwsr.setSource(QUrl(url_path))
        helpTextBrwsr.setSearchPaths(['{}/help'.format(os.path.dirname(__file__))])
        helpTextBrwsr.setMinimumSize(700, 600)

        layout.addWidget(helpTextBrwsr)

        self.setLayout(layout)

        self.setWindowTitle("{} - points-plane distances Help".format(plugin_name))
