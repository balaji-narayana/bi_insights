#login_logout.py

from flask import render_template, request, redirect, url_for, session, flash
import msal
import requests
import os

from functools import wraps
from db_connection import insert_user_log

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available (that's okay in production)
    pass

AZURE_AD_CONFIG = {
    "client_id": os.getenv('SSO_CLIENT_ID'),
    "client_secret": os.getenv('SSO_CLIENT_SECRET'),
    "tenant": os.getenv('SSO_TENANT'),
    "authority": None,
    "redirect_uri": 'http://localhost:5000/auth/callback',
    "scopes": ["User.Read"]
}

AZURE_AD_CONFIG["authority"] = f"https://login.microsoftonline.com/{AZURE_AD_CONFIG['tenant']}"


def get_msal_app():
    """Create MSAL app for Azure AD authentication"""
    return msal.ConfidentialClientApplication(
        AZURE_AD_CONFIG["client_id"],
        authority=AZURE_AD_CONFIG["authority"],
        client_credential=AZURE_AD_CONFIG["client_secret"]
    )


def authenticate_user(email):
    """
    Authenticate user by checking email against database
    """
    from db_connection import get_db_connection, close_db_connection
    
    try:
        conn = get_db_connection()
        if not conn:
            print("Failed to connect to database")
            return None
        
        cursor = conn.cursor()
        
        query = """
            SELECT UserID, UserEmail, UserName, DepartmentID, DepartmentName, Role 
            FROM Users 
            WHERE UserEmail = ?
        """
        
        cursor.execute(query, (email,))
        user = cursor.fetchone()
        close_db_connection(conn)
        
        if user:
            user_dict = {
                'UserID': user[0],
                'UserEmail': user[1],
                'UserName': user[2],
                'DepartmentID': user[3],
                'DepartmentName': user[4],
                'Role': user[5]
            }
            return user_dict
        
        return None
    except Exception as e:
        print(f"Authentication Error: {e}")
        return None


def login_required(f):
    """
    Decorator to check if user is logged in
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Decorator to check if user is admin or superuser
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'warning')
            return redirect(url_for('login'))
        if session.get('role') not in ['admin', 'superuser']:
            flash('You do not have admin access', 'danger')
            return redirect(url_for('user_dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def admin_write_required(f):
    """
    Decorator to check if user is admin (not superuser)
    Used for CRUD operations that superuser cannot perform
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('You do not have permission to perform this action', 'danger')
            return redirect(url_for('admin_dashboard') if session.get('role') == 'superuser' else url_for('user_dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def register_login_routes(app):
    """Register login/logout routes"""
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """
        Login page - Azure AD SSO
        """
        if request.method == 'POST':
            auth_app = get_msal_app()
            auth_url = auth_app.get_authorization_request_url(
                scopes=AZURE_AD_CONFIG["scopes"],
                redirect_uri=AZURE_AD_CONFIG["redirect_uri"]
            )
            return redirect(auth_url)
        
        return render_template('login.html')

    @app.route('/auth/callback')
    def auth_callback():
        """
        Azure AD callback handler
        """
        code = request.args.get('code')
        error = request.args.get('error')
        error_description = request.args.get('error_description')
        
        if error:
            flash(f'Azure AD Error: {error_description}', 'danger')
            return redirect(url_for('login'))
        
        if not code:
            flash('No authorization code received', 'danger')
            return redirect(url_for('login'))
        
        try:
            auth_app = get_msal_app()
            token_response = auth_app.acquire_token_by_authorization_code(
                code,
                scopes=AZURE_AD_CONFIG["scopes"],
                redirect_uri=AZURE_AD_CONFIG["redirect_uri"]
            )
            
            if 'error' in token_response:
                flash(f'Authentication Error: {token_response.get("error_description", "Unknown")}', 'danger')
                return redirect(url_for('login'))
            
            if 'access_token' not in token_response:
                flash('No access token received', 'danger')
                return redirect(url_for('login'))
            
            headers = {
                'Authorization': f"Bearer {token_response['access_token']}",
                'Content-Type': 'application/json'
            }
            
            user_response = requests.get(
                'https://graph.microsoft.com/v1.0/me?$select=id,displayName,mail,userPrincipalName',
                headers=headers,
                timeout=5
            )
            
            if user_response.status_code != 200:
                flash('Failed to fetch user information', 'danger')
                return redirect(url_for('login'))
            
            user_data = user_response.json()
            user_email = user_data.get('mail') or user_data.get('userPrincipalName', '')
            
            user = authenticate_user(user_email)
            
            if user:
                session['user_id'] = user['UserID']
                session['email'] = user['UserEmail']
                session['username'] = user['UserName']
                session['role'] = user['Role']
                session['department_id'] = user['DepartmentID']
                session['department_name'] = user['DepartmentName']
                session.permanent = True
                
                insert_user_log(user['UserID'], user['UserName'], user['UserEmail'], 'Login')
                
                flash(f'Welcome {user["UserName"]}!', 'success')
                
                return redirect(url_for('user_dashboard'))
            else:
                flash(f'Email {user_email} is not registered in the system.', 'danger')
                return redirect(url_for('login'))
        
        except requests.exceptions.Timeout:
            flash('Request timeout - please try again', 'danger')
            return redirect(url_for('login'))
        except Exception as e:
            print(f"Auth Error: {e}")
            flash('Authentication failed', 'danger')
            return redirect(url_for('login'))

    @app.route('/logout')
    def logout():
        """
        Logout route - clear session
        """
        if 'user_id' in session and 'username' in session and 'email' in session:
            insert_user_log(session['user_id'], session['username'], session['email'], 'Logout')
        
        session.clear()
        flash('You have been logged out', 'info')
        return redirect(url_for('login'))
    
