#admin_permissions

from flask import request, jsonify, session
from Backend.DB_backend.db_connection import get_db_connection, close_db_connection
from Backend.DB_backend.login_logout import admin_write_required


def get_department_permissions():
    """
    Fetch all department permissions from database
    """
    try:
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        
        query = """
            SELECT DepartmentDashboardID, DepartmentID, DepartmentName, DashboardID, 
                   DashboardName, GrantedAt, GrantedBy
            FROM DepartmentDashboards
            ORDER BY DepartmentDashboardID DESC
        """
        
        cursor.execute(query)
        permissions = cursor.fetchall()
        close_db_connection(conn)
        
        permissions_list = []
        for perm in permissions:
            permissions_list.append({
                'DepartmentDashboardID': perm[0],
                'DepartmentID': perm[1],
                'DepartmentName': perm[2],
                'DashboardID': perm[3],
                'DashboardName': perm[4],
                'GrantedAt': perm[5],
                'GrantedBy': perm[6]
            })
        
        return permissions_list
    except Exception as e:
        print(f"Error fetching department permissions: {e}")
        return []


def register_admin_permissions_routes(app):
    """Register admin permissions routes"""
    
    @app.route('/admin/grant-dashboard-permission', methods=['POST'])
    @admin_write_required
    def grant_dashboard_permission():
        """
        Grant dashboard permission to department - Admin only
        """
        try:
            data = request.get_json()
            
            department_id = data.get('department_id')
            dashboard_id = data.get('dashboard_id')
            
            if not department_id or not dashboard_id:
                return jsonify({'success': False, 'error': 'Department and Dashboard are required'}), 400
            
            conn = get_db_connection()
            if not conn:
                return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor()
            
            check_query = "SELECT COUNT(*) FROM DepartmentDashboards WHERE DepartmentID = ? AND DashboardID = ?"
            cursor.execute(check_query, (department_id, dashboard_id))
            exists = cursor.fetchone()[0]
            
            if exists > 0:
                close_db_connection(conn)
                return jsonify({'success': False, 'error': 'Permission already exists'}), 400
            
            dept_query = "SELECT DepartmentName FROM Departments WHERE DepartmentID = ?"
            cursor.execute(dept_query, (department_id,))
            dept_result = cursor.fetchone()
            department_name = dept_result[0] if dept_result else 'Unknown'
            
            dash_query = "SELECT DashboardName FROM Dashboards WHERE DashboardID = ?"
            cursor.execute(dash_query, (dashboard_id,))
            dash_result = cursor.fetchone()
            dashboard_name = dash_result[0] if dash_result else 'Unknown'
            
            insert_query = """
                INSERT INTO DepartmentDashboards 
                (DepartmentID, DepartmentName, DashboardID, DashboardName, GrantedAt, GrantedBy)
                VALUES (?, ?, ?, ?, GETDATE(), ?)
            """
            
            cursor.execute(insert_query, (
                department_id,
                department_name,
                dashboard_id,
                dashboard_name,
                session.get('username')
            ))
            
            conn.commit()
            close_db_connection(conn)
            
            return jsonify({'success': True, 'message': 'Permission granted successfully'}), 200
        
        except Exception as e:
            print(f"Error granting dashboard permission: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/admin/revoke-dashboard-permission/<int:permission_id>', methods=['POST'])
    @admin_write_required
    def revoke_dashboard_permission(permission_id):
        """
        Revoke dashboard permission from department - Admin only
        """
        try:
            conn = get_db_connection()
            if not conn:
                return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor()
            
            query = "DELETE FROM DepartmentDashboards WHERE DepartmentDashboardID = ?"
            cursor.execute(query, (permission_id,))
            
            conn.commit()
            close_db_connection(conn)
            
            return jsonify({'success': True, 'message': 'Permission revoked successfully'}), 200
        
        except Exception as e:
            print(f"Error revoking dashboard permission: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
        
if __name__=="__main__":
    print(get_department_permissions())