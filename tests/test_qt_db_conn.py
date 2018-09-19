import sys

from PyQt5.QtCore import Qt
from PyQt5.QtSql import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *


db_path = "/home/mauro/Documents/projects/temp/results/db.sqlite3"
tbl_nm = "solutions"

##


class TableWidget(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout()

        db = QSqlDatabase("QSQLITE")

        db.setConnectOptions("QSQLITE_OPEN_READONLY;")

        db.setDatabaseName(db_path)

        open = db.open()

        print("Open: {}".format(open))

        tables = db.tables()

        print("Tables: {}".format(tables))

        print("Creating model")

        model = QSqlTableModel(db=db)
        model.setTable(tbl_nm)
        model.select()
        model.setHeaderData(0, Qt.Horizontal, "id")
        model.setHeaderData(1, Qt.Horizontal, "dip_dir")
        model.setHeaderData(2, Qt.Horizontal, "dip_ang")
        model.setHeaderData(3, Qt.Horizontal, "label")
        model.setHeaderData(4, Qt.Horizontal, "comments")
        model.setHeaderData(5, Qt.Horizontal, "creat_time")

        view = QTableView()

        view.setModel(model)

        layout.addWidget(view)

        self.setLayout(layout)

        db.close()
        
        print("Db closed")


if __name__ == '__main__':

    app = QApplication(sys.argv)
    window = TableWidget()
    #window.setSourceModel(createMailModel(window))
    window.show()
    sys.exit(app.exec_())


