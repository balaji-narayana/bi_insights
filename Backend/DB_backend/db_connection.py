#db_connection.py

import pyodbc
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available (that's okay in production)
    pass
DB_SERVER = os.getenv('DB_SERVER')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

CONNECTION_STRING = f'Driver={{ODBC Driver 18 for SQL Server}};Server=tcp:{DB_SERVER},1433;Database={DB_NAME};Uid={DB_USER};Pwd={DB_PASSWORD};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'

def get_db_connection():
    """
    Establish connection to Azure SQL Database
    Returns: Connection object or None if connection fails
    """
    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        return conn
    except pyodbc.Error as e:
        print(f"Database Connection Error: {e}")
        return None


def close_db_connection(conn):
    """
    Close database connection safely
    """
    try:
        if conn:
            conn.close()
    except pyodbc.Error as e:
        print(f"Error closing connection: {e}")


def insert_user_log(user_id, username, email, action):
    """
    Insert user activity log into UserLogs table
    Args: user_id, username, email, action ('Login' or 'Logout')
    """
    try:
        conn = get_db_connection()
        if not conn:
            print(f"Failed to connect to database for logging")
            return False
        
        cursor = conn.cursor()
        
        query = """
            INSERT INTO UserLogs (UserID, UserName, UserEmail, Action, LogTime)
            VALUES (?, ?, ?, ?, GETDATE())
        """
        
        cursor.execute(query, (user_id, username, email, action))
        conn.commit()
        close_db_connection(conn)
        
        print(f"User log inserted: {username} - {action}")
        return True
    except Exception as e:
        print(f"Error inserting user log: {e}")
        return False
    
print(get_db_connection())