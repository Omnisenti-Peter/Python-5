"""
Admin routes for Opinian platform
Handles user management, permissions, and system administration
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from app import get_db_connection, login_required, role_required, log_user_activity

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/dashboard')
@login_required
@role_required(['SuperAdmin', 'Admin'])
def dashboard():
    """Admin dashboard"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            user_role = session['user_role']
            group_id = session.get('group_id')
            
            if user_role == 'SuperAdmin':
                # SuperAdmin sees platform-wide data
                cursor.execute("""
                    SELECT 
                        (SELECT COUNT(*) FROM users WHERE is_active = TRUE) as total_users,
                        (SELECT COUNT(*) FROM groups WHERE is_active = TRUE) as total_groups,
                        (SELECT COUNT(*) FROM blog_posts WHERE is_published = TRUE) as total_blog_posts,
                        (SELECT COUNT(*) FROM pages WHERE is_published = TRUE) as total_pages,
                        (SELECT COUNT(*) FROM users WHERE is_banned = TRUE) as banned_users,
                        (SELECT COUNT(*) FROM moderation_queue WHERE status = 'pending') as pending_moderation
                """)
            else:
                # Admin sees group-specific data
                cursor.execute("""
                    SELECT 
                        (SELECT COUNT(*) FROM users WHERE group_id = %s AND is_active = TRUE) as total_users,
                        (SELECT COUNT(*) FROM blog_posts WHERE group_id = %s AND is_published = TRUE) as total_blog_posts,
                        (SELECT COUNT(*) FROM pages WHERE group_id = %s AND is_published = TRUE) as total_pages,
                        (SELECT COUNT(*) FROM users WHERE group_id = %s AND is_banned = TRUE) as banned_users
                """, (group_id, group_id, group_id, group_id))
            
            stats = cursor.fetchone()
            
            # Get recent user activity
            if user_role == 'SuperAdmin':
                cursor.execute("""
                    SELECT ual.*, u.username
                    FROM user_activity_logs ual
                    JOIN users u ON ual.user_id = u.id
                    ORDER BY ual.created_at DESC
                    LIMIT 20
                """)
            else:
                cursor.execute("""
                    SELECT ual.*, u.username
                    FROM user_activity_logs ual
                    JOIN users u ON ual.user_id = u.id
                    WHERE u.group_id = %s
                    ORDER BY ual.created_at DESC
                    LIMIT 20
                """, (group_id,))
            
            recent_activity = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return render_template('admin/dashboard.html', 
                                 stats=stats, 
                                 recent_activity=recent_activity,
                                 user_role=user_role)
        else:
            flash('Database connection error', 'danger')
            return render_template('admin/dashboard.html')
            
    except Exception as e:
        flash('Error loading admin dashboard', 'danger')
        return render_template('admin/dashboard.html')

@bp.route('/users')
@login_required
@role_required(['SuperAdmin', 'Admin'])
def manage_users():
    """User management page"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            user_role = session['user_role']
            group_id = session.get('group_id')
            
            if user_role == 'SuperAdmin':
                # SuperAdmin sees all users
                cursor.execute("""
                    SELECT u.*, r.name as role_name, g.name as group_name
                    FROM users u
                    JOIN roles r ON u.role_id = r.id
                    LEFT JOIN groups g ON u.group_id = g.id
                    ORDER BY u.created_at DESC
                """)
            else:
                # Admin sees only users in their group
                cursor.execute("""
                    SELECT u.*, r.name as role_name, g.name as group_name
                    FROM users u
                    JOIN roles r ON u.role_id = r.id
                    JOIN groups g ON u.group_id = g.id
                    WHERE u.group_id = %s
                    ORDER BY u.created_at DESC
                """, (group_id,))
            
            users = cursor.fetchall()
            
            # Get available roles
            cursor.execute("SELECT id, name, description FROM roles ORDER BY id")
            roles = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return render_template('admin/users.html', users=users, roles=roles)
        else:
            flash('Database connection error', 'danger')
            return render_template('admin/users.html', users=[], roles=[])
            
    except Exception as e:
        flash('Error loading users', 'danger')
        return render_template('admin/users.html', users=[], roles=[])

@bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@role_required(['SuperAdmin', 'Admin'])
def create_user():
    """Create a new user"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        role_id = request.form.get('role_id')
        
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                
                # Check if user already exists
                cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", 
                             (username, email))
                if cursor.fetchone():
                    flash('Username or email already exists.', 'danger')
                    return redirect(url_for('admin.create_user'))
                
                # Create user
                password_hash = generate_password_hash(password)
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, first_name, last_name, role_id, group_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    username, email, password_hash, first_name, last_name, 
                    role_id, session.get('group_id')
                ))
                
                user_id = cursor.fetchone()[0]
                conn.commit()
                cursor.close()
                conn.close()
                
                # Log activity
                log_user_activity(session['user_id'], 'create_user', 'user', user_id)
                
                flash('User created successfully!', 'success')
                return redirect(url_for('admin.manage_users'))
                
        except Exception as e:
            flash('Error creating user', 'danger')
            logger.error(f"Error creating user: {e}")
    
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get available roles
            cursor.execute("SELECT id, name, description FROM roles ORDER BY id")
            roles = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return render_template('admin/create_user.html', roles=roles)
        else:
            flash('Database connection error', 'danger')
            return render_template('admin/create_user.html', roles=[])
            
    except Exception as e:
        flash('Error loading roles', 'danger')
        return render_template('admin/create_user.html', roles=[])

@bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required(['SuperAdmin', 'Admin'])
def edit_user(user_id):
    """Edit user details and permissions"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get user
            cursor.execute("""
                SELECT u.*, r.name as role_name, g.name as group_name
                FROM users u
                JOIN roles r ON u.role_id = r.id
                LEFT JOIN groups g ON u.group_id = g.id
                WHERE u.id = %s
            """, (user_id,))
            user = cursor.fetchone()
            
            if not user:
                flash('User not found', 'danger')
                return redirect(url_for('admin.manage_users'))
            
            # Check permissions
            if session['user_role'] == 'Admin' and user['group_id'] != session.get('group_id'):
                flash('You cannot edit users from other groups', 'danger')
                return redirect(url_for('admin.manage_users'))
            
            if request.method == 'POST':
                first_name = request.form.get('first_name')
                last_name = request.form.get('last_name')
                role_id = request.form.get('role_id')
                is_active = request.form.get('is_active') == 'on'
                is_banned = request.form.get('is_banned') == 'on'
                
                # Update user
                cursor.execute("""
                    UPDATE users 
                    SET first_name = %s, last_name = %s, role_id = %s, 
                        is_active = %s, is_banned = %s, updated_at = %s
                    WHERE id = %s
                """, (first_name, last_name, role_id, is_active, is_banned, datetime.utcnow(), user_id))
                
                conn.commit()
                
                # Log activity
                log_user_activity(session['user_id'], 'edit_user', 'user', user_id)
                
                flash('User updated successfully!', 'success')
                return redirect(url_for('admin.manage_users'))
            
            # Get available roles
            cursor.execute("SELECT id, name, description FROM roles ORDER BY id")
            roles = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return render_template('admin/edit_user.html', user=user, roles=roles)
        else:
            flash('Database connection error', 'danger')
            return redirect(url_for('admin.manage_users'))
            
    except Exception as e:
        flash('Error loading user', 'danger')
        logger.error(f"Error editing user: {e}")
        return redirect(url_for('admin.manage_users'))

@bp.route('/users/ban/<int:user_id>', methods=['POST'])
@login_required
@role_required(['SuperAdmin', 'Admin'])
def ban_user(user_id):
    """Ban or unban a user"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get user
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return jsonify({'success': False, 'message': 'User not found'}), 404
            
            # Check permissions
            if session['user_role'] == 'Admin' and user['group_id'] != session.get('group_id'):
                return jsonify({'success': False, 'message': 'Permission denied'}), 403
            
            # Toggle ban status
            new_status = not user['is_banned']
            cursor.execute("UPDATE users SET is_banned = %s WHERE id = %s", (new_status, user_id))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            # Log activity
            action = 'ban_user' if new_status else 'unban_user'
            log_user_activity(session['user_id'], action, 'user', user_id)
            
            return jsonify({
                'success': True, 
                'message': f'User {"banned" if new_status else "unbanned"} successfully',
                'is_banned': new_status
            })
            
    except Exception as e:
        logger.error(f"Error banning user: {e}")
        return jsonify({'success': False, 'message': 'Error updating user status'}), 500

