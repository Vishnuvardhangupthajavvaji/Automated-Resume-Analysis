# Use PyMySQL as Django's MySQL DB-API driver. This must run before Django
# initializes the MySQL backend.
import pymysql

pymysql.install_as_MySQLdb()
