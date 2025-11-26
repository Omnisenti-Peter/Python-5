#!/usr/bin/env python3
"""
Opinian SaaS Blogging Platform - Main Application
Flask backend with PostgreSQL database
"""

import os
import sys
from datetime import datetime, timedelta
from functools import wraps
import json
import bcrypt
import jwt
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', '10485760'))

# Configure CORS
CORS(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database connection helper
def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'opinian'),
            port=os.getenv('DB_PORT', '5432')
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

# Authentication decorators
def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login'))
            
            user_role = session.get('user_role')
            if user_role not in allowed_roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Utility functions
def allowed_file(filename):
    """Check if file extension is allowed"""
    allowed_extensions = set(os.getenv('ALLOWED_EXTENSIONS', 'png,jpg,jpeg,gif,webp').split(','))
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def log_user_activity(user_id, action, resource_type=None, resource_id=None, metadata=None):
    """Log user activity for audit purposes"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_activity_logs 
                (user_id, action, resource_type, resource_id, ip_address, user_agent, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
            """, (
                user_id, action, resource_type, resource_id,
                request.remote_addr, request.headers.get('User-Agent'),
                json.dumps(metadata) if metadata else None
            ))
            conn.commit()
            cursor.close()
            conn.close()
    except Exception as e:
        logger.error(f"Error logging user activity: {e}")

# Routes will be defined in separate modules
# For now, let's create the basic structure

@app.route('/')
def index():
    """Home page - display public content"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get published blog posts from all active groups
            cursor.execute("""
                SELECT bp.*, u.username, u.first_name, u.last_name, g.name as group_name
                FROM blog_posts bp
                JOIN users u ON bp.author_id = u.id
                JOIN groups g ON bp.group_id = g.id
                WHERE bp.is_published = TRUE AND g.is_active = TRUE
                ORDER BY bp.published_at DESC
                LIMIT 10
            """)
            blog_posts = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return render_template('index.html', blog_posts=blog_posts)
        else:
            flash('Database connection error', 'danger')
            return render_template('index.html', blog_posts=[])
            
    except Exception as e:
        logger.error(f"Error loading index: {e}")
        return render_template('index.html', blog_posts=[])

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("""
                    SELECT u.*, r.name as role_name
                    FROM users u
                    JOIN roles r ON u.role_id = r.id
                    WHERE u.username = %s AND u.is_active = TRUE
                """, (username,))
                
                user = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if user and check_password_hash(user['password_hash'], password):
                    if user['is_banned']:
                        flash('Your account has been banned.', 'danger')
                        return render_template('login.html')
                    
                    # Set session variables
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['user_role'] = user['role_name']
                    session['group_id'] = user['group_id']
                    
                    # Update last login
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE users SET last_login = %s WHERE id = %s
                        """, (datetime.utcnow(), user['id']))
                        conn.commit()
                        cursor.close()
                        conn.close()
                    
                    # Log login activity
                    log_user_activity(user['id'], 'login')
                    
                    flash('Welcome back!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid username or password.', 'danger')
                    
        except Exception as e:
            logger.error(f"Login error: {e}")
            flash('An error occurred during login.', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                
                # Check if user already exists
                cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", 
                             (username, email))
                if cursor.fetchone():
                    flash('Username or email already exists.', 'danger')
                    return render_template('register.html')
                
                # Get default user role
                cursor.execute("SELECT id FROM roles WHERE name = 'User'")
                role_result = cursor.fetchone()
                default_role_id = role_result[0] if role_result else None
                
                # Create user
                password_hash = generate_password_hash(password)
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, first_name, last_name, role_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (username, email, password_hash, first_name, last_name, default_role_id))
                
                user_id = cursor.fetchone()[0]
                conn.commit()
                cursor.close()
                conn.close()
                
                # Log registration activity
                log_user_activity(user_id, 'register')
                
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            flash('An error occurred during registration.', 'danger')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """User logout"""
    user_id = session.get('user_id')
    if user_id:
        log_user_activity(user_id, 'logout')
    
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            user_id = session['user_id']
            user_role = session['user_role']
            group_id = session.get('group_id')
            
            # Get user statistics based on role
            if user_role == 'SuperAdmin':
                # SuperAdmin sees platform-wide stats
                cursor.execute("""
                    SELECT 
                        (SELECT COUNT(*) FROM users WHERE is_active = TRUE) as total_users,
                        (SELECT COUNT(*) FROM groups WHERE is_active = TRUE) as total_groups,
                        (SELECT COUNT(*) FROM blog_posts WHERE is_published = TRUE) as total_blog_posts,
                        (SELECT COUNT(*) FROM pages WHERE is_published = TRUE) as total_pages
                """)
            elif user_role == 'Admin':
                # Admin sees group-wide stats
                cursor.execute("""
                    SELECT 
                        (SELECT COUNT(*) FROM users WHERE group_id = %s AND is_active = TRUE) as total_users,
                        (SELECT COUNT(*) FROM blog_posts WHERE group_id = %s AND is_published = TRUE) as total_blog_posts,
                        (SELECT COUNT(*) FROM pages WHERE group_id = %s AND is_published = TRUE) as total_pages
                """, (group_id, group_id, group_id))
            else:
                # Regular users see their own stats
                cursor.execute("""
                    SELECT 
                        (SELECT COUNT(*) FROM blog_posts WHERE author_id = %s AND is_published = TRUE) as my_blog_posts,
                        (SELECT COUNT(*) FROM pages WHERE author_id = %s AND is_published = TRUE) as my_pages
                """, (user_id, user_id))
            
            stats = cursor.fetchone()
            
            # Get recent activity
            cursor.execute("""
                SELECT action, resource_type, created_at
                FROM user_activity_logs
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 10
            """, (user_id,))
            recent_activity = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return render_template('dashboard.html', 
                                 stats=stats, 
                                 recent_activity=recent_activity,
                                 user_role=user_role)
        else:
            flash('Database connection error', 'danger')
            return render_template('dashboard.html')
            
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return render_template('dashboard.html')

# Import additional route modules
from routes import blog, pages, admin, themes, api

# Register blueprints
app.register_blueprint(blog.bp)
app.register_blueprint(pages.bp)
app.register_blueprint(admin.bp)
app.register_blueprint(themes.bp)
app.register_blueprint(api.bp)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)