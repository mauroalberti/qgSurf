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

# The "delete_selected_records" method
# contains code modified from (chp. 15) assetmanager.pyw by Summerfield

#!/usr/bin/env python
# Copyright (c) 2007-8 Qtrac Ltd. All rights reserved.
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.


# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
from datetime import datetime as dt

import sqlite3

from osgeo import ogr

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtSql import *
from PyQt5.QtSql import QSqlDatabase
from qgis.PyQt.uic import loadUi

from qgis.core import *
from qgis.gui import *

from .config.general_params import *
from .db_queries.queries import *
from .config.minor_params import *
from .messages.msgs import *

from .pygsf.libs_utils.qt.filesystem import define_path_new_file, old_file_path
from .pygsf.libs_utils.qt.databases import try_connect_to_sqlite3_db_with_qt, get_selected_recs_ids
from .pygsf.libs_utils.gdal.ogr import shapefile_create, try_write_point_shapefile, try_write_line_shapefile
from .pygsf.libs_utils.gdal.gdal import try_read_raster_band
from .pygsf.libs_utils.qgis.qgs_tools import *
from .pygsf.libs_utils.mpl.mpl_widget import MplWidget
from .pygsf.spatial.rasters.geoarray import GeoArray
from .pygsf.orientations.orientations import *
from .pygsf.mathematics.arrays import xyzSvd
from .pygsf.libs_utils.yaml.io import read_yaml
from .pygsf.libs_utils.sqlite.sqlite3 import try_create_db_tables, try_execute_query_with_sqlite3
from .pygsf.libs_utils.qt.databases import try_execute_query_with_qt

bfp_texts_flnm = "texts.yaml"
bfp_params_flnm = "parameters.yaml"

plugin_folder = os.path.dirname(__file__)

config_fldrpth = os.path.join(
    plugin_folder,
    config_fldr)


def get_field_dict(key_val, flds_dicts):

    filt_dicts = list(filter(lambda dct: key_val in dct.keys(), flds_dicts))

    if len(filt_dicts) == 1:
        return filt_dicts[0][key_val]
    else:
        return None


def parse_db_params(sqlite_params):

    tables = sqlite_params["tables"]

    solutions_pars = tables["solutions"]
    src_points_pars = tables["src_pts"]

    solutions_tbl_nm = solutions_pars["name"]
    solutions_tbl_flds = solutions_pars["fields"]

    src_points_tbl_nm = src_points_pars["name"]
    src_points_tbl_flds = src_points_pars["fields"]

    return (
        solutions_tbl_nm,
        solutions_tbl_flds,
        src_points_tbl_nm,
        src_points_tbl_flds)


def get_out_shape_params(geom_type="point"):

    output_shapefile_params_file = os.path.join(
        config_fldrpth,
        output_shapefile_params_flnm)

    plugin_params = read_yaml(output_shapefile_params_file)

    if geom_type == "point":
        return plugin_params["pt_shapefile"]
    elif geom_type == "line":
        return plugin_params["ln_shapefile"]
    else:
        return None


def try_xprt_selected_records_to_pt_shapefile(point_shapefile_path: str, solutions: List[Tuple]):

    try:

        shape_pars = get_out_shape_params("point")
        fld_nms = list(map(lambda par: par["name"], shape_pars))

        success, msg = try_write_point_shapefile(
            path=point_shapefile_path,
            field_names=fld_nms,
            values=solutions,
            ndx_x_val=ndx_x_val)

        if success:
            return True, "Results saved in shapefile.<br />Now you can load it"
        else:
             return False, msg

    except Exception as e:

        return False, str(e)


def try_xprt_selected_records_to_ln_shapefile(line_shapefile_path: str, id_vals_xyzs: Dict):

    try:

        shape_pars = get_out_shape_params("line")
        fld_nms = list(map(lambda par: par["name"], shape_pars))

        success, msg = try_write_line_shapefile(
            path=line_shapefile_path,
            field_names=fld_nms,
            values=id_vals_xyzs)

        if success:
            return True, "Results saved in shapefile.<br />Now you can load it"
        else:
             return False, msg

    except Exception as e:

        return False, str(e)


def remove_equal_consecutive_xypairs(xy_list):

    out_xy_list = [xy_list[0]]

    for n in range(1, len(xy_list)):
        if not eq_xy_pair(xy_list[n], out_xy_list[-1]):
            out_xy_list.append(xy_list[n])

    return out_xy_list


def list3_to_list(list3):
    """
    input: a list of list of (x,y) tuples
    output: a list of (x,y) tuples
    """

    out_list = []
    for list2 in list3:
        for list1 in list2:
            out_list += list1

    return out_list


