#admin_reports

from flask import request, jsonify, session
from db_connection import get_db_connection, close_db_connection
from login_logout import admin_write_required


def get_all_dashboards():
    """
    Fetch all dashboards from database
    """
    try:
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        
        query = """
            SELECT DashboardID, DashboardName, ReportID, GroupID, CoreDatasetID, 
                   ProxyDatasetID, CreatedAt, CreatedBy, UpdatedAt, UpdatedBy, Status, Description, DashboardOwner, Alert
            FROM Dashboards
            ORDER BY DashboardID DESC
        """
        
        cursor.execute(query)
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
        print(f"Error fetching all dashboards: {e}")
        return []


def register_admin_reports_routes(app):
    """Register admin reports routes"""
    
    @app.route('/admin/add-dashboard', methods=['POST'])
    @admin_write_required
    def add_dashboard():
        """
        Add new dashboard to database - Admin only
        """
        try:
            data = request.get_json()
            
            dashboard_name = data.get('dashboard_name', '') or ''
            if isinstance(dashboard_name, str):
                dashboard_name = dashboard_name.strip()
            
            report_id = data.get('report_id', '') or ''
            if isinstance(report_id, str):
                report_id = report_id.strip()
            
            group_id = data.get('group_id', '') or ''
            if isinstance(group_id, str):
                group_id = group_id.strip()
            
            core_dataset = data.get('core_dataset', '') or ''
            if isinstance(core_dataset, str):
                core_dataset = core_dataset.strip()
            
            proxy_dataset = data.get('proxy_dataset', '') or ''
            if proxy_dataset and isinstance(proxy_dataset, str):
                proxy_dataset = proxy_dataset.strip()
            else:
                proxy_dataset = ''
            
            description = data.get('description', '') or ''
            if isinstance(description, str):
                description = description.strip()
            
            dashboard_owner = data.get('dashboard_owner', '') or ''
            if isinstance(dashboard_owner, str):
                dashboard_owner = dashboard_owner.strip()
            
            status = data.get('status', 'Active') or 'Active'
            if isinstance(status, str):
                status = status.strip()
            
            alert = data.get('alert', '') or ''
            if isinstance(alert, str):
                alert = alert.strip()
            
            if status == 'Inactive' and not alert:
                return jsonify({'success': False, 'error': 'Alert message is required for Inactive dashboards'}), 400
            
            if status == 'Active':
                alert = ''
            
            created_by = session.get('username')
            
            if not all([dashboard_name, report_id, group_id, core_dataset]):
                return jsonify({'success': False, 'error': 'All required fields must be filled'}), 400
            
            conn = get_db_connection()
            if not conn:
                return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor()
            
            query = """
                INSERT INTO Dashboards 
                (DashboardName, ReportID, GroupID, CoreDatasetID, ProxyDatasetID, Description, CreatedBy, Status, DashboardOwner, Alert, CreatedAt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """
            
            cursor.execute(query, (
                dashboard_name,
                report_id,
                group_id,
                core_dataset,
                proxy_dataset if proxy_dataset else None,
                description if description else None,
                created_by,
                status,
                dashboard_owner if dashboard_owner else None,
                alert if alert else None
            ))
            
            conn.commit()
            close_db_connection(conn)
            
            return jsonify({'success': True, 'message': 'Dashboard added successfully'}), 200
        
        except Exception as e:
            print(f"Error adding dashboard: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/admin/update-dashboard/<int:dashboard_id>', methods=['POST'])
    @admin_write_required
    def update_dashboard(dashboard_id):
        """
        Update existing dashboard - Admin only
        """
        try:
            data = request.get_json()
            
            dashboard_name = data.get('dashboard_name', '').strip()
            report_id = data.get('report_id', '').strip()
            group_id = data.get('group_id', '').strip()
            core_dataset = data.get('core_dataset', '').strip()
            proxy_dataset = data.get('proxy_dataset', '').strip()
            description = data.get('description', '').strip()
            status = data.get('status', '').strip()
            dashboard_owner = data.get('dashboard_owner', '').strip()
            alert = data.get('alert', '').strip()
            updated_by = session.get('username')
            
            if status == 'Inactive' and not alert:
                return jsonify({'success': False, 'error': 'Alert message is required for Inactive dashboards'}), 400
            
            if status == 'Active':
                alert = ''
            
            if not all([dashboard_name, report_id, group_id, core_dataset, status]):
                return jsonify({'success': False, 'error': 'All required fields must be filled'}), 400
            
            conn = get_db_connection()
            if not conn:
                return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor()
            
            query = """
                UPDATE Dashboards 
                SET DashboardName = ?, ReportID = ?, GroupID = ?, CoreDatasetID = ?, 
                    ProxyDatasetID = ?, Description = ?, Status = ?, DashboardOwner = ?, Alert = ?, UpdatedBy = ?, UpdatedAt = GETDATE()
                WHERE DashboardID = ?
            """
            
            cursor.execute(query, (
                dashboard_name,
                report_id,
                group_id,
                core_dataset,
                proxy_dataset if proxy_dataset else None,
                description if description else None,
                status,
                dashboard_owner if dashboard_owner else None,
                alert if alert else None,
                updated_by,
                dashboard_id
            ))
            
            conn.commit()
            close_db_connection(conn)
            
            return jsonify({'success': True, 'message': 'Dashboard updated successfully'}), 200
        
        except Exception as e:
            print(f"Error updating dashboard: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/admin/delete-dashboard/<int:dashboard_id>', methods=['POST'])
    @admin_write_required
    def delete_dashboard(dashboard_id):
        """
        Delete dashboard from database - Admin only
        """
        try:
            conn = get_db_connection()
            if not conn:
                return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor()
            
            query = "DELETE FROM Dashboards WHERE DashboardID = ?"
            cursor.execute(query, (dashboard_id,))
            
            conn.commit()
            close_db_connection(conn)
            
            return jsonify({'success': True, 'message': 'Dashboard deleted successfully'}), 200
        
        except Exception as e:
            print(f"Error deleting dashboard: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500