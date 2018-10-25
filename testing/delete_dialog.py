
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


from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtSql import *
from PyQt5.QtSql import QSqlDatabase

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


import resources


MAC = "qt_mac_set_native_menubar" in dir()


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

ID_SOL, DIP_DIR, DIP_ANG, LABEL, COMMENTS, CREAT_TIME = range(len(solutions_fields))

src_pts_tbl_nm = "src_points"

ID_PT, FK_ID_SOL, X, Y, Z = range(5)


class MainForm(QDialog):

    def __init__(self, db, solutions_tblnm, srcpts_tblnm):

        super().__init__()

        self.solutionsModel = QSqlTableModel(db=db)
        self.solutionsModel.setTable(solutions_tblnm)
        """
        self.solutionsModel.setRelation(
            ID,
            QSqlRelation("src_points", "id", "name"))
        """
        # self.solutionsModel.setSort(ROOM, Qt.AscendingOrder)

        self.solutionsModel.setHeaderData(ID_SOL, Qt.Horizontal, QVariant("id"))
        self.solutionsModel.setHeaderData(DIP_DIR, Qt.Horizontal, QVariant("dip direction"))
        self.solutionsModel.setHeaderData(DIP_ANG, Qt.Horizontal, QVariant("dip angle"))
        self.solutionsModel.setHeaderData(LABEL, Qt.Horizontal, QVariant("label"))
        self.solutionsModel.setHeaderData(COMMENTS, Qt.Horizontal, QVariant("comments"))
        self.solutionsModel.setHeaderData(CREAT_TIME, Qt.Horizontal, QVariant("created"))

        self.solutionsModel.select()

        self.solutionsView = QTableView()
        self.solutionsView.setModel(self.solutionsModel)
        # self.solutionsView.setItemDelegate(AssetDelegate(self))
        self.solutionsView.setSelectionMode(QTableView.SingleSelection)
        self.solutionsView.setSelectionBehavior(QTableView.SelectRows)
        self.solutionsView.setColumnHidden(ID_SOL, True)
        self.solutionsView.resizeColumnsToContents()
        solutionsLabel = QLabel("&Solutions")
        solutionsLabel.setBuddy(self.solutionsView)

        self.srcptsModel = QSqlTableModel(self)
        self.srcptsModel.setTable(srcpts_tblnm)
        """
        self.srcptsModel.setRelation(ACTIONID,
                QSqlRelation("actions", "id", "name"))
        """
        #self.srcptsModel.setSort(DATE, Qt.AscendingOrder)

        self.srcptsModel.setHeaderData(ID_PT, Qt.Horizontal,
                QVariant("id"))
        self.srcptsModel.setHeaderData(FK_ID_SOL, Qt.Horizontal,
                QVariant("id_sol"))
        self.srcptsModel.setHeaderData(X, Qt.Horizontal,
                QVariant("x"))
        self.srcptsModel.setHeaderData(Y, Qt.Horizontal,
                QVariant("y"))
        self.srcptsModel.setHeaderData(Z, Qt.Horizontal,
                QVariant("z"))
        self.srcptsModel.select()

        self.srcptsView = QTableView()
        self.srcptsView.setModel(self.srcptsModel)
        #self.srcptsView.setItemDelegate(LogDelegate(self))
        self.srcptsView.setSelectionMode(QTableView.SingleSelection)
        self.srcptsView.setSelectionBehavior(QTableView.SelectRows)
        self.srcptsView.setColumnHidden(ID_PT, True)
        self.srcptsView.setColumnHidden(FK_ID_SOL, True)
        self.srcptsView.resizeColumnsToContents()
        self.srcptsView.horizontalHeader().setStretchLastSection(True)
        srcptsLabel = QLabel("Source &points")
        srcptsLabel.setBuddy(self.srcptsView)

        dataLayout = QVBoxLayout()
        dataLayout.addWidget(solutionsLabel)
        dataLayout.addWidget(self.solutionsView, 1)
        dataLayout.addWidget(srcptsLabel)
        dataLayout.addWidget(self.srcptsView)

        deleteSolutionButton = QPushButton("&Delete solution")
        quitButton = QPushButton("&Quit")
        for button in (deleteSolutionButton,
                       quitButton):
            if MAC:
                button.setDefault(False)
                button.setAutoDefault(False)
            else:
                button.setFocusPolicy(Qt.NoFocus)

        buttonLayout = QVBoxLayout()
        #buttonLayout.addWidget(addAssetButton)
        buttonLayout.addWidget(deleteSolutionButton)
        #buttonLayout.addWidget(addActionButton)
        #buttonLayout.addWidget(deleteActionButton)
        #buttonLayout.addWidget(editActionsButton)
        #buttonLayout.addWidget(editCategoriesButton)
        buttonLayout.addStretch()
        buttonLayout.addWidget(quitButton)

        layout = QHBoxLayout()
        layout.addLayout(dataLayout, 1)
        layout.addLayout(buttonLayout)
        self.setLayout(layout)

        self.solutionsView.selectionModel().currentRowChanged.connect(self.solutionChanged)

        """
        self.connect(addAssetButton, SIGNAL("clicked()"),
                     self.addAsset)
        """
        deleteSolutionButton.clicked.connect(self.deleteSolution)
        """
        self.connect(addActionButton, SIGNAL("clicked()"),
                     self.addAction)
        self.connect(deleteActionButton, SIGNAL("clicked()"),
                     self.deleteAction)
        self.connect(editActionsButton, SIGNAL("clicked()"),
                     self.editActions)
        self.connect(editCategoriesButton, SIGNAL("clicked()"),
                     self.editCategories)
        """
        quitButton.clicked.connect(self.done)

        self.solutionChanged(self.solutionsView.currentIndex())
        self.setMinimumWidth(850)
        self.setWindowTitle("Solutions Manager")

    def done(self, result=1):

        query = QSqlQuery()
        query.exec_("DELETE FROM {0} WHERE {0}.id_sol NOT IN"
                    "(SELECT id FROM {1})".format(
            src_pts_tbl_nm,
            sol_tbl_nm))

        QDialog.done(self, 1)

    def deleteSolution(self):

        self.solutionsView.setSortingEnabled(False)
        self.solutionsModel.beginResetModel()

        index = self.solutionsView.currentIndex()
        if not index.isValid():
            print("Index for solution deletion is not valid")
            return
        QSqlDatabase.database().transaction()
        record = self.solutionsModel.record(index.row())
        solution_id = record.value(ID_SOL)  #.toInt()[0]
        point_records = 1
        query = QSqlQuery("SELECT COUNT(*) FROM {} "
                          "WHERE id_sol = {}".format(
            src_pts_tbl_nm,
            solution_id))
        if query.next():
            point_records = query.value(0) #.toInt()[0]
            print("There is/are {} source point(s) to delete for solution id {}".format(
                point_records,
                solution_id))
        msg = "<font color=red>Delete record {}</font>".format(solution_id)
        if point_records > 1:
            msg += ", along with {} point records".format(point_records)
        msg += "?"
        if QMessageBox.question(self, "Delete solution", msg,
                QMessageBox.Yes|QMessageBox.No) == QMessageBox.No:
            QSqlDatabase.database().rollback()
            return
        query.exec_("DELETE FROM {} WHERE id_sol = {}".format(
            src_pts_tbl_nm,
            solution_id))
        self.solutionsModel.removeRow(index.row())
        self.solutionsModel.submitAll()
        QSqlDatabase.database().commit()
        self.solutionsModel.endResetModel()
        self.solutionsView.setSortingEnabled(True)
        self.solutionsView.repaint()
        self.solutionChanged(self.solutionsView.currentIndex())

    def solutionChanged(self, index):

        if index.isValid():
            record = self.solutionsModel.record(index.row())
            id = record.value("id") #.toInt()[0]
            self.srcptsModel.setFilter("id_sol = {}".format(id))
        else:
            self.srcptsModel.setFilter("id_sol = -1")
        #self.srcptsModel.reset()
        self.srcptsModel.select()
        self.srcptsView.horizontalHeader().setVisible(
                self.srcptsModel.rowCount() > 0)


if __name__ == "__main__":

    app = QApplication(sys.argv)

    success, msg = try_connect_to_sqlite3_db_with_qt(
        db_path=src_db_pth,
        conn_type="readwrite")

    if not success:
        print("Error: {}".format(msg))
        sys.exit()

    db = QSqlDatabase.database()

    form = MainForm(
        db=db,
        solutions_tblnm=sol_tbl_nm,
        srcpts_tblnm=src_pts_tbl_nm
    )
    form.show()

    app.exec_()

    del form
    del db