class BestFitPlaneMainWidget(QWidget):

    bfp_calc_update = pyqtSignal()

    def __init__(self, tool_nm, canvas, plugin_qaction, db_tables_params):

        super(BestFitPlaneMainWidget, self).__init__()

        self.tool_nm = tool_nm
        self.canvas, self.plugin = canvas, plugin_qaction

        self.db_tables_params = db_tables_params
        self.init_params()

        self.setup_gui()

        self.bfp_calc_update.connect(self.update_bfpcalc_btn_state)

        self.db_tables_params = db_tables_params

    def init_params(self):

        bfp_text_config_flpth = os.path.join(
            config_fldrpth,
            bfp_texts_flnm)

        texts_params = read_yaml(bfp_text_config_flpth)

        self.dem_default_text = texts_params["layer_default_text"]
        self.ptlnlyr_default_text = texts_params["ptlnlyr_default_text"]

        bfp_num_config_flpth = os.path.join(
            config_fldrpth,
            bfp_params_flnm)

        num_params = read_yaml(
            file_pth=bfp_num_config_flpth
        )

        self.ciMaxPointsNumberForBFP = num_params["ciMaxPointsNumberForBFP"]

        self.reset_dem_input_states()
        self.previousTool = None        
        self.input_points = None
        self.bestfitplane_point_markers = []  
        self.res_id = 0

        self.bestfitplane_points = []
        self.bestfitplane = None

        self.sol_tbl_flds = None
        self.selection_model = None

    def reset_dem_input_states(self):
        
        self.dem, self.grid = None, None

    def setup_gui(self):

        dialog_layout = QVBoxLayout()
        self.main_widget = QTabWidget()
        self.main_widget.addTab(self.setup_processing_tab(), "Processing")
        self.main_widget.addTab(self.setup_configurations_tab(), "Configurations")
        self.main_widget.addTab(self.setup_results_tab(), "Results")
        self.main_widget.addTab(self.setup_help_tab(), "Help")

        self.main_widget.currentChanged.connect(self.onTabChange)

        dialog_layout.addWidget(self.main_widget)
        self.setLayout(dialog_layout)                    
        self.adjustSize()                       
        self.setWindowTitle('{} - {}'.format(plugin_nm, self.tool_nm))

    @pyqtSlot()
    def onTabChange(self):

        self.setup_results_tableview()
        self.solutionsView.update()

    def setup_processing_tab(self):
        
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.setup_source_dem())
        layout.addWidget(self.setup_source_points())
        layout.addWidget(self.setup_bfp_processing())
        widget.setLayout(layout)
        return widget

    def setup_results_tab(self):

        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.setup_results_processings())
        widget.setLayout(layout)
        return widget

    def setup_configurations_tab(self):

        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.setup_results_configurations())
        widget.setLayout(layout)
        return widget

    def setup_help_tab(self):

        qwdtHelp = QWidget()
        qlytHelp = QVBoxLayout()

        qtbrHelp = QTextBrowser(qwdtHelp)
        url_path = "file:///{}/help/help_bfp.html".format(os.path.dirname(__file__))
        qtbrHelp.setSource(QUrl(url_path))
        qtbrHelp.setSearchPaths(['{}/help'.format(os.path.dirname(__file__))])
        qlytHelp.addWidget(qtbrHelp)

        qwdtHelp.setLayout(qlytHelp)

        return qwdtHelp

    def setup_results_tableview(self):

        db_path = self.result_db_path_qle.text()

        if db_path:

            success, msg = try_connect_to_sqlite3_db_with_qt(db_path)
            if not success:
                QMessageBox.critical(
                    self,
                    self.tool_nm,
                    msg)
                return

            pars = parse_db_params(self.db_tables_params)

            self.solutions_tblnm, self.sol_tbl_flds, self.pts_tbl_nm, self.pts_tbl_flds = pars
            self.solutionsModel = QSqlTableModel(db=QSqlDatabase.database())
            self.solutionsModel.setTable(self.solutions_tblnm)

            self.solutionsModel.setHeaderData(ID_SOL, Qt.Horizontal, "id")
            self.solutionsModel.setHeaderData(DIP_DIR, Qt.Horizontal, "dip direction")
            self.solutionsModel.setHeaderData(DIP_ANG, Qt.Horizontal, "dip angle")
            self.solutionsModel.setHeaderData(DATASET, Qt.Horizontal, "dataset")
            self.solutionsModel.setHeaderData(NOTES, Qt.Horizontal, "notes")
            self.solutionsModel.setHeaderData(SRC_CRS, Qt.Horizontal, "source crs")
            self.solutionsModel.setHeaderData(CREAT_TIME, Qt.Horizontal, "created")

            self.solutionsModel.select()

            self.solutionsView.setModel(self.solutionsModel)
            self.solutionsView.setSelectionMode(QTableView.MultiSelection)
            self.solutionsView.setSelectionBehavior(QTableView.SelectRows)
            self.solutionsView.verticalHeader().hide()
            self.solutionsView.resizeColumnsToContents()

            self.solutionsView.resizeRowsToContents()
            self.solutionsView.setSortingEnabled(True)

            self.selection_model = self.solutionsView.selectionModel()

    def setup_results_processings(self):

        self.results_widget = QWidget()

        self.results_layout = QVBoxLayout()

        plot_selected_recs = QPushButton("Plot selected records")
        plot_selected_recs.clicked.connect(self.plot_selected_records)
        self.results_layout.addWidget(plot_selected_recs)

        delete_selected_recs = QPushButton("Delete selected records")
        delete_selected_recs.clicked.connect(self.delete_selected_records)
        self.results_layout.addWidget(delete_selected_recs)

        xprt_selected_recs = QPushButton("Export selected records")
        xprt_selected_recs.clicked.connect(self.xprt_selected_records)
        self.results_layout.addWidget(xprt_selected_recs)

        self.solutionsView = QTableView()

        self.solutionsView.show()

        self.results_layout.addWidget(self.solutionsView)

        self.results_widget.setLayout(self.results_layout)

        return self.results_widget

    def setup_source_dem(self):

        main_groupbox = QGroupBox(self.tr("Source DEM"))
        
        main_layout = QGridLayout()
    
        main_layout.addWidget(QLabel("DEM layer"), 0, 0, 1, 1)
        self.define_dem_QComboBox = QComboBox()
        self.define_dem_QComboBox.addItem(self.dem_default_text)
        main_layout.addWidget(self.define_dem_QComboBox, 0, 1, 1, 2)

        self.refresh_raster_layer_list()
        QgsProject.instance().layerWasAdded.connect(self.refresh_raster_layer_list)
        QgsProject.instance().layerRemoved.connect(self.refresh_raster_layer_list)
                             
        main_groupbox.setLayout(main_layout)
              
        return main_groupbox

    def setup_source_points(self):
        
        main_groupbox = QGroupBox(self.tr("Source points"))
        
        main_layout = QGridLayout()

        self.bestfitplane_definepoints_pButton = QPushButton("Define source points in map (n >= 3)")
        self.bestfitplane_definepoints_pButton.clicked.connect(self.bfp_inpoint_from_map_click)
        main_layout.addWidget(self.bestfitplane_definepoints_pButton, 0, 0, 1, 2)

        self.bestfitplane_getpointsfromlyr_pButton = QPushButton("Get source points from layer")
        self.bestfitplane_getpointsfromlyr_pButton.clicked.connect(self.bfp_points_from_lyr)
        main_layout.addWidget(self.bestfitplane_getpointsfromlyr_pButton, 1, 0, 1, 2)

        self.bestfitplane_inpts_lyr_list_QComboBox = QComboBox()
        main_layout.addWidget(self.bestfitplane_inpts_lyr_list_QComboBox, 2, 0, 1, 2)

        self.bestfitplane_resetpoints_pButton = QPushButton("Reset source points")
        self.bestfitplane_resetpoints_pButton.clicked.connect(self.bfp_reset_all_inpoints)
        main_layout.addWidget(self.bestfitplane_resetpoints_pButton, 3, 0, 1, 2)

        self.refresh_inpts_layer_list()
        QgsProject.instance().layerWasAdded.connect(self.refresh_inpts_layer_list)
        QgsProject.instance().layerRemoved.connect(self.refresh_inpts_layer_list)
        
        self.bestfitplane_src_points_ListWdgt = QListWidget()
        main_layout.addWidget(self.bestfitplane_src_points_ListWdgt, 4, 0, 1, 2)

        self.enable_point_input_buttons(False)

        main_groupbox.setLayout(main_layout)
                 
        return main_groupbox

    def setup_bfp_processing(self):

        main_groupbox = QGroupBox(self.tr("Best fit planes"))

        layout = QGridLayout()

        self.bestfitplane_calculate_pButton = QPushButton("Calculate best fit plane")
        self.bestfitplane_calculate_pButton.clicked.connect(self.calculate_bestfitplane)
        self.bestfitplane_calculate_pButton.setEnabled(False)
        layout.addWidget(self.bestfitplane_calculate_pButton, 0, 0, 1, 2)

        self.enable_point_input_buttons(False)

        main_groupbox.setLayout(layout)

        return main_groupbox

    def setup_results_configurations(self):

        group_box = QGroupBox(self.tr("Database for result storage (sqlite3)"))

        layout = QGridLayout()

        self.result_db_path_qle = QLineEdit()
        layout.addWidget(self.result_db_path_qle, 0, 0, 1, 2)

        self.open_existing_sqlite = QPushButton("Load existing database")
        self.open_existing_sqlite.clicked.connect(self.find_existing_db)
        layout.addWidget(self.open_existing_sqlite, 1, 0, 1, 2)

        self.create_new_sqlite = QPushButton("Create result database")
        self.create_new_sqlite.clicked.connect(self.create_result_db)
        layout.addWidget(self.create_new_sqlite, 2, 0, 1, 2)

        group_box.setLayout(layout)

        return group_box

    def view_in_stereonet(self):
        """
        Plot plane solution in stereonet.

        :return: None
        """

        stereonet_dialog = SolutionStereonetDialog(
            tool_nm=self.tool_nm,
            plane=self.bestfitplane,
            points=self.bestfitplane_points,
            result_db_path=self.result_db_path_qle.text(),
            db_tables_params=self.db_tables_params,
            prj_crs=self.get_project_crs_long_descr())
        stereonet_dialog.exec_()

    def create_result_db(self):

        db_path = define_path_new_file(
            parent=self,
            show_msg="Create sqlite3 db",
            path=None,
            filter_text="Database (*.sqlite3)")

        if not db_path:
            return

        tables = self.db_tables_params["tables"]

        solutions_pars = tables["solutions"]
        src_points_pars = tables["src_pts"]

        success, msg = try_create_db_tables(
            db_path=db_path,
            tables_pars=[
                solutions_pars,
                src_points_pars])

        if success:

            self.result_db_path_qle.setText(db_path)

            self.setup_results_tableview()

            QMessageBox.information(
                self,
                self.tool_nm,
                "Result db created")

        else:

            QMessageBox.critical(
                self,
                self.tool_nm,
                msg)

    def find_existing_db(self):

        def check_table_presence(table_nm):

            check_query_str = check_query_template.format(
                table_name=table_nm)

            curs.execute(check_query_str)

            return curs.fetchone()[0]

        db_path = old_file_path(
            parent=self,
            show_msg="Open sqlite3 db",
            filter_extension="sqlite3",
            filter_text="Database (*.sqlite3)")

        if not db_path:
            return

        pars = parse_db_params(self.db_tables_params)
        sol_tbl_nm, sol_tbl_flds, pts_tbl_nm, pts_tbl_flds = pars

        conn = sqlite3.connect(db_path)
        curs = conn.cursor()

        tables_to_check = [sol_tbl_nm, pts_tbl_nm]

        tables_found = True
        for table in tables_to_check:
            if not check_table_presence(table):
                QMessageBox.critical(
                    self,
                    self.tool_nm,
                    "Table {} not found in db {}".format(table, db_path)
                )
                tables_found = False
                break

        conn.close()

        if tables_found:

            self.result_db_path_qle.setText(db_path)

            self.setup_results_tableview()

            QMessageBox.information(
                self,
                self.tool_nm,
                "Result db set")

    def add_marker(self, prj_crs_x, prj_crs_y):

        marker = self.create_marker(self.canvas, prj_crs_x, prj_crs_y)       
        self.bestfitplane_point_markers.append(marker)        
        self.canvas.refresh()        

    def set_bfp_input_point(self, qgs_pt, add_marker=True):

        prj_crs_x, prj_crs_y = qgs_pt.x(), qgs_pt.y()

        dem_crs_coord_x, dem_crs_coord_y = self.get_dem_crs_coords(prj_crs_x, prj_crs_y)

        dem_z_value = self.geoarray.interpolate_bilinear(dem_crs_coord_x, dem_crs_coord_y)

        if dem_z_value is None:
            return

        if add_marker:
            self.add_marker(prj_crs_x, prj_crs_y)

        lon, lat = qgs_project_xy(
            x=prj_crs_x,
            y=prj_crs_y,
            srcCrs=self.get_project_crs())
        curr_ndx = len(self.bestfitplane_points) + 1
        self.bestfitplane_points.append([curr_ndx, prj_crs_x, prj_crs_y, dem_z_value, lon, lat])
        self.bestfitplane_src_points_ListWdgt.addItem("%i: %.3f %.3f %.3f %.6f %.6f" % (curr_ndx, prj_crs_x, prj_crs_y, dem_z_value, lon, lat))

        self.bfp_calc_update.emit()

    def bfp_reset_all_inpoints(self):
        
        self.reset_point_input_values()
        self.bfp_calc_update.emit()
                       
    def bfp_inpoint_from_map_click(self):
       
        try:
            self.bestfitplane_PointMapTool.canvasClicked.disconnect(self.set_bfp_input_point)
        except:
            pass

        self.bestfitplane_PointMapTool = PointMapToolEmitPoint(self.canvas, self.plugin)  # mouse listener
        self.previousTool = self.canvas.mapTool()  # save the standard map tool for restoring it at the end
        self.bestfitplane_PointMapTool.canvasClicked.connect(self.set_bfp_input_point)
        self.bestfitplane_PointMapTool.setCursor(Qt.CrossCursor)        
        self.canvas.setMapTool(self.bestfitplane_PointMapTool)

    def bfp_points_from_lyr(self):
        
        # get vector layer
        
        try:
            assert self.bestfitplane_inpts_lyr_list_QComboBox.currentIndex() > 0
            inpts_lyr_qgis_ndx = self.bestfitplane_inpts_lyr_list_QComboBox.currentIndex() - 1
            inpts_lyr = self.inpts_Layers[inpts_lyr_qgis_ndx ]
        except:
            QMessageBox.critical(
                self,
                "Input point layer",
                "Check chosen input layer")
            return

        # read xy tuples from layer (removed consecutive duplicates)

        layer_geom_type = vector_type(inpts_lyr)
        if layer_geom_type == 'point':
            xypair_list = pt_geoms_attrs(inpts_lyr)
            if not xypair_list:
                QMessageBox.critical(
                    self,
                    "Input layer",
                    "Is chosen layer empty?")
                return
        elif layer_geom_type == 'line':
            xypair_list3 = line_geoms_attrs(inpts_lyr)
            if not xypair_list3:
                QMessageBox.critical(
                    self,
                    "Input layer",
                    "Is chosen layer empty?")
                return
            xypair_list3_1 = [xypair_list02[0] for xypair_list02 in xypair_list3 ]
            xypair_flatlist = list3_to_list(xypair_list3_1)
            xypair_list = remove_equal_consecutive_xypairs(xypair_flatlist)
        else:
            raise VectorIOException("Geometry type of chosen layer is not point or line")
        
        if len(xypair_list) > self.ciMaxPointsNumberForBFP:
            QMessageBox.critical(
                self,
                "Input point layer",
                "More than {} points to handle. Please use less features or modify value in config/parameters.yaml".format(self.ciMaxPointsNumberForBFP))
            return

        # for all xy tuples, project to project CRS as a qgis point

        projectCrs = self.get_project_crs()
        proj_crs_qgispoint_list = [qgs_project_point(qgs_point(x, y), inpts_lyr.crs(), projectCrs) for (x, y) in xypair_list]

        # for all qgs points, process them for the input point processing queue

        for qgs_pt in proj_crs_qgispoint_list:
            self.set_bfp_input_point(qgs_pt, add_marker=False)

    def reset_input_point_states(self):
       
        self.reset_point_input_values()        
        self.disable_point_tools()

        self.bfp_calc_update.emit()

    def reset_point_input_values(self):

        self.reset_point_markers()
        self.reset_point_inputs()  

    def reset_point_inputs(self):

        self.bestfitplane_src_points_ListWdgt.clear()
        self.bestfitplane_points = []
        self.bestfitplane = None

    def reset_point_markers(self):

        for mrk in self.bestfitplane_point_markers:
            self.canvas.scene().removeItem(mrk)  
        self.bestfitplane_point_markers = []          

    def enable_point_input_buttons(self, choice = True):
        
        self.bestfitplane_definepoints_pButton.setEnabled(choice)
        self.bestfitplane_getpointsfromlyr_pButton.setEnabled(choice)
        self.bestfitplane_inpts_lyr_list_QComboBox.setEnabled(choice)
        self.bestfitplane_resetpoints_pButton.setEnabled(choice)

    def disable_point_tools(self):

        self.enable_point_input_buttons(False)

        try: 
            self.bestfitplane_PointMapTool.leftClicked.disconnect(self.set_bfp_input_point)
        except: 
            pass
        try: 
            self.disable_MapTool(self.bestfitplane_PointMapTool)
        except: 
            pass         

    def refresh_raster_layer_list(self):

        self.reset_dem_input_states()
                
        try: 
            self.define_dem_QComboBox.currentIndexChanged[int].disconnect(self.get_working_dem)
        except: 
            pass
         
        try:               
            self.reset_input_point_states()
        except:
            pass

        try:
            self.define_dem_QComboBox.clear()
        except:
            return
        
        self.define_dem_QComboBox.addItem(self.dem_default_text)
                                  
        self.rasterLayers = loaded_raster_layers()                 
        if self.rasterLayers is None or len(self.rasterLayers) == 0:
            return
        for layer in self.rasterLayers: 
            self.define_dem_QComboBox.addItem(layer.name())
                        
        self.define_dem_QComboBox.currentIndexChanged[int].connect(self.get_working_dem)                

    def refresh_inpts_layer_list(self):
        
        try:
            self.bestfitplane_inpts_lyr_list_QComboBox.clear()
        except:
            return
        
        self.bestfitplane_inpts_lyr_list_QComboBox.addItem(self.ptlnlyr_default_text)
                                  
        self.inpts_Layers = loaded_point_layers() + loaded_line_layers()                
        if self.inpts_Layers is None or len(self.inpts_Layers) == 0:
            return
        for layer in self.inpts_Layers: 
            self.bestfitplane_inpts_lyr_list_QComboBox.addItem(layer.name())

    def get_working_dem(self, ndx_DEM_file = 0): 
        
        self.reset_dem_input_states()       
        self.reset_input_point_states()        
        if self.rasterLayers is None or len(self.rasterLayers) == 0: 
            return          
                                
        # no DEM layer defined

        if ndx_DEM_file == 0: 
            return             

        self.dem = self.rasterLayers[ndx_DEM_file-1]        

        success, cnt = try_read_raster_band(self.dem.source())
        if not success:
            QMessageBox.critical(self, "DEM", cnt)
            return

        geotransform, projection, band_params, data = cnt

        self.geoarray = GeoArray(
            inGeotransform=geotransform,
            inProjection=projection,
            inLevels=[data]
        )

        self.enable_point_input_buttons()

    def coords_within_dem_bndr(self, dem_crs_coord_x, dem_crs_coord_y):
        
        if dem_crs_coord_x <= self.grid.xmin or dem_crs_coord_x >= self.grid.xmax or \
           dem_crs_coord_y <= self.grid.ymin or dem_crs_coord_y >= self.grid.ymax:
            return False        
        return True        

    def create_marker(self, canvas, prj_crs_x, prj_crs_y, pen_width= 2, icon_type = 2, icon_size = 18, icon_color = 'limegreen'):
        
        marker = QgsVertexMarker(canvas)
        marker.setIconType(icon_type)
        marker.setIconSize(icon_size)
        marker.setPenWidth(pen_width)
        marker.setColor(QColor(icon_color))
        marker.setCenter(QgsPointXY(prj_crs_x, prj_crs_y))
        return marker        

    def update_bfpcalc_btn_state(self):

        if self.bestfitplane_src_points_ListWdgt.count () >= 3:
            state = True
        else:
            state = False

        self.bestfitplane_calculate_pButton.setEnabled(state)

    def calculate_bestfitplane(self):        

        x_ndx, y_ndx, z_ndx = 1, 2, 3
        lfXyz = list(map(lambda idxyz: (idxyz[x_ndx], idxyz[y_ndx], idxyz[z_ndx]), self.bestfitplane_points))
        npaXyz = np.array(lfXyz, dtype=np.float64)
        self.xyz_mean = np.mean(npaXyz, axis=0)
        svd = xyzSvd(npaXyz - self.xyz_mean)
        if svd['result'] == None:
            QMessageBox.critical(
                self,
                self.tool_nm,
                "Unable to calculate result")
            return
        _, _, eigenvectors = svd['result'] 
        lowest_eigenvector = eigenvectors[-1, : ]  # Solution is last row
        normal = lowest_eigenvector[: 3 ] / np.linalg.norm(lowest_eigenvector[: 3 ])        
        normal_vector = Vect(normal[0], normal[1], normal[2])
        normal_direct = Direct.fromVect(normal_vector)
        self.bestfitplane = normal_direct.normPlane()
        
        self.view_in_stereonet()

    def disable_points_definition(self):
        
        self.enable_point_input_buttons(False)

        self.disable_points_MapTool()
        self.reset_point_markers()
        self.bestfitplane_src_points_ListWdgt.clear()

    def disable_MapTool(self, mapTool):
                            
        try:
            if mapTool is not None: self.canvas.unsetMapTool(mapTool)
        except:
            pass                            

        try:
            if self.previousTool is not None: self.canvas.setMapTool(self.previousTool)
        except:
            pass

    def disable_points_MapTool(self):
        
        self.disable_MapTool(self.bestfitplane_PointMapTool)

    def get_project_crs(self) -> QgsCoordinateReferenceSystem:

        return self.canvas.mapSettings().destinationCrs()

    def get_project_crs_authid(self) -> str:

        return self.get_project_crs().authid()

    def get_project_crs_descr(self) -> str:

        return self.get_project_crs().description()

    def get_project_crs_long_descr(self) -> str:

        return "{} - {}".format(
            self.get_project_crs_authid(),
            self.get_project_crs_descr()
        )

    def project_coords(self, x, y, source_crs, dest_crs):
        
        if source_crs != dest_crs:
            dest_crs_qgs_pt = qgs_project_point(qgs_point(x, y), source_crs, dest_crs)
            return dest_crs_qgs_pt.x(), dest_crs_qgs_pt.y()
        else:
            return x, y

    def get_dem_crs_coords(self, x, y):

        projectCrs = self.get_project_crs()

        return self.project_coords(x, y, projectCrs, self.dem.crs())

    def get_prj_crs_coords(self, x, y):

        projectCrs = self.get_project_crs()

        return self.project_coords(x, y, self.dem.crs(), projectCrs)

    def plot_selected_records(self):

        if not self.sol_tbl_flds:
            QMessageBox.warning(
                self,
                self.tool_nm,
                msg_database_missing
            )
            return

        # get relevant fields names

        id_alias = self.sol_tbl_flds[0]["id"]["name"]
        dip_dir_alias = self.sol_tbl_flds[1]["dip_dir"]["name"]
        dip_ang_alias = self.sol_tbl_flds[2]["dip_ang"]["name"]

        # get selected records attitudes

        selected_ids = get_selected_recs_ids(self.selection_model)

        # create query string

        if not selected_ids:
            qry = query_solutions_all_template.format(
                dip_dir_alias,
                dip_ang_alias,
                self.solutions_tblnm)
        else:
            selected_ids_string = ",".join(map(str, selected_ids))
            qry = query_solutions_selection_template.format(
                dip_dir_alias, dip_ang_alias, self.solutions_tblnm, id_alias, selected_ids_string)

        # query the database

        success, query_results = try_execute_query_with_qt(
            query=qry)
        if not success:
            QMessageBox.critical(
                self,
                self.tool_nm,
                query_results)
            return

        # get vals for selected records

        planes = []
        while query_results.next():
            dip_dir = float(query_results.value(0))
            dip_ang = float(query_results.value(1))
            planes.append(Plane(dip_dir, dip_ang))

        # plot in stereoplot

        selected_recs_stereonet_dialog = SelectedSolutionsStereonetDialog(
            tool_nm=self.tool_nm,
            planes=planes,
            parent=self)

        selected_recs_stereonet_dialog.show()
        selected_recs_stereonet_dialog.raise_()
        selected_recs_stereonet_dialog.activateWindow()

    def delete_selected_records(self):

        if not self.selection_model:
            QMessageBox.warning(
                self,
                self.tool_nm,
                msg_database_missing
            )
            return

        selected_ids = get_selected_recs_ids(self.selection_model)
        if not selected_ids:
            QMessageBox.warning(
                self,
                "Delete records",
                "No selected records")
            return

        num_sel_recs = len(selected_ids)
        if num_sel_recs == 0:
            QMessageBox.warning(
                self,
                "Delete records",
                "No selected records")
            return
        else:
            msg = "<font color=red>Delete {} record(s)?</font>".format(num_sel_recs)
            if QMessageBox.question(self, "Delete solution", msg,
                    QMessageBox.Yes|QMessageBox.No) == QMessageBox.No:
                return

        self.solutionsView.setSortingEnabled(False)
        self.solutionsModel.beginResetModel()

        # create query string

        selected_ids_string = ",".join(map(str, selected_ids))
        query = QSqlQuery(db=QSqlDatabase.database())
        query.exec_("DELETE FROM {} WHERE id_sol IN ({})".format(
            self.pts_tbl_nm,
            selected_ids_string))
        for index in self.solutionsView.selectedIndexes():
            self.solutionsModel.removeRow(index.row())

        self.solutionsModel.submitAll()
        QSqlDatabase.database().commit()

        self.solutionsModel.endResetModel()

        self.solutionsView.setSortingEnabled(True)
        self.solutionsView.update()

    def xprt_selected_records(self):

        if not self.selection_model:
            QMessageBox.warning(
                self,
                self.tool_nm,
                msg_database_missing
            )
            return

        # get selected records attitudes

        selected_ids = get_selected_recs_ids(self.selection_model)

        if not selected_ids or len(selected_ids) == 0:
            QMessageBox.warning(
                self,
                self.tool_nm,
                "No records to export"
            )
            return

        dialog = ExportDialog(
            self.get_project_crs())

        if dialog.exec_():
            if dialog.pt_shape_choice.isChecked():
                geom_type = "point"
            elif dialog.ln_shape_choice.isChecked():
                geom_type = "line"
            file_path = dialog.result_shapefile.text()
            if file_path == "":
                QMessageBox.critical(
                    self,
                    "Point shapefile",
                    "No shapefile path provided in Configurations")
                return
            else:
                pass
        else:
            return

        if not os.path.exists(file_path):

            if geom_type == "point":
                ogr_geom_type = ogr.wkbPoint
            elif geom_type == "line":
                ogr_geom_type = ogr.wkbLineString
            else:
                QMessageBox.critical(
                    self,
                    self.tool_nm,
                    "Error: debug <geom_type>: {}".format(geom_type))
                return

            shape_pars = get_out_shape_params(geom_type)
            if not shape_pars:
                QMessageBox.critical(
                    self,
                    self.tool_nm,
                    "Error: debug <shape_pars>: {}".format(shape_pars))
                return

            shapefile_create(
                path=file_path,
                geom_type=ogr_geom_type,
                fields_dict_list=shape_pars,
                crs=str(self.get_project_crs()))

        # create query string

        if geom_type == "point":

            if not selected_ids:
                qry_solutions = xprt_shppt_select_all_results
            else:
                selected_ids_string = ",".join(map(str, selected_ids))
                qry_solutions = xprt_shppt_select_part_results.format(
                    selected_ids_string)
                print(qry_solutions)

            # query the database

            db_path = self.result_db_path_qle.text()
            success, solutions = try_execute_query_with_sqlite3(
                db_path=db_path,
                query=qry_solutions)
            if not success:
                QMessageBox.critical(
                    self,
                    self.tool_nm,
                    solutions)
                return

        elif geom_type == "line":

            # create query string

            if selected_ids:
                ids = selected_ids
            else:
                success, cntn = try_execute_query_with_qt(
                    query=select_all_solutions_ids)
                if not success:
                    QMessageBox.critical(
                        self,
                        self.tool_nm,
                        cntn)
                    return
                else:
                    query_results = cntn

                # get ids for selected records

                ids = []
                while query_results.next():
                    id = int(query_results.value(0))
                    ids.append(id)

            id_pts = {}
            for id in ids:

                sol_vals_qr = select_solution_pars_template.format(id)
                success, cntn = try_execute_query_with_qt(
                    query=sol_vals_qr)
                if not success:
                    QMessageBox.critical(
                        self,
                        self.tool_nm,
                        cntn)
                    return
                else:
                    cntn.first()
                    dip_dir = cntn.value(0)
                    dip_ang = cntn.value(1)
                    dataset = cntn.value(2)
                    notes = cntn.value(3)
                    src_crs = cntn.value(4)
                    creat_time = cntn.value(5)

                    id_pts[id] = dict(vals=(
                        id,
                        dip_dir,
                        dip_ang,
                        dataset,
                        notes,
                        src_crs,
                        creat_time))

                sol_pts_qr = xprt_shpln_select_sol_pts_pars_template.format(id)
                success, cntn = try_execute_query_with_qt(
                    query=sol_pts_qr)
                if not success:
                    QMessageBox.critical(
                        self,
                        self.tool_nm,
                        cntn)
                    return

                # get ids for selected records

                sol_ixzs = []
                while cntn.next():
                    x, y, z = cntn.value(0), cntn.value(1), cntn.value(2)
                    sol_ixzs.append((x, y, z))

                id_pts[id]["pts"] = sol_ixzs

        else:

            QMessageBox.critical(
                self,
                self.tool_nm,
                "Error - debug with geom_type: {}".format(geom_type))

        # save results in export dataset

        if geom_type == "point":

            success, msg = try_xprt_selected_records_to_pt_shapefile(file_path, solutions)

        elif geom_type == "line":

            success, msg = try_xprt_selected_records_to_ln_shapefile(file_path, id_pts)

        else:

            QMessageBox.critical(
                self,
                self.tool_nm,
                "Error - debug with geom_type = {}".format(geom_type))
            return

        info = QMessageBox.information if success else QMessageBox.warning

        info(
            self,
            self.tool_nm,
            msg)


