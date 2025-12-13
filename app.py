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

# Configure Flask-Mail
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@opinian.com')

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

def get_active_theme(group_id):
    """Get the active theme for a group"""
    if not group_id:
        return None
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT t.* FROM themes t
                JOIN groups g ON g.theme_id = t.id
                WHERE g.id = %s
            """, (group_id,))
            theme = cursor.fetchone()
            cursor.close()
            conn.close()
            return theme
    except Exception as e:
        logger.error(f"Error loading theme: {e}")
        return None

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
                SELECT bp.*, u.username, u.first_name, u.last_name, u.profile_image_url, g.name as group_name
                FROM blog_posts bp
                JOIN users u ON bp.author_id = u.id
                LEFT JOIN groups g ON bp.group_id = g.id
                WHERE bp.is_published = TRUE AND (g.is_active = TRUE OR bp.group_id IS NULL)
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

                # Send welcome email
                from email_service import send_welcome_email
                user_name = f"{first_name} {last_name}"
                send_welcome_email(email, user_name, username, app=app)

                flash('Registration successful! Please check your email and log in.', 'success')
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


# ============== PROFILE EDIT ROUTE ==============

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    user_id = session.get('user_id')

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        bio = request.form.get('bio', '').strip()
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # Handle profile image upload
        profile_image_url = request.form.get('existing_profile_image', '').strip()
        profile_image = request.files.get('profile_image')

        if profile_image and profile_image.filename:
            # Validate file type
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            filename = secure_filename(profile_image.filename)
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

            if file_ext in allowed_extensions:
                # Create uploads directory if it doesn't exist
                upload_dir = os.path.join('static', 'uploads', 'profiles')
                os.makedirs(upload_dir, exist_ok=True)

                # Generate unique filename with user_id
                unique_filename = f"user_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
                file_path = os.path.join(upload_dir, unique_filename)

                # Check file size (max 5MB)
                profile_image.seek(0, os.SEEK_END)
                file_size = profile_image.tell()
                profile_image.seek(0)

                if file_size > 5 * 1024 * 1024:  # 5MB
                    flash('Profile image must be less than 5MB', 'danger')
                    return redirect(url_for('edit_profile'))

                # Save the file
                profile_image.save(file_path)
                profile_image_url = f"static/uploads/profiles/{unique_filename}"
                logger.info(f"Profile image saved: {profile_image_url}")
            else:
                flash('Invalid file type. Please upload PNG, JPG, or GIF', 'danger')
                return redirect(url_for('edit_profile'))

        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)

                # Get current user data
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()

                if not user:
                    flash('User not found', 'danger')
                    return redirect(url_for('index'))

                # If changing password, verify current password
                if new_password:
                    if not current_password:
                        flash('Please enter your current password to change it', 'danger')
                        return render_template('edit_profile.html', user=user)

                    if not check_password_hash(user['password_hash'], current_password):
                        flash('Current password is incorrect', 'danger')
                        return render_template('edit_profile.html', user=user)

                    if new_password != confirm_password:
                        flash('New passwords do not match', 'danger')
                        return render_template('edit_profile.html', user=user)

                    if len(new_password) < 6:
                        flash('New password must be at least 6 characters', 'danger')
                        return render_template('edit_profile.html', user=user)

                    # Update with new password
                    password_hash = generate_password_hash(new_password)
                    cursor.execute("""
                        UPDATE users
                        SET first_name = %s, last_name = %s, bio = %s,
                            profile_image_url = %s, password_hash = %s, updated_at = %s
                        WHERE id = %s
                    """, (first_name, last_name, bio, profile_image_url, password_hash, datetime.utcnow(), user_id))
                else:
                    # Update without password change
                    cursor.execute("""
                        UPDATE users
                        SET first_name = %s, last_name = %s, bio = %s,
                            profile_image_url = %s, updated_at = %s
                        WHERE id = %s
                    """, (first_name, last_name, bio, profile_image_url, datetime.utcnow(), user_id))

                conn.commit()

                # Update session with new name
                session['first_name'] = first_name
                session['last_name'] = last_name

                # Log activity
                log_user_activity(user_id, 'update_profile', 'user', user_id)

                cursor.close()
                conn.close()

                flash('Profile updated successfully!', 'success')
                return redirect(url_for('edit_profile'))

        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            flash('Error updating profile', 'danger')

    # GET request - show form
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT u.*, r.name as role_name, g.name as group_name
                FROM users u
                JOIN roles r ON u.role_id = r.id
                LEFT JOIN groups g ON u.group_id = g.id
                WHERE u.id = %s
            """, (user_id,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            return render_template('edit_profile.html', user=user)
        else:
            flash('Database connection error', 'danger')
            return redirect(url_for('index'))

    except Exception as e:
        logger.error(f"Error loading profile: {e}")
        flash('Error loading profile', 'danger')
        return redirect(url_for('index'))


# ============== PASSWORD RESET ROUTES ==============

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()

        if not email:
            flash('Please enter your email address.', 'danger')
            return render_template('forgot_password.html')

        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)

                # Find user by email
                cursor.execute("SELECT id, username, first_name, last_name, email FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()

                if user:
                    import secrets

                    # Generate reset token
                    token = secrets.token_urlsafe(32)
                    expires_at = datetime.utcnow() + timedelta(hours=1)

                    # Store token in database
                    cursor.execute("""
                        INSERT INTO password_reset_tokens (user_id, token, expires_at)
                        VALUES (%s, %s, %s)
                    """, (user['id'], token, expires_at))
                    conn.commit()

                    # Send password reset email
                    from email_service import send_password_reset_email
                    user_name = f"{user['first_name']} {user['last_name']}"
                    send_password_reset_email(user['email'], token, user_name, app=app)

                    # Log activity
                    log_user_activity(user['id'], 'request_password_reset')

                cursor.close()
                conn.close()

                # Always show success message (security best practice)
                flash('If an account with that email exists, a password reset link has been sent.', 'success')
                return redirect(url_for('login'))

        except Exception as e:
            logger.error(f"Password reset request error: {e}")
            flash('An error occurred. Please try again.', 'danger')

    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection error', 'danger')
            return redirect(url_for('login'))

        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Verify token
        cursor.execute("""
            SELECT prt.*, u.id as user_id, u.username, u.email
            FROM password_reset_tokens prt
            JOIN users u ON prt.user_id = u.id
            WHERE prt.token = %s AND prt.used = FALSE AND prt.expires_at > %s
        """, (token, datetime.utcnow()))

        token_data = cursor.fetchone()

        if not token_data:
            cursor.close()
            conn.close()
            flash('Invalid or expired password reset link.', 'danger')
            return redirect(url_for('login'))

        if request.method == 'POST':
            new_password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            if not new_password or not confirm_password:
                flash('Please fill in all fields.', 'danger')
                return render_template('reset_password.html', token=token)

            if new_password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return render_template('reset_password.html', token=token)

            if len(new_password) < 6:
                flash('Password must be at least 6 characters long.', 'danger')
                return render_template('reset_password.html', token=token)

            # Update password
            password_hash = generate_password_hash(new_password)
            cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s",
                          (password_hash, token_data['user_id']))

            # Mark token as used
            cursor.execute("UPDATE password_reset_tokens SET used = TRUE WHERE token = %s", (token,))
            conn.commit()

            # Log activity
            log_user_activity(token_data['user_id'], 'reset_password')

            cursor.close()
            conn.close()

            flash('Your password has been reset successfully. Please log in.', 'success')
            return redirect(url_for('login'))

        cursor.close()
        conn.close()
        return render_template('reset_password.html', token=token)

    except Exception as e:
        logger.error(f"Password reset error: {e}")
        flash('An error occurred. Please try again.', 'danger')
        return redirect(url_for('login'))


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

