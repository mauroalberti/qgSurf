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
from .pygsf.orientations.orientations import Plane as GPlane
from .pygsf.libs_utils.gdal.ogr import shapefile_create, try_write_point_shapefile

from .pygsf.libs_utils.qgis.qgs_tools import pt_geoms_attrs, loaded_point_layers


def formally_valid_angles_params(structural_input_params):

    for param_key in structural_input_params:
        if structural_input_params[param_key] is None:
            return False
    return True


def get_anglecalc_input_params(dialog):

    def parse_field_choice(val, choose_message):

        if val == choose_message:
            return None
        else:
            return val

    point_layer = dialog.point_layer

    plane_azimuth_type = dialog.cmbInputPlaneOrientAzimType.currentText()
    plane_azimuth_name_field = parse_field_choice(dialog.cmbInputPlaneAzimSrcFld.currentText(),
                                                  tFieldUndefined)

    plane_dip_type = dialog.cmbInputPlaneOrientDipType.currentText()
    plane_dip_name_field = parse_field_choice(dialog.cmbInputPlaneDipSrcFld.currentText(),
                                              tFieldUndefined)

    target_dipdir = dialog.spnTargetAttDipDir.value()
    target_dipangle = dialog.spnTargetAttDipAng.value()

    output_shapefile_path = dialog.lnedtOutFilename.text()

    return point_layer, dict(plane_azimuth_type=plane_azimuth_type,
                             plane_azimuth_name_field=plane_azimuth_name_field,
                             plane_dip_type=plane_dip_type,
                             plane_dip_name_field=plane_dip_name_field,
                             target_dipdir=target_dipdir,
                             target_dipangle=target_dipangle,
                             output_shapefile_path=output_shapefile_path)


def get_angle_data_type(structural_input_params):

    # define type for planar data
    if structural_input_params["plane_azimuth_name_field"] is not None and \
                    structural_input_params["plane_dip_name_field"] is not None:
        planar_data = True
        if structural_input_params["plane_azimuth_type"] == "dip direction":
            planar_az_type = "dip_dir"
        elif structural_input_params["plane_azimuth_type"] == "strike rhr":
            planar_az_type = "strike_rhr"
        else:
            raise Exception("Error with input azimuth type")
        planar_dip_type = "dip"
    else:
        planar_data = False
        planar_az_type = None
        planar_dip_type = None

    return dict(planar_data=planar_data,
                planar_az_type=planar_az_type,
                planar_dip_type=planar_dip_type)


def parse_angles_geodata(input_data_types, structural_data):

    def parse_azimuth_values(azimuths, az_type):

        if az_type == "dip_dir":
            offset = 0.0
        elif az_type == "strike_rhr":
            offset = 90.0
        else:
            raise Exception("Invalid azimuth data type")

        return [(val + offset) % 360.0 for val in azimuths]

    xy_vals = [(float(rec[0]), float(rec[1])) for rec in structural_data]

    try:
        if input_data_types["planar_data"]:
            azimuths = [float(rec[2]) for rec in structural_data]
            dipdir_vals = parse_azimuth_values(azimuths,
                                                input_data_types["planar_az_type"])
            dipangle_vals = [float(rec[3]) for rec in structural_data]
            plane_vals = list(zip(dipdir_vals, dipangle_vals))
        else:
            plane_vals = None
    except Exception as e:
        raise Exception("Error in planar data parsing: {}".format(e))

    return xy_vals, plane_vals


class PtsPlnDistancesWidget(QWidget):

    sgnWindowClosed = pyqtSignal()

    def __init__(self, canvas, plugin_name):

        super(PtsPlnDistancesWidget, self).__init__()
        self.mapCanvas = canvas
        self.pluginName = plugin_name

        self.pointLayer = None
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
        self.pshCalculateAngles.clicked.connect(self.calculate_angles)
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
            try:
                point_layer, structural_input_params = get_anglecalc_input_params(dialog)
            except:
                self.warn("Incorrect definition")
                return
        else:
            self.warn("Nothing defined")
            return

        if not formally_valid_angles_params(structural_input_params):
            self.warn("Invalid/incomplete parameters")
            return
        else:
            self.info("Input data defined")

        self.pointLayer, self.distancesAnalysisParams = point_layer, structural_input_params

    def calculate_angles(self):

        # check definition of input point layer
        if self.pointLayer is None or \
           self.distancesAnalysisParams is None:
            self.warn(str("Input point layer/parameters not defined"))
            return

        # get used field names in the point attribute table 
        lAttitudeFldnms = [self.distancesAnalysisParams["plane_azimuth_name_field"],
                           self.distancesAnalysisParams["plane_dip_name_field"]]

        # get input data presence and type
        structural_data = pt_geoms_attrs(self.pointLayer, lAttitudeFldnms)
        input_data_types = get_angle_data_type(self.distancesAnalysisParams)
           
        try:  
            xy_coords, plane_orientations = parse_angles_geodata(input_data_types, structural_data)
        except Exception as msg:
            self.warn(str(msg))
            return

        if plane_orientations is None:
            self.warn("Plane orientations are not available")
            return

        target_plane_dipdir = self.distancesAnalysisParams["target_dipdir"]
        target_plane_dipangle = self.distancesAnalysisParams["target_dipangle"]

        trgt_geolplane = GPlane(target_plane_dipdir, target_plane_dipangle)
        angles = []
        for plane_or in plane_orientations:
            angles.append(trgt_geolplane.angle(GPlane(*plane_or)))

        fields_dict_list = [dict(name='id', ogr_type=ogr.OFTInteger),
                            dict(name='x', ogr_type=ogr.OFTReal),
                            dict(name='y', ogr_type=ogr.OFTReal),
                            dict(name='azimuth', ogr_type=ogr.OFTReal),
                            dict(name='dip_angle', ogr_type=ogr.OFTReal),
                            dict(name='angle', ogr_type=ogr.OFTReal)]

        point_shapefile, point_shapelayer = shapefile_create(
            self.distancesAnalysisParams["output_shapefile_path"],
            ogr.wkbPoint,
            fields_dict_list)

        lFields = [field_dict["name"] for field_dict in fields_dict_list]

        rngIds = list(range(1, len(angles) + 1))
        x = [val[0] for val in xy_coords]
        y = [val[1] for val in xy_coords]
        plane_az = [val[0] for val in plane_orientations]
        plane_dip = [val[1] for val in plane_orientations]

        llRecValues = list(zip(rngIds,
                          x,
                          y,
                          plane_az,
                          plane_dip,
                          angles))

        try_write_point_shapefile(
            path=self.distancesAnalysisParams["output_shapefile_path"],
            field_names=lFields,
            values=llRecValues,
            ndx_x_val=4)

        self.info("Output shapefile written")

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