class SolutionStereonetDialog(QDialog):

    def __init__(self, tool_nm, plane, points, result_db_path, db_tables_params, prj_crs, parent=None):

        super().__init__(parent)

        self.tool_nm = tool_nm
        self.plane = plane
        self.pts = points
        self.db_path = result_db_path
        self.db_tables_params = db_tables_params
        self.prj_crs = prj_crs
        self.plugin_fldrpth = os.path.dirname(__file__)

        layout = QVBoxLayout()

        solution_wdg = QPlainTextEdit("Solution: {:05.1f}, {:04.1f}".format(*plane.dda))
        solution_wdg.setMaximumHeight(40)
        layout.addWidget(solution_wdg)
        pts_str = "\n".join(map(lambda pt: "{}, {}, {}".format(*pt), points))
        layout.addWidget(QPlainTextEdit("Source points:\nx, y, z\n{}".format(pts_str), self))
        mpl_widget = MplWidget(window_title="Stereoplot", type="Stereonet", data=plane)
        layout.addWidget(mpl_widget)

        save_btn = QPushButton("Save solution")
        save_btn.clicked.connect(self.save_solution)
        layout.addWidget(save_btn)

        self.setLayout(layout)

        self.setWindowTitle("Best fit plane solution")

    def save_solution(self):

        if not self.db_path:
            QMessageBox.warning(
                self,
                self.tool_nm,
                "Result database not defined in 'Configurations' tab"
            )
            return

        pars = parse_db_params(self.db_tables_params)

        sol_tbl_nm, sol_tbl_flds, pts_tbl_nm, pts_tbl_flds = pars

        noteDialog = SolutionNotesDialog(self.plugin_fldrpth, parent=self)

        if noteDialog.exec_():

            dataset = noteDialog.label.toPlainText()
            notes = noteDialog.comments.toPlainText()

            conn = sqlite3.connect(self.db_path)
            curs = conn.cursor()

            # Insert a row of data

            values = [None, self.plane.dd, self.plane.da, dataset, notes, str(self.prj_crs), dt.now()]
            curs.execute("INSERT INTO {} VALUES (?, ?, ?, ?, ?, ?, ?)".format(sol_tbl_nm), values)

            # Get the max id of the saved solution

            id_fld_alias = get_field_dict('id', sol_tbl_flds)["name"]
            creat_time_alias = get_field_dict('creat_time', sol_tbl_flds)["name"]
            query_sol_id = query_sol_id_template.format(
                id=id_fld_alias,
                creat_time=creat_time_alias,
                solutions=sol_tbl_nm)
            curs.execute(query_sol_id)
            last_sol_id = curs.fetchone()[0]

            # Create the query strings for updating the points table

            pts_vals = list(map(lambda idxyzlonlat: [None, last_sol_id, *idxyzlonlat], self.pts))

            curs.executemany("INSERT INTO {} VALUES (?, ?, ?, ?, ?, ?, ?, ?)".format(pts_tbl_nm), pts_vals)

            conn.commit()
            conn.close()

            QMessageBox.information(
                self,
                "{}".format(self.tool_nm),
                "Solution saved in result database")


