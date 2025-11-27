#admin_configuration

from flask import request, jsonify, session
from login_logout import admin_required
from embed_token_url import get_embed_token


def register_admin_configuration_routes(app):
    """Register admin configuration testing routes"""
    
    @app.route('/admin/configuration-token', methods=['POST'])
    @admin_required
    def configuration_token():
        """
        Generate Power BI embed token with workspace and report names from configuration tab
        """
        try:
            data = request.get_json()
            
            client_id = data.get('client_id', '') or ''
            if isinstance(client_id, str):
                client_id = client_id.strip()
            
            tenant_id = data.get('tenant_id', '') or ''
            if isinstance(tenant_id, str):
                tenant_id = tenant_id.strip()
            
            client_secret = data.get('client_secret', '') or ''
            if isinstance(client_secret, str):
                client_secret = client_secret.strip()
            
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
            
            config_username = data.get('username', '') or ''
            if isinstance(config_username, str):
                config_username = config_username.strip()
            
            config_role = data.get('role', '') or ''
            if isinstance(config_role, str):
                config_role = config_role.strip()
            
            if not all([client_id, tenant_id, client_secret, report_id, group_id, core_dataset]):
                return jsonify({'success': False, 'error': 'All required fields must be filled'}), 400
            
            username_to_use = config_username if config_username else session.get('email')
            
            roles_to_use = [config_role] if config_role else ['RM']
            
            token, embed_url, workspace_name, report_name, error = get_embed_token(
                client_id=client_id,
                tenant_id=tenant_id,
                client_secret=client_secret,
                report_id=report_id,
                group_id=group_id,
                core_dataset=core_dataset,
                proxy_dataset=proxy_dataset,
                username=username_to_use,
                roles=roles_to_use
            )
            
            if error:
                return jsonify({'success': False, 'error': error}), 400
            
            return jsonify({
                'success': True,
                'token': token,
                'embed_url': embed_url,
                'workspace_name': workspace_name,
                'report_name': report_name,
                'username_used': username_to_use,
                'role_used': roles_to_use[0],
                'message': 'Embed token generated successfully!'
            }), 200
        
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500