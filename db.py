import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def createDBConn():
   try:
     servername = os.environ.get("db_server");
     usernameSQL = os.environ.get("db_user");
     passwordSQL = os.environ.get("db_pass");
     databaseName = os.environ.get("db_name");
     mydb = mysql.connector.connect(
       host = servername,
       user = usernameSQL,
       passwd = passwordSQL,
       database = databaseName
       )
     return mydb
   except:
     print("DB Connection Failed")
     raise
   