# -*- coding: utf-8 -*-


from typing import List, Tuple, Dict, Optional, Union

from PyQt5.QtCore import QItemSelectionModel
from PyQt5.QtSql import QSqlDatabase


def try_open_sqlite3_db(db_path: str, conn_type: str= "readwrite") -> Tuple[bool, Union[str, QSqlDatabase]]:
    """
    Open ans sqlite3 database for reading/writing, based on connection option.

    :param db_path: the path to the database.
    :type db_path: str.
    :param conn_type: the connection type, i.e. for reading/writing.
    :type conn_type: str.
    :return: the success status and a message error or a QSqlDatabase instance.
    :rtype: a tuple made up by a boolean and a string or a QSqlDatabase instance.
    """

    try:

        if conn_type == "readonly":
            conn_opt_str = "QSQLITE_OPEN_READONLY;"
        elif conn_type == "readwrite":
            conn_opt_str = "SQLITE_OPEN_READWRITE;"
        else:
            raise Exception("Unimplemented connection option")

        db = QSqlDatabase("QSQLITE")
        db.setConnectOptions(conn_opt_str)
        db.setDatabaseName(db_path)
        db.open()

        return True, db

    except Exception as e:

        return False, "Exception: {}".format(e)


def get_selected_recs_ids(selection_model: QItemSelectionModel) -> Optional[Tuple[int, ...]]:
    """
    Get integer ids from selected records.

    :param selection_model: the selection model.
    :type selection_model: QItemSelectionModel.
    :return: the sequence of ids.
    :rtype: tuple of integers.
    """

    # get selected records attitudes

    selected_records = selection_model.selectedRows()

    if not selected_records:
        return None

    selected_ids = tuple(map(lambda qmodel_ndx: qmodel_ndx.data(), selected_records))

    return selected_ids

