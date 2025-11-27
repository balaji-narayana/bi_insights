#user_interface.py


from flask import render_template, request, redirect, url_for, session, jsonify
from db_connection import get_db_connection, close_db_connection
from login_logout import login_required
from embed_token_url import get_embed_token
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available (that's okay in production)
    pass

POWERBI_CLIENT_ID = os.getenv('POWERBI_CLIENT_ID')
POWERBI_CLIENT_SECRET = os.getenv('POWERBI_CLIENT_SECRET')
POWERBI_TENANT_ID = os.getenv('POWERBI_TENANT_ID')


def get_user_department_info(user_id):
    """
    Get department information for a specific user
    """
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        
        query = """
            SELECT d.DepartmentID, d.DepartmentName, d.CreatedAt
            FROM Departments d
            INNER JOIN Users u ON d.DepartmentID = u.DepartmentID
            WHERE u.UserID = ?
        """
        
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        close_db_connection(conn)
        
        if result:
            return {
                'DepartmentID': result[0],
                'DepartmentName': result[1],
                'CreatedAt': result[2]
            }
        
        return None
    except Exception as e:
        print(f"Error fetching user department: {e}")
        return None


def get_users_by_department(department_name='Data'):
    """
    Get all users from a specific department
    """
    try:
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        
        query = """
            SELECT UserID, UserName, UserEmail
            FROM Users
            WHERE DepartmentName = ?
            ORDER BY UserName
        """
        
        cursor.execute(query, (department_name,))
        users = cursor.fetchall()
        close_db_connection(conn)
        
        user_list = []
        for user in users:
            user_list.append({
                'UserID': user[0],
                'UserName': user[1],
                'UserEmail': user[2]
            })
        
        return user_list
    except Exception as e:
        print(f"Error fetching users by department: {e}")
        return []


def get_user_accessible_dashboards(user_id):
    """
    Get dashboards accessible to a user based on their role and department
    """
    try:
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        
        role_query = "SELECT Role, DepartmentID FROM Users WHERE UserID = ?"
        cursor.execute(role_query, (user_id,))
        user_info = cursor.fetchone()
        
        if not user_info:
            close_db_connection(conn)
            return []
        
        user_role = user_info[0]
        user_department_id = user_info[1]
        
        if user_role in ['admin', 'superuser']:
            query = """
                SELECT DashboardID, DashboardName, ReportID, GroupID, CoreDatasetID, 
                       ProxyDatasetID, CreatedAt, CreatedBy, UpdatedAt, UpdatedBy, Status, Description, DashboardOwner, Alert
                FROM Dashboards
                ORDER BY DashboardID DESC
            """
            cursor.execute(query)
        else:
            query = """
                SELECT DISTINCT d.DashboardID, d.DashboardName, d.ReportID, d.GroupID, d.CoreDatasetID, 
                       d.ProxyDatasetID, d.CreatedAt, d.CreatedBy, d.UpdatedAt, d.UpdatedBy, d.Status, d.Description, d.DashboardOwner, d.Alert
                FROM Dashboards d
                INNER JOIN DepartmentDashboards dd ON d.DashboardID = dd.DashboardID
                WHERE dd.DepartmentID = ?
                ORDER BY d.DashboardID DESC
            """
            cursor.execute(query, (user_department_id,))
        
        dashboards = cursor.fetchall()
        close_db_connection(conn)
        
        dashboard_list = []
        for dashboard in dashboards:
            dashboard_list.append({
                'DashboardID': dashboard[0],
                'DashboardName': dashboard[1],
                'ReportID': dashboard[2],
                'GroupID': dashboard[3],
                'CoreDatasetID': dashboard[4],
                'ProxyDatasetID': dashboard[5],
                'CreatedAt': dashboard[6],
                'CreatedBy': dashboard[7],
                'UpdatedAt': dashboard[8],
                'UpdatedBy': dashboard[9],
                'Status': dashboard[10],
                'Description': dashboard[11],
                'DashboardOwner': dashboard[12],
                'Alert': dashboard[13]
            })
        
        return dashboard_list
    except Exception as e:
        print(f"Error fetching user accessible dashboards: {e}")
        return []


def get_dashboard_by_id(dashboard_id):
    """
    Fetch dashboard details from database by ID
    """
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        
        query = """
            SELECT DashboardID, DashboardName, ReportID, GroupID, CoreDatasetID, 
                   ProxyDatasetID, CreatedAt, CreatedBy, UpdatedAt, UpdatedBy, Status, Description, DashboardOwner, Alert
            FROM Dashboards
            WHERE DashboardID = ?
        """
        
        cursor.execute(query, (dashboard_id,))
        dashboard = cursor.fetchone()
        close_db_connection(conn)
        
        if dashboard:
            return {
                'DashboardID': dashboard[0],
                'DashboardName': dashboard[1],
                'ReportID': dashboard[2],
                'GroupID': dashboard[3],
                'CoreDatasetID': dashboard[4],
                'ProxyDatasetID': dashboard[5],
                'CreatedAt': dashboard[6],
                'CreatedBy': dashboard[7],
                'UpdatedAt': dashboard[8],
                'UpdatedBy': dashboard[9],
                'Status': dashboard[10],
                'Description': dashboard[11],
                'DashboardOwner': dashboard[12],
                'Alert': dashboard[13]
            }
        
        return None
    except Exception as e:
        print(f"Error fetching dashboard: {e}")
        return None


def register_user_routes(app):
    """Register user interface routes"""
    
    @app.route('/dashboard')
    @login_required
    def user_dashboard():
        """
        User dashboard
        """
        user_role = session.get('role')
        username = session.get('username')
        department_name = session.get('department_name')
        user_id = session.get('user_id')
        
        department_info = get_user_department_info(user_id)
        accessible_dashboards = get_user_accessible_dashboards(user_id)
        
        context = {
            'username': username,
            'department_name': department_name,
            'department_info': department_info,
            'role': user_role,
            'dashboards': accessible_dashboards
        }
        
        return render_template('user_dashboard.html', **context)

    @app.route('/user/report-token/<int:dashboard_id>', methods=['POST'])
    @login_required
    def user_report_token(dashboard_id):
        """
        Generate Power BI embed token for a dashboard from database (User accessible)
        """
        try:
            user_id = session.get('user_id')
            
            dashboard = get_dashboard_by_id(dashboard_id)
            
            if not dashboard:
                return jsonify({'success': False, 'error': 'Dashboard not found'}), 404
            
            user_role = session.get('role')
            if user_role not in ['admin', 'superuser'] and dashboard['Status'] != 'Active':
                return jsonify({'success': False, 'error': 'This dashboard is currently under development'}), 400
            
            if user_role not in ['admin', 'superuser']:
                user_department_id = session.get('department_id')
                conn = get_db_connection()
                if not conn:
                    return jsonify({'success': False, 'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor()
                check_query = """
                    SELECT COUNT(*) FROM DepartmentDashboards 
                    WHERE DepartmentID = ? AND DashboardID = ?
                """
                cursor.execute(check_query, (user_department_id, dashboard_id))
                access_count = cursor.fetchone()[0]
                close_db_connection(conn)
                
                if access_count == 0:
                    return jsonify({'success': False, 'error': 'You do not have access to this dashboard'}), 403
            
            client_id = POWERBI_CLIENT_ID
            tenant_id = POWERBI_TENANT_ID
            client_secret = POWERBI_CLIENT_SECRET
            
            report_id = dashboard['ReportID']
            group_id = dashboard['GroupID']
            core_dataset = dashboard['CoreDatasetID']
            proxy_dataset = dashboard['ProxyDatasetID'] or ''
            
            if not all([client_id, tenant_id, client_secret, report_id, group_id, core_dataset]):
                return jsonify({'success': False, 'error': 'Invalid dashboard configuration'}), 400
            
            token, embed_url, workspace_name, report_name, error = get_embed_token(
                client_id=client_id,
                tenant_id=tenant_id,
                client_secret=client_secret,
                report_id=report_id,
                group_id=group_id,
                core_dataset=core_dataset,
                proxy_dataset=proxy_dataset,
                username=session.get('email'),
                roles=['RM']
            )
            
            if error:
                return jsonify({'success': False, 'error': error}), 400
            
            return jsonify({
                'success': True,
                'token': token,
                'embed_url': embed_url,
                'report_id': report_id,
                'workspace_name': workspace_name,
                'report_name': report_name,
                'dashboard_name': dashboard['DashboardName'],
                'message': 'Report token generated successfully!'
            }), 200
        
        except Exception as e:
            print(f"Error generating report token: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/view-report')
    @login_required
    def view_report():
        """
        View embedded Power BI report
        """
        token = request.args.get('token')
        embed_url = request.args.get('embedUrl')
        report_id = request.args.get('reportId')
        report_name = request.args.get('reportName', 'Power BI Report')
        username = session.get('username', 'User')
        
        return render_template('powerbi_report.html', report_name=report_name, username=username)
    

if __name__=="__main__":
    print(get_user_department_info(4))
    print(get_users_by_department())