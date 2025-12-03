#admin_departments
from Backend.DB_backend.db_connection import get_db_connection, close_db_connection


def get_all_departments():
    """
    Fetch all departments from database
    """
    try:
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        
        query = """
            SELECT DepartmentID, DepartmentName, CreatedAt
            FROM Departments
            ORDER BY DepartmentID DESC
        """
        
        cursor.execute(query)
        departments = cursor.fetchall()
        close_db_connection(conn)
        
        dept_list = []
        for dept in departments:
            dept_list.append({
                'DepartmentID': dept[0],
                'DepartmentName': dept[1],
                'CreatedAt': dept[2]
            })
        
        return dept_list
    except Exception as e:
        print(f"Error fetching all departments: {e}")
        return []


def get_departments_with_dashboards():
    """
    Fetch all departments with their accessible dashboards
    Returns a structured dictionary with departments and their dashboards
    """
    try:
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        
        dept_query = """
            SELECT DepartmentID, DepartmentName, CreatedAt
            FROM Departments
            ORDER BY DepartmentName
        """
        
        cursor.execute(dept_query)
        departments = cursor.fetchall()
        
        dept_dashboard_map = []
        
        for dept in departments:
            dept_id = dept[0]
            dept_name = dept[1]
            dept_created = dept[2]
            
            dashboard_query = """
                SELECT DISTINCT d.DashboardID, d.DashboardName, d.Status, d.Description, 
                       d.CreatedBy, d.CreatedAt, dd.GrantedAt, dd.GrantedBy, d.DashboardOwner
                FROM Dashboards d
                INNER JOIN DepartmentDashboards dd ON d.DashboardID = dd.DashboardID
                WHERE dd.DepartmentID = ?
                ORDER BY d.DashboardName
            """
            
            cursor.execute(dashboard_query, (dept_id,))
            dashboards = cursor.fetchall()
            
            dashboard_list = []
            for dash in dashboards:
                dashboard_list.append({
                    'DashboardID': dash[0],
                    'DashboardName': dash[1],
                    'Status': dash[2],
                    'Description': dash[3],
                    'CreatedBy': dash[4],
                    'CreatedAt': dash[5],
                    'GrantedAt': dash[6],
                    'GrantedBy': dash[7],
                    'DashboardOwner': dash[8]
                })
            
            dept_dashboard_map.append({
                'DepartmentID': dept_id,
                'DepartmentName': dept_name,
                'CreatedAt': dept_created,
                'DashboardCount': len(dashboard_list),
                'Dashboards': dashboard_list
            })
        
        close_db_connection(conn)
        return dept_dashboard_map
        
    except Exception as e:
        print(f"Error fetching departments with dashboards: {e}")
        return []
    
if __name__=="__main__":
    print(get_all_departments())
    print(get_departments_with_dashboards())