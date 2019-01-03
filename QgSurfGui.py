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

# -*- coding: utf-8 -*-

from __future__ import absolute_import

from builtins import object

import os

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *

from . import resources

from .config.general_params import *

from .BestFitPlaneTool import BestFitPlaneMainWidget
from .DEMPlaneIntersectionTool import DemPlaneIntersectionWidget
from .PtsPlnDistances import PtsPlnDistancesWidget
from .StereoplotTool import StereoplotWidget
from .AboutDialog import AboutDialog

from .pygsf.libs_utils.qt.tools import *
from .pygsf.libs_utils.yaml.io import read_yaml


class QgSurfGui(object):

    def __init__(self, interface):

        self.plugin_folder = os.path.dirname(__file__)
        self.config_fldrpth = os.path.join(
            self.plugin_folder,
            config_fldr)

        plugin_config_file = os.path.join(
            self.config_fldrpth,
            plugin_params_flnm)

        dPluginParams = read_yaml(plugin_config_file)

        self.version = dPluginParams["version"]
        self.tools = dPluginParams["tools"]

        self.bestfitplane_toolpars = self.tools["bestfitplane_tool_params"]
        self.demplaneinters_toolpars = self.tools["demplaneinters_tool_params"]
        self.pointsplanedistances_toolpars = self.tools["pointsplanedistances_tool_params"]
        self.stereonet_toolpars = self.tools["stereonet_tool_params"]
        self.about_toolpars = self.tools["about_dlg_params"]

        db_config_file = os.path.join(
            self.config_fldrpth,
            db_params_flnm)
        db_params = read_yaml(db_config_file)
        self.sqlite_db_params = db_params["sqlite_db"]

        self.bPtsPlaneDistsWidgetOpen = False
        self.bStereoplotWidgetOpen = False

        self.interface = interface
        self.main_window = self.interface.mainWindow()
        self.canvas = self.interface.mapCanvas()

    def initGui(self):

        self.bestfitplane_geoproc = make_qaction(
            tool_params=self.bestfitplane_toolpars,
            plugin_nm=plugin_nm,
            icon_fldr=icon_fldr,
            parent=self.main_window)
        self.bestfitplane_geoproc.triggered.connect(self.RunBestFitPlaneGeoproc)
        self.interface.addPluginToMenu(
            plugin_nm,
            self.bestfitplane_geoproc)

        self.demplaneinters_geoproc = make_qaction(
            tool_params=self.demplaneinters_toolpars,
            plugin_nm=plugin_nm,
            icon_fldr=icon_fldr,
            parent=self.main_window)
        self.demplaneinters_geoproc.triggered.connect(self.RunDemPlaneIntersectionGeoproc)
        self.interface.addPluginToMenu(
            plugin_nm,
            self.demplaneinters_geoproc)

        self.pointsplanedistances_geoproc = make_qaction(
            tool_params=self.pointsplanedistances_toolpars,
            plugin_nm=plugin_nm,
            icon_fldr=icon_fldr,
            parent=self.main_window)
        self.pointsplanedistances_geoproc.triggered.connect(self.RunPointsPlaneDistancesGeoproc)
        self.interface.addPluginToMenu(
            plugin_nm,
            self.pointsplanedistances_geoproc)

        self.stereonet_geoproc = make_qaction(
            tool_params=self.stereonet_toolpars,
            plugin_nm=plugin_nm,
            icon_fldr=icon_fldr,
            parent=self.main_window)
        self.stereonet_geoproc.triggered.connect(self.RunStereonetGeoproc)
        self.interface.addPluginToMenu(
            plugin_nm,
            self.stereonet_geoproc)

        self.qgsurf_about = make_qaction(
            tool_params=self.about_toolpars,
            plugin_nm=plugin_nm,
            icon_fldr=icon_fldr,
            parent=self.main_window)
        self.qgsurf_about.triggered.connect(self.RunQgsurfAbout)
        self.interface.addPluginToMenu(
            plugin_nm,
            self.qgsurf_about)

        self.geoprocessings = [
            self.bestfitplane_geoproc,
            self.demplaneinters_geoproc,
            self.pointsplanedistances_geoproc,
            self.stereonet_geoproc,
            self.qgsurf_about]

    def RunBestFitPlaneGeoproc(self):

        BestFitPlaneDockWidget = QDockWidget(
            "{} - {}".format(plugin_nm, self.bestfitplane_toolpars["tool_nm"]),
            self.interface.mainWindow())
        BestFitPlaneDockWidget.setAttribute(Qt.WA_DeleteOnClose)
        BestFitPlaneDockWidget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        self.BestFitPlaneQwidget = BestFitPlaneMainWidget(
            tool_nm=self.bestfitplane_toolpars["tool_nm"],
            canvas=self.canvas,
            plugin_qaction=self.bestfitplane_geoproc,
            db_tables_params=self.sqlite_db_params)
        BestFitPlaneDockWidget.setWidget(self.BestFitPlaneQwidget)
        BestFitPlaneDockWidget.destroyed.connect(self.BestFitPlaneCloseEvent)
        self.interface.addDockWidget(Qt.RightDockWidgetArea, BestFitPlaneDockWidget)

    def RunDemPlaneIntersectionGeoproc(self):

        DemPlaneIntersectionDockWidget = QDockWidget(
            "{} - {}".format(plugin_nm, self.demplaneinters_toolpars["tool_nm"]),
            self.interface.mainWindow())
        DemPlaneIntersectionDockWidget.setAttribute(Qt.WA_DeleteOnClose)
        DemPlaneIntersectionDockWidget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        self.DemPlaneIntersectionQwidget = DemPlaneIntersectionWidget(
            tool_nm=self.demplaneinters_toolpars["tool_nm"],
            canvas=self.canvas,
            plugin_qaction=self.demplaneinters_geoproc)
        DemPlaneIntersectionDockWidget.setWidget(self.DemPlaneIntersectionQwidget)
        DemPlaneIntersectionDockWidget.destroyed.connect(self.DemPlaneIntersectionCloseEvent)
        self.interface.addDockWidget(Qt.RightDockWidgetArea, DemPlaneIntersectionDockWidget)

    def RunPointsPlaneDistancesGeoproc(self):

        if self.bPtsPlaneDistsWidgetOpen:
            self.warn("Points-plane distances widget already open")
            return

        self.wdgtPtsPlnDistances = PtsPlnDistancesWidget(self.canvas, plugin_nm)
        self.wdgtPtsPlnDistances.sgnWindowClosed.connect(self.ptsplndist_off)
    
        settings = QSettings(settings_name, plugin_nm)
        if settings.contains("PtsPlnDistancesWidget/size") and settings.contains("PtsPlnDistancesWidget/position"):
            size = settings.value("PtsPlnDistancesWidget/size", None)
            pos = settings.value("PtsPlnDistancesWidget/position", None)
            self.wdgtPtsPlnDistances.resize(size)
            self.wdgtPtsPlnDistances.move(pos)
            self.wdgtPtsPlnDistances.show()
        else:
            self.wdgtPtsPlnDistances.show()
    
        self.bPtsPlaneDistsWidgetOpen = True
    
    def RunStereonetGeoproc(self):

        if self.bStereoplotWidgetOpen:
            self.warn("Geologic stereonets widget already open")
            return

        dwgtStereoplotDockWidget = QDockWidget(
            "{} - {}".format(plugin_nm, self.stereonet_toolpars["tool_nm"]),
            self.interface.mainWindow())
        dwgtStereoplotDockWidget.setAttribute(Qt.WA_DeleteOnClose)
        dwgtStereoplotDockWidget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        self.wdgtStereoplot = StereoplotWidget(
            tool_nm=self.stereonet_toolpars["tool_nm"],
            canvas=self.canvas,
            settings_name=settings_name)

        dwgtStereoplotDockWidget.setWidget(self.wdgtStereoplot)
        dwgtStereoplotDockWidget.destroyed.connect(self.StereoplotCloseEvent)
        self.interface.addDockWidget(Qt.RightDockWidgetArea, dwgtStereoplotDockWidget)

        self.bStereoplotWidgetOpen = True

    def RunQgsurfAbout(self):

        qgsurf_about_dlg = AboutDialog(
            version=self.version)

        qgsurf_about_dlg.show()
        qgsurf_about_dlg.exec_()

    def BestFitPlaneCloseEvent(self, event):

        for mrk in self.BestFitPlaneQwidget.bestfitplane_point_markers:
            self.BestFitPlaneQwidget.canvas.scene().removeItem(mrk)

        try:
            QgsProject.instance().layerWasAdded.disconnect(self.BestFitPlaneQwidget.refresh_raster_layer_list)
        except:
            pass

        try:
            QgsProject.instance().layerRemoved.disconnect(self.BestFitPlaneQwidget.refresh_raster_layer_list)
        except:
            pass

        try:
            self.BestFitPlaneQwidget.bestfitplane_PointMapTool.canvasClicked.disconnect(
                self.BestFitPlaneQwidget.set_bfp_input_point)
        except:
            pass

        try:
            QgsProject.instance().layerWasAdded.disconnect(self.BestFitPlaneQwidget.refresh_inpts_layer_list)
        except:
            pass

        try:
            QgsProject.instance().layerRemoved.disconnect(self.BestFitPlaneQwidget.refresh_inpts_layer_list)
        except:
            pass

        try:
            self.BestFitPlaneQwidget.bestfitplane_PointMapTool.leftClicked.disconnect(
                self.BestFitPlaneQwidget.set_bfp_input_point)
        except:
            pass

    def DemPlaneIntersectionCloseEvent(self, event):

        for mrk in self.DemPlaneIntersectionQwidget.intersections_markers_list:
            self.DemPlaneIntersectionQwidget.canvas.scene().removeItem(mrk)

        for mrk in self.DemPlaneIntersectionQwidget.source_point_marker_list:
            self.DemPlaneIntersectionQwidget.canvas.scene().removeItem(mrk)
            
        try:
            self.DemPlaneIntersectionQwidget.intersection_PointMapTool.canvasClicked.disconnect(self.DemPlaneIntersectionQwidget.update_intersection_point_pos)
        except:
            pass

    def StereoplotCloseEvent(self):

        self.bStereoplotWidgetOpen = False

    def ptsplndist_off(self):

        self.bPtsPlaneDistsWidgetOpen = False

    def info(self, msg):

        QMessageBox.information(None, plugin_nm, msg)

    def warn(self, msg):

        QMessageBox.warning(None, plugin_nm, msg)

    def unload(self):

        for geoprocessing in self.geoprocessings:

            self.interface.removePluginMenu(
                plugin_nm,
                geoprocessing)





        