# Route to serve uploaded files
from flask import send_from_directory

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Context processor to inject active theme into all templates
@app.context_processor
def inject_active_theme():
    """Inject the active theme for the current user's group into all templates"""
    theme = None
    if 'group_id' in session:
        theme = get_active_theme(session['group_id'])
    return {'active_theme': theme}

def make_breadcrumbs(*crumbs):
    """
    Helper function to create breadcrumb navigation

    Usage:
        breadcrumbs = make_breadcrumbs(
            ('Home', url_for('index')),
            ('Admin', url_for('admin.dashboard')),
            ('Users', None)  # Current page (no link)
        )

    Returns list of dicts: [{'name': 'Home', 'url': '/'}]
    """
    result = []
    for crumb in crumbs:
        if isinstance(crumb, tuple) and len(crumb) == 2:
            name, url = crumb
            result.append({'name': name, 'url': url})
        elif isinstance(crumb, dict):
            result.append(crumb)
    return result

# Make breadcrumb helper available in templates
app.jinja_env.globals['make_breadcrumbs'] = make_breadcrumbs

# Import additional route modules
from routes import blog, pages, admin, themes, api, media, search

# Register blueprints
app.register_blueprint(blog.bp)
app.register_blueprint(pages.bp)
app.register_blueprint(admin.bp)
app.register_blueprint(themes.bp)
app.register_blueprint(api.bp)
app.register_blueprint(media.bp)
app.register_blueprint(search.bp)

# Initialize email service
from email_service import init_mail
init_mail(app)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)