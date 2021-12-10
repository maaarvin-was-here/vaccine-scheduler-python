import pymssql
import os


class ConnectionManager:

    def __init__(self):
        #self.server_name = os.getenv("Server")
        #self.db_name = os.getenv("DBName")
        #self.user = os.getenv("UserID")
        #self.password = os.getenv("Password")
        self.server_name = "mlin586.database.windows.net"
        self.db_name = "Homework 3"
        self.user = "mlin586@mlin586"
        self.password = "Flygonrules123"
        self.conn = None

    def create_connection(self):
        try:
            self.conn = pymssql.connect(server=self.server_name, user=self.user, password=self.password, database=self.db_name)
        except pymssql.Error as db_err:
            print("Database Programming Error in SQL connection processing! ")
            sqlrc = str(db_err.args[0])
            print("Exception code: " + str(sqlrc))
        return self.conn

    def close_connection(self):
        try:
            self.conn.close()
        except pymssql.Error as db_err:
            print("Database Programming Error in SQL connection processing! ")
            sqlrc = str(db_err.args[0])
            print("Exception code: " + str(sqlrc))
