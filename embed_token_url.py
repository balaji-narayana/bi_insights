#embed_token_url.py

import msal
import requests
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


def get_embed_token(client_id, tenant_id, client_secret, report_id, group_id, core_dataset, proxy_dataset="", username="user@example.com", roles=None):
    """
    Generate Power BI embed token with workspace name and report name
    Returns: (embed_token, embed_url, workspace_name, report_name, error_message)
    """
    try:
        authority = f'https://login.microsoftonline.com/{tenant_id}'
        scope = ['https://analysis.windows.net/powerbi/api/.default']
        
        app_msal = msal.ConfidentialClientApplication(
            client_id,
            authority=authority,
            client_credential=client_secret
        )
        
        result = app_msal.acquire_token_for_client(scopes=scope)
        
        if 'access_token' not in result:
            error_msg = result.get('error_description', 'Unknown error')
            return None, None, None, None, f"Error acquiring access token: {error_msg}"
        
        access_token = result['access_token']
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        powerbi_api = 'https://api.powerbi.com/v1.0/myorg'
        
        workspace_name = 'Unknown Workspace'
        try:
            group_url = f"{powerbi_api}/groups/{group_id}"
            group_resp = requests.get(group_url, headers=headers, timeout=5)
            if group_resp.status_code == 200:
                workspace_name = group_resp.json().get('name', 'Unknown Workspace')
        except Exception as e:
            print(f"Error fetching workspace name: {e}")
            workspace_name = 'Unknown Workspace'
        
        report_url = f"{powerbi_api}/groups/{group_id}/reports/{report_id}"
        report_resp = requests.get(report_url, headers=headers, timeout=5)
        
        if report_resp.status_code != 200:
            return None, None, None, None, f"Report not found: {report_resp.status_code}"
        
        report_name = report_resp.json().get('name', 'Unknown Report')
        
        datasets_list = [{"id": core_dataset, "xmlaPermissions": "ReadOnly"}]
        if proxy_dataset and proxy_dataset.strip():
            datasets_list.append({"id": proxy_dataset, "xmlaPermissions": "ReadOnly"})
        
        identity_datasets = [core_dataset]
        
        payload = {
            "datasets": datasets_list,
            "reports": [{"id": report_id}],
            "targetWorkspaces": [{"id": group_id}],
            "accessLevel": "View",
            "identities": [
                {
                    "username": username,
                    "roles": roles if roles else ["RM"],
                    "datasets": identity_datasets
                }
            ]
        }
        
        token_url = f"{powerbi_api}/GenerateToken"
        token_resp = requests.post(token_url, headers=headers, json=payload, timeout=5)
        
        if token_resp.status_code != 200:
            error_text = token_resp.text
            return None, None, None, None, f"Token generation failed: {error_text}"
        
        embed_token = token_resp.json().get('token')
        embed_url = report_resp.json().get('embedUrl')

        return embed_token, embed_url, workspace_name, report_name, None
    
    except Exception as e:
        return None, None, None, None, f"Error: {str(e)}"