@bp.route('/groups')
@login_required
@role_required(['SuperAdmin'])
def manage_groups():
    """Group management page (SuperAdmin only)"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT g.*, u.username as admin_username, t.name as theme_name
                FROM groups g
                LEFT JOIN users u ON g.admin_user_id = u.id
                LEFT JOIN themes t ON g.theme_id = t.id
                ORDER BY g.created_at DESC
            """)
            groups = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return render_template('admin/groups.html', groups=groups)
        else:
            flash('Database connection error', 'danger')
            return render_template('admin/groups.html', groups=[])
            
    except Exception as e:
        flash('Error loading groups', 'danger')
        return render_template('admin/groups.html', groups=[])

@bp.route('/activity-logs')
@login_required
@role_required(['SuperAdmin', 'Admin'])
def activity_logs():
    """View user activity logs"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            user_role = session['user_role']
            group_id = session.get('group_id')
            
            if user_role == 'SuperAdmin':
                cursor.execute("""
                    SELECT ual.*, u.username
                    FROM user_activity_logs ual
                    JOIN users u ON ual.user_id = u.id
                    ORDER BY ual.created_at DESC
                    LIMIT 100
                """)
            else:
                cursor.execute("""
                    SELECT ual.*, u.username
                    FROM user_activity_logs ual
                    JOIN users u ON ual.user_id = u.id
                    WHERE u.group_id = %s
                    ORDER BY ual.created_at DESC
                    LIMIT 100
                """, (group_id,))
            
            logs = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return render_template('admin/activity_logs.html', logs=logs)
        else:
            flash('Database connection error', 'danger')
            return render_template('admin/activity_logs.html', logs=[])
            
    except Exception as e:
        flash('Error loading activity logs', 'danger')
        return render_template('admin/activity_logs.html', logs=[])

@bp.route('/moderation')
@login_required
@role_required(['SuperAdmin', 'Admin'])
def moderation_queue():
    """Content moderation queue"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT mq.*, u.username
                FROM moderation_queue mq
                JOIN users u ON mq.content_id = u.id
                WHERE mq.status = 'pending'
                ORDER BY mq.created_at DESC
            """)
            queue_items = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return render_template('admin/moderation.html', queue_items=queue_items)
        else:
            flash('Database connection error', 'danger')
            return render_template('admin/moderation.html', queue_items=[])
            
    except Exception as e:
        flash('Error loading moderation queue', 'danger')
        return render_template('admin/moderation.html', queue_items=[])

@bp.route('/api-settings')
@login_required
@role_required(['SuperAdmin'])
def api_settings():
    """API settings management (SuperAdmin only)"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("SELECT * FROM api_settings ORDER BY setting_key")
            settings = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return render_template('admin/api_settings.html', settings=settings)
        else:
            flash('Database connection error', 'danger')
            return render_template('admin/api_settings.html', settings=[])
            
    except Exception as e:
        flash('Error loading API settings', 'danger')
        return render_template('admin/api_settings.html', settings=[])

@bp.route('/api-settings/update', methods=['POST'])
@login_required
@role_required(['SuperAdmin'])
def update_api_settings():
    """Update API settings"""
    try:
        data = request.get_json()
        setting_key = data.get('setting_key')
        setting_value = data.get('setting_value')
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO api_settings (setting_key, setting_value, updated_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (setting_key) 
                DO UPDATE SET setting_value = %s, updated_at = %s
            """, (setting_key, setting_value, datetime.utcnow(), setting_value, datetime.utcnow()))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Log activity
            log_user_activity(session['user_id'], 'update_api_settings', 'api_settings', None, {'key': setting_key})
            
            return jsonify({'success': True, 'message': 'Setting updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Database connection error'}), 500
            
    except Exception as e:
        logger.error(f"Error updating API settings: {e}")
        return jsonify({'success': False, 'message': 'Error updating setting'}), 500