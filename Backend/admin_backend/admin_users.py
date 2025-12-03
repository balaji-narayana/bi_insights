#admin_users

from flask import request, jsonify, session
from Backend.DB_backend.db_connection import get_db_connection, close_db_connection
from Backend.DB_backend.login_logout import admin_required, admin_write_required


def get_all_users():
    """
    Fetch all users from database
    """
    try:
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        
        query = """
            SELECT UserID, UserEmail, UserName, DepartmentID, DepartmentName, Role, CreatedAt
            FROM Users
            ORDER BY UserID DESC
        """
        
        cursor.execute(query)
        users = cursor.fetchall()
        close_db_connection(conn)
        
        user_list = []
        for user in users:
            user_list.append({
                'UserID': user[0],
                'UserEmail': user[1],
                'UserName': user[2],
                'DepartmentID': user[3],
                'DepartmentName': user[4],
                'Role': user[5],
                'CreatedAt': user[6]
            })
        
        return user_list
    except Exception as e:
        print(f"Error fetching all users: {e}")
        return []


def register_admin_users_routes(app):
    """Register admin users routes"""
    
    @app.route('/api/department-users')
    @admin_required
    def api_department_users():
        """
        API endpoint to get users by department (default: Data)
        """
        try:
            from Backend.user_backend.user_interface import get_users_by_department
            department = request.args.get('department', 'Data')
            users = get_users_by_department(department)
            return jsonify({'success': True, 'users': users}), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/admin/update-user-role', methods=['POST'])
    @admin_write_required
    def update_user_role():
        """
        Update user role (admin/superuser/user) - Admin only
        """
        try:
            data = request.get_json()
            
            user_id = data.get('user_id')
            new_role = data.get('new_role', '').strip().lower()
            current_user_id = session.get('user_id')
            
            if not user_id:
                return jsonify({'success': False, 'error': 'User ID is required'}), 400
            
            if new_role not in ['admin', 'superuser', 'user']:
                return jsonify({'success': False, 'error': f'Invalid role: {new_role}'}), 400
            
            conn = get_db_connection()
            if not conn:
                return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor()
            
            verify_query = "SELECT UserID, Role FROM Users WHERE UserID = ?"
            cursor.execute(verify_query, (user_id,))
            user = cursor.fetchone()
            
            if not user:
                close_db_connection(conn)
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
            old_role = user[1]
            
            is_self_update = int(user_id) == current_user_id
            
            query = "UPDATE Users SET Role = ? WHERE UserID = ?"
            cursor.execute(query, (new_role, user_id))
            
            conn.commit()
            
            cursor.execute(verify_query, (user_id,))
            updated_user = cursor.fetchone()
            updated_role = updated_user[1] if updated_user else None
            
            close_db_connection(conn)
            
            if updated_role != new_role:
                print(f"WARNING: Role update failed for user {user_id}. Expected {new_role}, got {updated_role}")
                return jsonify({'success': False, 'error': 'Role update failed - please try again'}), 500
            
            print(f"SUCCESS: User {user_id} role changed from {old_role} to {new_role}")
            
            if is_self_update:
                return jsonify({
                    'success': True, 
                    'message': f'Your role has been updated successfully from {old_role.upper()} to {new_role.upper()}. Redirecting...',
                    'is_self_update': True,
                    'new_role': new_role,
                    'old_role': old_role
                }), 200
            else:
                return jsonify({
                    'success': True, 
                    'message': f'User role updated successfully from {old_role.upper()} to {new_role.upper()}',
                    'is_self_update': False
                }), 200
        
        except Exception as e:
            print(f"Error updating user role: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': f'Error: {str(e)}'}), 500