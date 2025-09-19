import mysql.connector
import pyodbc



def get_mysql_conn():
    return mysql.connector.connect(
        host="Strider",
        user="admin",
        password="fab",
        database="fabrication",
        autocommit=True,
        use_pure=True,
    )

def get_ms_sql_conn():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=Voltron,1433;"
        "DATABASE=MFC_NTLIVE;"
        "UID=SA;"
        "PWD=MetFab$;"
        "TrustServerCertificate=yes;",
        autocommit=True
    )
