import mysql.connector
import os
SQL_SERVER = os.getenv('SQL_SERVER')
SQL_PASSWORD = os.getenv('SQL_PASSWORD')
SQL_USERNAME = os.getenv('SQL_USERNAME')
SQL_DATABASE = os.getenv('SQL_DATABASE')

# Make sure you have a "library" database created!

class dbMysql():
    def __init__(self):
        self.password = SQL_PASSWORD
        self.username = SQL_USERNAME
        self.host = SQL_SERVER
        self.database = SQL_DATABASE
        self.mydb = None

    def connection(self):
        self.mydb = mysql.connector.connect(
            host=self.host,
            user=self.username,
            passwd=self.password,
            database=self.database
        )
        return(self.mydb)

    def configure_db(self, mycursor):
        mycursor.execute(f"CREATE DATABASE IF NOT EXISTS {SQL_DATABASE}")
        self.mydb.commit()

        mycursor.execute(
            "CREATE TABLE IF NOT EXISTS admin (id INT NOT NULL AUTO_INCREMENT,"
            "name VARCHAR(255) NOT NULL,"
            "password VARCHAR(256) NOT NULL,"
            "email VARCHAR(255) NOT NULL,"
            "PRIMARY KEY (id))")
        self.mydb.commit()