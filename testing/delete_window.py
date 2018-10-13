
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


class ListModel(QAbstractListModel):

    def __init__(self, colors=None):

        super(QAbstractListModel, self).__init__()
        self._datas = colors

    def data(self, index: QModelIndex, role=None):

        row = index.row()
        value = self._datas[row]

        if role == Qt.DisplayRole:

            return value.name()

        elif role == Qt.DecorationRole:

            pixmap = QPixmap(20, 20)
            pixmap.fill(value)
            icon = QPixmap(pixmap)
            return icon

        elif role == Qt.ToolTipRole:

            return "Hex code: " + self._datas[row].name()

    def rowCount(self, parent=None, *args, **kwargs):

        return len(self._datas)

    def headerData(self, p_int, Qt_Orientation, role=None):

        if role == Qt.DisplayRole:
            if Qt_Orientation == Qt.Horizontal:
                return "Palette"
            else:
                return "Color {a}".format(a=p_int)

    def flags(self, QModelIndex: QModelIndex):

        # check state editable or not?
        return Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsEnabled

    @pyqtSlot()
    def setData(self, QModelIndex, Any, role=None):

        if role == Qt.EditRole:
            row = QModelIndex.row()
            color = QColor(Any)
            if color.isValid():
                self._datas[row] = color
                self.dataChanged.emit(QModelIndex, QModelIndex, [])
                return True
        return False


class TableModel(QAbstractTableModel):

    def __init__(self, colors=None):

        super().__init__()
        self._datas = colors

    def data(self, index: QModelIndex, role=None):

        row = index.row()
        value = self._datas[row]

        if role == Qt.DisplayRole:

            return value.name()

        elif role == Qt.DecorationRole:

            pixmap = QPixmap(20, 20)
            pixmap.fill(value)
            icon = QPixmap(pixmap)
            return icon

        elif role == Qt.ToolTipRole:

            return "Hex code: " + self._datas[row].name()

    def rowCount(self, parent=None, *args, **kwargs):

        return len(self._datas)

    def headerData(self, p_int, Qt_Orientation, role=None):

        if role == Qt.DisplayRole:
            if Qt_Orientation == Qt.Horizontal:
                return "Palette"
            else:
                return "Color {a}".format(a=p_int)

    def flags(self, QModelIndex: QModelIndex):

        # check state editable or not?
        return Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsEnabled

    @pyqtSlot()
    def setData(self, QModelIndex, Any, role=None):

        if role == Qt.EditRole:
            row = QModelIndex.row()
            color = QColor(Any)
            if color.isValid():
                self._datas[row] = color
                self.dataChanged.emit(QModelIndex, QModelIndex, [])
                return True
        return False


def delete_selected_records():

    # get selected records attitudes

    selected_ids = get_selected_recs_ids(selection_model)

    # create query string

    if not selected_ids:
        return

    selected_ids_string = ",".join(map(str, selected_ids))

    qry = "DELETE FROM {} WHERE {} IN ({})".format(
        sol_tbl_nm,
        id_alias,
        selected_ids_string)

    success, msg = try_execute_query_with_qt(qry)

    if not success:
        return
    else:
        table_model.dataChanged.emit(
            table_model.createIndex(0, 0),
            table_model.createIndex(table_model.rowCount() - 1, table_model.columnCount() - 1),
            [])
        print("Emitted")

        """
        # from: https://stackoverflow.com/questions/12893904/automatically-refreshing-a-qtableview-when-data-changed
        QModelIndex topLeft = index(0, 0);
        QModelIndex bottomRight = index(rowCount() - 1, columnCount() - 1);

        emit dataChanged(topLeft, bottomRight);
        emit layoutChanged();

        table_model.rowCount() - 1, table_model.columnCount() - 1
        """
        """
        self.dataChanged.emit(QModelIndex, QModelIndex, [])"""
        """
        void QAbstractItemModel::dataChanged(const QModelIndex &topLeft, const QModelIndex &bottomRight, const QVector<int> &roles = ...)"""


if __name__ == '__main__':

    # get relevant fields names

    src_db_pth = "/home/mauro/Temp/results/results_10.sqlite3"

    table_nm = "solutions"

    fields = [('id', 'INTEGER PRIMARY KEY'),
              ('dip_dir', 'REAL'),
              ('dip_ang', 'REAL'),
              ('label', 'TEXT'),
              ('comments', 'TEXT'),
              ('creat_time', 'DATE')]

    sol_tbl_nm = "solutions"
    id_alias = "id"

    #

    app = QApplication(sys.argv)

    success, msg = try_connect_to_sqlite3_db_with_qt(
        db_path=src_db_pth,
        conn_type="readonly")

    if not success:
        print("Error: {}".format(msg))
        sys.exit()

    db = QSqlDatabase.database()

    table_model = QSqlTableModel(db=db)
    table_model.setTable(sol_tbl_nm)
    table_model.select()
    table_model.setHeaderData(0, Qt.Horizontal, "id")
    table_model.setHeaderData(1, Qt.Horizontal, "dip direction")
    table_model.setHeaderData(2, Qt.Horizontal, "dip angle")
    table_model.setHeaderData(3, Qt.Horizontal, "label")
    table_model.setHeaderData(4, Qt.Horizontal, "comments")
    table_model.setHeaderData(5, Qt.Horizontal, "created")

    proxy_model = QSortFilterProxyModel()
    proxy_model.setSourceModel(table_model)

    view = QTableView()
    view.setModel(proxy_model)

    view.verticalHeader().hide()
    view.setSelectionBehavior(QAbstractItemView.SelectRows)

    selection_model = view.selectionModel()

    view.resizeRowsToContents()
    view.setSortingEnabled(True)

    layout = QVBoxLayout()

    layout.addWidget(view)

    delete_selected_recs = QPushButton("Delete selected records")
    delete_selected_recs.clicked.connect(delete_selected_records)
    layout.addWidget(delete_selected_recs)

    widg = QDialog()
    widg.setLayout(layout)


    """
    yellow = QColor(255, 255, 0)

    colors = [red, green, blue, yellow]

    model = ListModel(colors)

    tableView = QTableView()
    tableView.setModel(model)
    tableView.setWindowTitle('Table view')
    """

    widg.show()

    sys.exit(app.exec_())

