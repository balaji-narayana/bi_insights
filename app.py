#app.py

from flask import Flask, render_template, request, session, redirect, url_for, flash
import os
from datetime import timedelta
import secrets
from functools import wraps

# Import all modules
from db_connection import get_db_connection, close_db_connection
from login_logout import register_login_routes, login_required, admin_required, admin_write_required
from user_interface import register_user_routes
from embed_token_url import get_embed_token
from admin_overview import (
    get_users_count, 
    get_departments_count, 
    get_active_dashboards_count, 
    get_all_user_logs
)
from admin_reports import register_admin_reports_routes, get_all_dashboards
from admin_departments import get_all_departments, get_departments_with_dashboards
from admin_permissions import register_admin_permissions_routes, get_department_permissions
from admin_users import register_admin_users_routes, get_all_users
from admin_configuration_test import register_admin_configuration_routes

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available (that's okay in production)
    pass

# Load environment variables


# Initialize Flask App
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Session Configuration
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Register all blueprints and routes
register_login_routes(app)
register_user_routes(app)
register_admin_reports_routes(app)
register_admin_permissions_routes(app)
register_admin_users_routes(app)
register_admin_configuration_routes(app)


@app.route('/')
def index():
    """
    Index route - redirect to login or dashboard based on session
    """
    if 'user_id' in session:
        return redirect(url_for('user_dashboard'))
    return redirect(url_for('login')) # in login_logout.py


@app.route('/admin')
@admin_required
def admin_dashboard():
    """
    Admin and Superuser dashboard
    """
    users = get_all_users()
    departments = get_all_departments()
    dashboards = get_all_dashboards()
    permissions = get_department_permissions()
    departments_with_dashboards = get_departments_with_dashboards()
    user_logs = get_all_user_logs()
    users_count = get_users_count()
    departments_count = get_departments_count()
    active_dashboards_count = get_active_dashboards_count()
    
    context = {
        'username': session.get('username'),
        'role': session.get('role'),
        'users': users,
        'departments': departments,
        'dashboards': dashboards,
        'permissions': permissions,
        'departments_with_dashboards': departments_with_dashboards,
        'user_logs': user_logs,
        'users_count': users_count,
        'departments_count': departments_count,
        'active_dashboards_count': active_dashboards_count
    }
    
    return render_template('admin_dashboard.html', **context)


@app.route('/admin/report-token/<int:dashboard_id>', methods=['POST'])
@admin_required
def admin_report_token(dashboard_id):
    """
    Generate Power BI embed token for a dashboard from database
    """
    from user_interface import get_dashboard_by_id
    
    try:
        dashboard = get_dashboard_by_id(dashboard_id)
        
        if not dashboard:
            return {'success': False, 'error': 'Dashboard not found'}, 404
        
        from db_connection import get_db_connection, close_db_connection
        import os
        from dotenv import load_dotenv
        from flask import jsonify
        
        load_dotenv()
        
        POWERBI_CLIENT_ID = os.getenv('POWERBI_CLIENT_ID')
        POWERBI_CLIENT_SECRET = os.getenv('POWERBI_CLIENT_SECRET')
        POWERBI_TENANT_ID = os.getenv('POWERBI_TENANT_ID')
        
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
        from flask import jsonify
        return jsonify({'success': False, 'error': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('error.html', error_code=404, error_message='Page not found'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('error.html', error_code=500, error_message='Internal server error'), 500


@app.route('/debug/test-db', methods=['GET'])
def test_db():
    """
    Test database connection (remove in production)
    """
    conn = get_db_connection()
    if conn:
        close_db_connection(conn)
        return "Database connection successful!", 200
    return "Database connection failed!", 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port,debug=True)

