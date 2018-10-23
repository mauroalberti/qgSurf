
# modified from assetmanager.pyw by Summerfield

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

import os
import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtSql import *
import resources


from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtSql import *
from PyQt5.QtSql import QSqlDatabase

#from PyQt5.QtWidgets import QApplication

import sys
sys.path.append("/home/mauro/Documents/projects/qgSurf/")
from pygsf.libs_utils.qt.filesystem import define_path_new_file, old_file_path
from pygsf.libs_utils.qt.databases import try_connect_to_sqlite3_db_with_qt, get_selected_recs_ids
from pygsf.libs_utils.gdal.exceptions import OGRIOException
from pygsf.libs_utils.gdal.ogr import shapefile_create
from pygsf.libs_utils.gdal.gdal import try_read_raster_band

from pygsf.libs_utils.mpl.mpl_widget import MplWidget
from pygsf.spatial.rasters.geoarray import GeoArray
from pygsf.orientations.orientations import *
from pygsf.mathematics.arrays import xyzSvd

from pygsf.libs_utils.sqlite.sqlite3 import try_create_db_tables, try_execute_query_with_sqlite3
from pygsf.libs_utils.qt.databases import try_execute_query_with_qt


class MainForm(QDialog):

    def __init__(self, db, sol_tbl_nm, solutions_fields):

        super().__init__()

        ID, DIP_DIR, DIP_ANG, LABEL, COMMENTS, CREAT_TIME = range(len(solutions_fields))

        solutionsModel = QSqlRelationalTableModel(db=db)
        solutionsModel.setTable(sol_tbl_nm)
        """
        solutionsModel.setRelation(
            ID,
            QSqlRelation("src_points", "id", "name"))
        """
        # solutionsModel.setSort(ROOM, Qt.AscendingOrder)

        solutionsModel.setHeaderData(ID, Qt.Horizontal, QVariant("id"))
        solutionsModel.setHeaderData(DIP_DIR, Qt.Horizontal, QVariant("dip direction"))
        solutionsModel.setHeaderData(DIP_ANG, Qt.Horizontal, QVariant("dip angle"))
        solutionsModel.setHeaderData(LABEL, Qt.Horizontal, QVariant("label"))
        solutionsModel.setHeaderData(COMMENTS, Qt.Horizontal, QVariant("comments"))
        solutionsModel.setHeaderData(CREAT_TIME, Qt.Horizontal, QVariant("created"))

        solutionsModel.select()

        solutionsView = QTableView()
        solutionsView.setModel(solutionsModel)
        # solutionsView.setItemDelegate(AssetDelegate(self))
        solutionsView.setSelectionMode(QTableView.SingleSelection)
        solutionsView.setSelectionBehavior(QTableView.SelectRows)
        solutionsView.setColumnHidden(ID, True)
        solutionsView.resizeColumnsToContents()
        assetLabel = QLabel("&Solutions")
        assetLabel.setBuddy(solutionsView)


if __name__ == "__main__":

    # get relevant fields names

    src_db_pth = "/home/mauro/Temp/results/results_10.sqlite3"

    sol_tbl_nm = "solutions"

    solutions_fields = [('id', 'INTEGER PRIMARY KEY'),
                        ('dip_dir', 'REAL'),
                        ('dip_ang', 'REAL'),
                        ('label', 'TEXT'),
                        ('comments', 'TEXT'),
                        ('creat_time', 'DATE')]

    id_alias = solutions_fields[0][0]



    #

    app = QApplication(sys.argv)

    success, msg = try_connect_to_sqlite3_db_with_qt(
        db_path=src_db_pth,
        conn_type="readonly")

    if not success:
        print("Error: {}".format(msg))
        sys.exit()

    db = QSqlDatabase.database()

    form = MainForm(
        db=db,
        sol_tbl_nm=sol_tbl_nm,
        solutions_fields=solutions_fields
    )
    form.show()

    app.exec_()

    del form
    del db
