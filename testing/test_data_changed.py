# from: https://stackoverflow.com/questions/45782296/emit-datachanged-signal-pyqt5?rq=1

from PyQt5 import QtGui, QtCore
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QModelIndex, pyqtSignal, QAbstractListModel, pyqtSlot
import sys


class ListModel(QAbstractListModel):

    def __init__(self, colors=None):

        super(QAbstractListModel, self).__init__()
        self._datas = colors

    def data(self, index: QModelIndex, role=None):

        row = index.row()
        value = self._datas[row]

        if role == QtCore.Qt.DisplayRole:

            return value.name()

        elif role == QtCore.Qt.DecorationRole:

            pixmap = QtGui.QPixmap(20, 20)
            pixmap.fill(value)
            icon = QtGui.QPixmap(pixmap)
            return icon

        elif role == QtCore.Qt.ToolTipRole:

            return "Hex code: " + self._datas[row].name()

    def rowCount(self, parent=None, *args, **kwargs):

        return len(self._datas)

    def headerData(self, p_int, Qt_Orientation, role=None):

        if role == QtCore.Qt.DisplayRole:
            if Qt_Orientation == QtCore.Qt.Horizontal:
                return "Palette"
            else:
                return "Color {a}".format(a=p_int)

    def flags(self, QModelIndex: QModelIndex):

        # check state editable or not?
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

    @pyqtSlot()
    def setData(self, QModelIndex, Any, role=None):

        if role == QtCore.Qt.EditRole:
            row = QModelIndex.row()
            color = QtGui.QColor(Any)
            if color.isValid():
                self._datas[row] = color
                self.dataChanged.emit(QModelIndex, QModelIndex, [])
                return True
        return False


if __name__ == '__main__':

    app = QApplication(sys.argv)

    red = QtGui.QColor(255, 0, 0)
    green = QtGui.QColor(0, 255, 0)
    blue = QtGui.QColor(0, 0, 255)
    yellow = QtGui.QColor(255, 255, 0)

    colors = [red, green, blue, yellow]

    model = ListModel(colors)

    listView = QtWidgets.QListView()
    listView.setModel(model)
    listView.setWindowTitle('List view')
    listView.show()

    treeView = QtWidgets.QTreeView()
    treeView.setModel(model)
    treeView.setWindowTitle('Tree view')
    treeView.show()

    tableView = QtWidgets.QTableView()
    tableView.setModel(model)
    tableView.setWindowTitle('Table view')
    tableView.show()

    sys.exit(app.exec_())