class SolutionNotesDialog(QDialog):

    def __init__(self, plugin_dir, parent=None):
        super().__init__(parent=parent)
        loadUi(os.path.join(plugin_dir, 'solution_notes.ui'), self)
        self.show()


class SelectedSolutionsStereonetDialog(QDialog):

    def __init__(self, tool_nm, planes, parent=None):

        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.tool_nm = tool_nm
        self.planes = planes
        self.plugin_fldrpth = os.path.dirname(__file__)

        layout = QVBoxLayout()

        mpl_widget = MplWidget(
            window_title="Stereoplot",
            type="Stereonet",
            data=self.planes,
            set_rc_params=False)
        mpl_widget.adjustSize()

        layout.addWidget(mpl_widget)

        solutions_str = "\n".join(list(map(lambda plane: "{:05.1f}, {:04.1f}".format(*plane.dda), self.planes)))
        solutions_wdg = QPlainTextEdit("Solutions:\n{}".format(solutions_str))
        solutions_wdg.setMaximumHeight(140)
        layout.addWidget(solutions_wdg)

        self.setLayout(layout)

        self.setWindowTitle("Selected solutions")


class ExportDialog(QDialog):

    def __init__(self, projectCrs, parent=None):

        super().__init__(parent)

        self.projectCrs = projectCrs

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Export selected results in"))

        self.use_shapefile_pButton = QPushButton("existing shapefile")
        self.use_shapefile_pButton.clicked.connect(self.shapefile_load_existing)
        layout.addWidget(self.use_shapefile_pButton)

        self.create_shapefile_pButton = QPushButton("new shapefile")
        self.create_shapefile_pButton.clicked.connect(self.shapefile_make_new)
        layout.addWidget(self.create_shapefile_pButton)

        self.result_shapefile = QLineEdit()
        layout.addWidget(self.result_shapefile)

        layout.addWidget(QLabel("as"))

        choiceLayout = QHBoxLayout()

        self.pt_shape_choice = QRadioButton("point data")
        self.pt_shape_choice.setChecked(True)
        self.ln_shape_choice = QRadioButton("line data")

        choiceLayout.addWidget(self.pt_shape_choice)
        choiceLayout.addWidget(self.ln_shape_choice)

        layout.addLayout(choiceLayout)

        okButton = QPushButton("&OK")
        cancelButton = QPushButton("Cancel")

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(okButton)
        buttonLayout.addWidget(cancelButton)

        layout.addLayout(buttonLayout)
        self.setLayout(layout)

        okButton.clicked.connect(self.accept)
        cancelButton.clicked.connect(self.reject)

        self.setWindowTitle("Export")

    def shapefile_make_new(self):

        shapefile_path = define_path_new_file(
            self,
            "Choose shapefile name",
            "*.shp",
            "shp (*.shp *.SHP)")

        self.result_shapefile.setText(shapefile_path)

    def shapefile_load_existing(self):

        shapefile_path = old_file_path(
            self,
            "Choose shapefile name",
            "*.shp",
            "shp (*.shp *.SHP)")

        self.result_shapefile.setText(shapefile_path)


