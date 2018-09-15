

from PyQt5.QtSql import *

db = QSqlDatabase.addDatabase("QSQLITE")


db.setDatabaseName("mynewdb.sqlite")
db.open()


db.setHostName("acidalia");
db.setDatabaseName("customdb");
db.setUserName("mojito");
db.setPassword("J0a1m8");
bool ok = db.open();