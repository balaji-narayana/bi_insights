#admin_overview
from flask import render_template, session
from db_connection import get_db_connection, close_db_connection
from login_logout import admin_required


def get_users_count():
    """
    Get total count of users
    """
    try:
        conn = get_db_connection()
        if not conn:
            return 0
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Users")
        count = cursor.fetchone()[0]
        close_db_connection(conn)
        
        return count
    except Exception as e:
        print(f"Error getting users count: {e}")
        return 0


def get_departments_count():
    """
    Get total count of departments
    """
    try:
        conn = get_db_connection()
        if not conn:
            return 0
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Departments")
        count = cursor.fetchone()[0]
        close_db_connection(conn)
        
        return count
    except Exception as e:
        print(f"Error getting departments count: {e}")
        return 0


def get_active_dashboards_count():
    """
    Get count of active dashboards
    """
    try:
        conn = get_db_connection()
        if not conn:
            return 0
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT DashboardID) FROM Dashboards WHERE Status = 'Active'")
        count = cursor.fetchone()[0]
        close_db_connection(conn)
        
        return count
    except Exception as e:
        print(f"Error getting active dashboards count: {e}")
        return 0


def get_all_user_logs():
    """
    Fetch all user logs from database - ordered by most recent first
    """
    try:
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        
        query = """
            SELECT LogID, UserID, UserName, UserEmail, Action, LogTime
            FROM UserLogs
            ORDER BY LogTime DESC
        """
        
        cursor.execute(query)
        logs = cursor.fetchall()
        close_db_connection(conn)
        
        logs_list = []
        for log in logs:
            logs_list.append({
                'LogID': log[0],
                'UserID': log[1],
                'UserName': log[2],
                'UserEmail': log[3],
                'Action': log[4],
                'LogTime': log[5]
            })
        
        return logs_list
    except Exception as e:
        print(f"Error fetching user logs: {e}")
        return []
    

if __name__=="__main__":
    print(get_users_count())
    print(get_departments_count())
    print(get_active_dashboards_count())
    print(get_all_user_logs())