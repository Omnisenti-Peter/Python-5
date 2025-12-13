"""
Admin routes for Opinian platform
Handles user management, permissions, and system administration
"""

import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from app import get_db_connection, login_required, role_required, log_user_activity

logger = logging.getLogger(__name__)

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
                        (SELECT COUNT(*) FROM users WHERE group_id = %s AND is_banned = TRUE) as banned_users,
                        (SELECT COUNT(*) FROM moderation_queue mq
                         LEFT JOIN blog_posts bp ON mq.content_type = 'blog_post' AND mq.content_id = bp.id
                         LEFT JOIN pages p ON mq.content_type = 'page' AND mq.content_id = p.id
                         WHERE mq.status = 'pending' AND (bp.group_id = %s OR p.group_id = %s)) as pending_moderation
                """, (group_id, group_id, group_id, group_id, group_id, group_id))
            
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
    """Create a new user

    NOTE: When SuperAdmin creates an Admin user, an organization (group) is automatically created.
    Admin users can only create User and SuperUser types within their organization.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        role_id = request.form.get('role_id')

        # Validate required fields
        if not username or not email or not password:
            flash('Username, email, and password are required.', 'danger')
            return redirect(url_for('admin.create_user'))

        # Validate and convert role_id to integer
        if not role_id or role_id == '' or role_id == '0':
            flash('Please select a valid role.', 'danger')
            return redirect(url_for('admin.create_user'))

        try:
            role_id = int(role_id)
        except ValueError:
            flash('Invalid role selected.', 'danger')
            return redirect(url_for('admin.create_user'))

        # Handle group assignment based on user role being created
        group_id = None
        organization_name = None
        organization_description = None

        if session['user_role'] == 'SuperAdmin':
            # Check if creating an Admin user - need organization name
            organization_name = request.form.get('organization_name', '').strip()
            organization_description = request.form.get('organization_description', '').strip()

            # For non-Admin roles, allow selecting existing group
            group_id = request.form.get('group_id')
            if group_id and group_id != '' and group_id != '0':
                try:
                    group_id = int(group_id)
                except ValueError:
                    flash('Invalid group selected.', 'danger')
                    return redirect(url_for('admin.create_user'))
            else:
                group_id = None
        else:
            # Admin users can only create within their own group
            group_id = session.get('group_id')

        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)

                # Check if user already exists
                cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s",
                             (username, email))
                if cursor.fetchone():
                    flash('Username or email already exists.', 'danger')
                    cursor.close()
                    conn.close()
                    return redirect(url_for('admin.create_user'))

                # Get the selected role to validate permissions
                cursor.execute("SELECT name FROM roles WHERE id = %s", (role_id,))
                role_result = cursor.fetchone()

                if not role_result:
                    flash('Invalid role selected.', 'danger')
                    cursor.close()
                    conn.close()
                    return redirect(url_for('admin.create_user'))

                role_name = role_result['name']

                # Validate: Admin can only create User and SuperUser roles within their group
                if session['user_role'] == 'Admin':
                    if role_name not in ['User', 'SuperUser']:
                        flash('You can only create User and SuperUser roles.', 'danger')
                        cursor.close()
                        conn.close()
                        return redirect(url_for('admin.create_user'))

                    if not group_id:
                        flash('Admin users must be assigned to a group.', 'danger')
                        cursor.close()
                        conn.close()
                        return redirect(url_for('admin.create_user'))

                # SuperAdmin creating an Admin user: Auto-create organization
                if session['user_role'] == 'SuperAdmin' and role_name == 'Admin':
                    if not organization_name:
                        flash('Organization name is required when creating an Admin user.', 'danger')
                        cursor.close()
                        conn.close()
                        return redirect(url_for('admin.create_user'))

                    # Check if organization name already exists
                    cursor.execute("SELECT id FROM groups WHERE name = %s", (organization_name,))
                    if cursor.fetchone():
                        flash(f'Organization "{organization_name}" already exists. Please choose a different name.', 'danger')
                        cursor.close()
                        conn.close()
                        return redirect(url_for('admin.create_user'))

                    # Create the organization first (without admin_user_id, we'll update it after creating user)
                    cursor.execute("""
                        INSERT INTO groups (name, description, is_active)
                        VALUES (%s, %s, TRUE)
                        RETURNING id
                    """, (organization_name, organization_description or f'Organization for {organization_name}'))

                    group_id = cursor.fetchone()['id']
                    logger.info(f"Created organization '{organization_name}' with ID {group_id}")

                # Validate: Non-Admin users created by SuperAdmin should have a group selected
                if session['user_role'] == 'SuperAdmin' and role_name != 'Admin' and role_name != 'SuperAdmin':
                    if not group_id:
                        flash('Please select an organization for this user.', 'danger')
                        cursor.close()
                        conn.close()
                        return redirect(url_for('admin.create_user'))

                # Create user
                password_hash = generate_password_hash(password)
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, first_name, last_name, role_id, group_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    username, email, password_hash, first_name, last_name,
                    role_id, group_id
                ))

                user_id = cursor.fetchone()['id']

                # If we created an Admin user with a new organization, link them
                if session['user_role'] == 'SuperAdmin' and role_name == 'Admin' and group_id:
                    cursor.execute("""
                        UPDATE groups SET admin_user_id = %s WHERE id = %s
                    """, (user_id, group_id))
                    logger.info(f"Linked Admin user {user_id} to organization {group_id}")

                conn.commit()
                cursor.close()
                conn.close()

                # Log activity
                log_user_activity(session['user_id'], 'create_user', 'user', user_id)

                flash('User created successfully!', 'success')
                return redirect(url_for('admin.manage_users'))

        except Exception as e:
            if 'conn' in locals() and conn:
                conn.rollback()
                if 'cursor' in locals() and cursor:
                    cursor.close()
                conn.close()
            flash(f'Error creating user: {str(e)}', 'danger')
            logger.error(f"Error creating user: {type(e).__name__}: {str(e)}")
            logger.exception("Full traceback:")
            return redirect(url_for('admin.create_user'))

    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Get available roles based on user's role
            if session['user_role'] == 'SuperAdmin':
                cursor.execute("SELECT id, name, description FROM roles ORDER BY id")
            else:
                # Admin can only create User and SuperUser roles
                cursor.execute("""
                    SELECT id, name, description FROM roles
                    WHERE name IN ('User', 'SuperUser')
                    ORDER BY id
                """)
            roles = cursor.fetchall()

            # Get available groups (only for SuperAdmin)
            groups = []
            if session['user_role'] == 'SuperAdmin':
                cursor.execute("""
                    SELECT id, name FROM groups
                    WHERE is_active = TRUE
                    ORDER BY name
                """)
                groups = cursor.fetchall()

            cursor.close()
            conn.close()

            return render_template('admin/create_user.html', roles=roles, groups=groups)
        else:
            flash('Database connection error', 'danger')
            return render_template('admin/create_user.html', roles=[], groups=[])

    except Exception as e:
        flash('Error loading roles', 'danger')
        logger.error(f"Error loading create user form: {e}")
        return render_template('admin/create_user.html', roles=[], groups=[])

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

                # For SuperAdmin, allow changing group; for Admin, keep their group
                if session['user_role'] == 'SuperAdmin':
                    group_id = request.form.get('group_id')
                    group_id = int(group_id) if group_id else None
                else:
                    group_id = user['group_id']  # Keep existing group for Admin

                # Update user
                cursor.execute("""
                    UPDATE users
                    SET first_name = %s, last_name = %s, role_id = %s, group_id = %s,
                        is_active = %s, is_banned = %s, updated_at = %s
                    WHERE id = %s
                """, (first_name, last_name, role_id, group_id, is_active, is_banned, datetime.utcnow(), user_id))

                conn.commit()

                # Log activity
                log_user_activity(session['user_id'], 'edit_user', 'user', user_id)

                flash('User updated successfully!', 'success')
                return redirect(url_for('admin.manage_users'))
            
            # Get available roles
            cursor.execute("SELECT id, name, description FROM roles ORDER BY id")
            roles = cursor.fetchall()

            # Get available groups (only for SuperAdmin)
            groups = []
            if session['user_role'] == 'SuperAdmin':
                cursor.execute("""
                    SELECT id, name FROM groups
                    WHERE is_active = TRUE
                    ORDER BY name
                """)
                groups = cursor.fetchall()

            cursor.close()
            conn.close()

            return render_template('admin/edit_user.html', user=user, roles=roles, groups=groups)
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
                SELECT g.*, u.username as admin_username, u.email as admin_email, t.name as theme_name,
                       (SELECT COUNT(*) FROM users WHERE group_id = g.id) as user_count,
                       (SELECT COUNT(*) FROM blog_posts WHERE group_id = g.id) as post_count
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
        logger.error(f"Error loading groups: {e}")
        return render_template('admin/groups.html', groups=[])

@bp.route('/groups/create', methods=['GET', 'POST'])
@login_required
@role_required(['SuperAdmin'])
def create_group():
    """Create a new organization (group) - Special cases only

    NOTE: Organizations are normally created automatically when creating Admin users.
    This route is for special cases like creating an organization without an admin yet,
    or reassigning existing admins to new organizations.
    """
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        admin_user_id = request.form.get('admin_user_id')
        theme_id = request.form.get('theme_id')

        # Convert theme_id to int or None
        if theme_id and theme_id != '':
            try:
                theme_id = int(theme_id)
            except ValueError:
                theme_id = None
        else:
            theme_id = None

        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()

                # Check if group name already exists
                cursor.execute("SELECT id FROM groups WHERE name = %s", (name,))
                if cursor.fetchone():
                    flash('Group name already exists.', 'danger')
                    cursor.close()
                    conn.close()
                    return redirect(url_for('admin.create_group'))

                # Create group
                cursor.execute("""
                    INSERT INTO groups (name, description, admin_user_id, theme_id)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (name, description, admin_user_id if admin_user_id else None, theme_id))

                group_id = cursor.fetchone()[0]

                # Update admin user's group_id
                if admin_user_id:
                    cursor.execute("""
                        UPDATE users SET group_id = %s WHERE id = %s
                    """, (group_id, admin_user_id))

                conn.commit()
                cursor.close()
                conn.close()

                # Log activity
                log_user_activity(session['user_id'], 'create_group', 'group', group_id)

                flash('Group created successfully!', 'success')
                return redirect(url_for('admin.manage_groups'))

        except Exception as e:
            flash('Error creating group', 'danger')
            logger.error(f"Error creating group: {e}")

    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Get all admin users (allow reassignment)
            cursor.execute("""
                SELECT u.id, u.username, u.email, u.first_name, u.last_name,
                       g.name as current_group
                FROM users u
                JOIN roles r ON u.role_id = r.id
                LEFT JOIN groups g ON u.group_id = g.id
                WHERE r.name IN ('Admin', 'SuperAdmin')
                ORDER BY u.username
            """)
            available_admins = cursor.fetchall()

            # Get all themes
            cursor.execute("""
                SELECT id, name, description, theme_type
                FROM themes
                WHERE is_active = TRUE
                ORDER BY name
            """)
            themes = cursor.fetchall()

            cursor.close()
            conn.close()

            return render_template('admin/create_group.html',
                                 available_admins=available_admins,
                                 themes=themes)
        else:
            flash('Database connection error', 'danger')
            return render_template('admin/create_group.html',
                                 available_admins=[],
                                 themes=[])

    except Exception as e:
        flash('Error loading form', 'danger')
        logger.error(f"Error loading create group form: {e}")
        return render_template('admin/create_group.html',
                             available_admins=[],
                             themes=[])

@bp.route('/groups/edit/<int:group_id>', methods=['GET', 'POST'])
@login_required
@role_required(['SuperAdmin'])
def edit_group(group_id):
    """Edit group details"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Get group
            cursor.execute("""
                SELECT g.*, u.username as admin_username
                FROM groups g
                LEFT JOIN users u ON g.admin_user_id = u.id
                WHERE g.id = %s
            """, (group_id,))
            group = cursor.fetchone()

            if not group:
                flash('Group not found', 'danger')
                cursor.close()
                conn.close()
                return redirect(url_for('admin.manage_groups'))

            if request.method == 'POST':
                name = request.form.get('name')
                description = request.form.get('description')
                admin_user_id = request.form.get('admin_user_id')
                theme_id = request.form.get('theme_id')
                contact_page_content = request.form.get('contact_page_content')
                about_page_content = request.form.get('about_page_content')
                is_active = request.form.get('is_active') == 'on'

                # Convert theme_id to int or None
                if theme_id and theme_id != '':
                    try:
                        theme_id = int(theme_id)
                    except ValueError:
                        theme_id = None
                else:
                    theme_id = None

                # Check if name is taken by another group
                cursor.execute("SELECT id FROM groups WHERE name = %s AND id != %s", (name, group_id))
                if cursor.fetchone():
                    flash('Group name already exists.', 'danger')
                else:
                    # Update group
                    cursor.execute("""
                        UPDATE groups
                        SET name = %s, description = %s, admin_user_id = %s, theme_id = %s,
                            contact_page_content = %s, about_page_content = %s,
                            is_active = %s, updated_at = %s
                        WHERE id = %s
                    """, (name, description, admin_user_id if admin_user_id else None, theme_id,
                          contact_page_content, about_page_content, is_active,
                          datetime.utcnow(), group_id))

                    # Update admin user's group_id
                    if admin_user_id:
                        cursor.execute("UPDATE users SET group_id = %s WHERE id = %s", (group_id, admin_user_id))

                    conn.commit()

                    # Log activity
                    log_user_activity(session['user_id'], 'edit_group', 'group', group_id)

                    flash('Group updated successfully!', 'success')
                    return redirect(url_for('admin.manage_groups'))

            # Get available admin users
            cursor.execute("""
                SELECT u.id, u.username, u.email, u.first_name, u.last_name
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE r.name IN ('Admin', 'SuperAdmin')
                ORDER BY u.username
            """)
            available_admins = cursor.fetchall()

            # Get themes
            cursor.execute("SELECT id, name FROM themes ORDER BY name")
            themes = cursor.fetchall()

            cursor.close()
            conn.close()

            return render_template('admin/edit_group.html', group=group,
                                 available_admins=available_admins, themes=themes)
        else:
            flash('Database connection error', 'danger')
            return redirect(url_for('admin.manage_groups'))

    except Exception as e:
        flash('Error loading group', 'danger')
        logger.error(f"Error editing group: {e}")
        return redirect(url_for('admin.manage_groups'))

@bp.route('/groups/view/<int:group_id>')
@login_required
@role_required(['SuperAdmin'])
def view_group(group_id):
    """View group details"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Get group details
            cursor.execute("""
                SELECT g.*, u.username as admin_username, u.email as admin_email,
                       u.first_name as admin_first_name, u.last_name as admin_last_name,
                       t.name as theme_name
                FROM groups g
                LEFT JOIN users u ON g.admin_user_id = u.id
                LEFT JOIN themes t ON g.theme_id = t.id
                WHERE g.id = %s
            """, (group_id,))
            group = cursor.fetchone()

            if not group:
                flash('Group not found', 'danger')
                return redirect(url_for('admin.manage_groups'))

            # Get group statistics
            cursor.execute("""
                SELECT
                    (SELECT COUNT(*) FROM users WHERE group_id = %s) as total_users,
                    (SELECT COUNT(*) FROM blog_posts WHERE group_id = %s) as total_posts,
                    (SELECT COUNT(*) FROM pages WHERE group_id = %s) as total_pages,
                    (SELECT COUNT(*) FROM users WHERE group_id = %s AND is_active = TRUE) as active_users
            """, (group_id, group_id, group_id, group_id))
            stats = cursor.fetchone()

            # Get group users
            cursor.execute("""
                SELECT u.*, r.name as role_name
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE u.group_id = %s
                ORDER BY u.created_at DESC
                LIMIT 10
            """, (group_id,))
            users = cursor.fetchall()

            # Get recent blog posts
            cursor.execute("""
                SELECT bp.*, u.username as author_username
                FROM blog_posts bp
                JOIN users u ON bp.author_id = u.id
                WHERE bp.group_id = %s
                ORDER BY bp.created_at DESC
                LIMIT 10
            """, (group_id,))
            posts = cursor.fetchall()

            cursor.close()
            conn.close()

            return render_template('admin/view_group.html', group=group, stats=stats,
                                 users=users, posts=posts)
        else:
            flash('Database connection error', 'danger')
            return redirect(url_for('admin.manage_groups'))

    except Exception as e:
        flash('Error loading group', 'danger')
        logger.error(f"Error viewing group: {e}")
        return redirect(url_for('admin.manage_groups'))

@bp.route('/groups/delete/<int:group_id>', methods=['POST'])
@login_required
@role_required(['SuperAdmin'])
def delete_group(group_id):
    """Delete a group (soft delete by setting is_active to false)"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()

            # Check if group exists
            cursor.execute("SELECT id FROM groups WHERE id = %s", (group_id,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'message': 'Group not found'}), 404

            # Soft delete - set is_active to false
            cursor.execute("UPDATE groups SET is_active = FALSE, updated_at = %s WHERE id = %s",
                         (datetime.utcnow(), group_id))
            conn.commit()

            cursor.close()
            conn.close()

            # Log activity
            log_user_activity(session['user_id'], 'delete_group', 'group', group_id)

            return jsonify({'success': True, 'message': 'Group deactivated successfully'})

    except Exception as e:
        logger.error(f"Error deleting group: {e}")
        return jsonify({'success': False, 'message': 'Error deleting group'}), 500

@bp.route('/groups/toggle/<int:group_id>', methods=['POST'])
@login_required
@role_required(['SuperAdmin'])
def toggle_group(group_id):
    """Toggle group active status"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Get current status
            cursor.execute("SELECT is_active FROM groups WHERE id = %s", (group_id,))
            result = cursor.fetchone()

            if not result:
                return jsonify({'success': False, 'message': 'Group not found'}), 404

            # Toggle status
            new_status = not result['is_active']
            cursor.execute("UPDATE groups SET is_active = %s, updated_at = %s WHERE id = %s",
                         (new_status, datetime.utcnow(), group_id))
            conn.commit()

            cursor.close()
            conn.close()

            # Log activity
            action = 'activate_group' if new_status else 'deactivate_group'
            log_user_activity(session['user_id'], action, 'group', group_id)

            return jsonify({
                'success': True,
                'message': f'Group {"activated" if new_status else "deactivated"} successfully',
                'is_active': new_status
            })

    except Exception as e:
        logger.error(f"Error toggling group status: {e}")
        return jsonify({'success': False, 'message': 'Error updating group status'}), 500

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
    """Content moderation queue with detailed content information"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            user_role = session['user_role']
            group_id = session.get('group_id')

            # Fetch pending items with content details
            queue_items = []

            # Get blog posts pending moderation
            if user_role == 'SuperAdmin':
                cursor.execute("""
                    SELECT mq.id as queue_id, mq.content_type, mq.content_id, mq.status,
                           mq.created_at, mq.review_notes,
                           bp.title, bp.excerpt, bp.slug, bp.is_published,
                           u.id as author_id, u.username, u.first_name, u.last_name, u.email,
                           g.name as group_name
                    FROM moderation_queue mq
                    JOIN blog_posts bp ON mq.content_id = bp.id
                    JOIN users u ON bp.author_id = u.id
                    LEFT JOIN groups g ON bp.group_id = g.id
                    WHERE mq.content_type = 'blog_post' AND mq.status = 'pending'
                    ORDER BY mq.created_at DESC
                """)
            else:
                cursor.execute("""
                    SELECT mq.id as queue_id, mq.content_type, mq.content_id, mq.status,
                           mq.created_at, mq.review_notes,
                           bp.title, bp.excerpt, bp.slug, bp.is_published,
                           u.id as author_id, u.username, u.first_name, u.last_name, u.email
                    FROM moderation_queue mq
                    JOIN blog_posts bp ON mq.content_id = bp.id
                    JOIN users u ON bp.author_id = u.id
                    WHERE mq.content_type = 'blog_post' AND mq.status = 'pending'
                          AND bp.group_id = %s
                    ORDER BY mq.created_at DESC
                """, (group_id,))

            blog_posts = cursor.fetchall()
            queue_items.extend(blog_posts)

            # Get pages pending moderation
            if user_role == 'SuperAdmin':
                cursor.execute("""
                    SELECT mq.id as queue_id, mq.content_type, mq.content_id, mq.status,
                           mq.created_at, mq.review_notes,
                           p.title, p.slug, p.is_published,
                           u.id as author_id, u.username, u.first_name, u.last_name, u.email,
                           g.name as group_name
                    FROM moderation_queue mq
                    JOIN pages p ON mq.content_id = p.id
                    JOIN users u ON p.author_id = u.id
                    LEFT JOIN groups g ON p.group_id = g.id
                    WHERE mq.content_type = 'page' AND mq.status = 'pending'
                    ORDER BY mq.created_at DESC
                """)
            else:
                cursor.execute("""
                    SELECT mq.id as queue_id, mq.content_type, mq.content_id, mq.status,
                           mq.created_at, mq.review_notes,
                           p.title, p.slug, p.is_published,
                           u.id as author_id, u.username, u.first_name, u.last_name, u.email
                    FROM moderation_queue mq
                    JOIN pages p ON mq.content_id = p.id
                    JOIN users u ON p.author_id = u.id
                    WHERE mq.content_type = 'page' AND mq.status = 'pending'
                          AND p.group_id = %s
                    ORDER BY mq.created_at DESC
                """, (group_id,))

            pages = cursor.fetchall()
            queue_items.extend(pages)

            # Get moderation stats
            if user_role == 'SuperAdmin':
                cursor.execute("""
                    SELECT
                        COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
                        COUNT(*) FILTER (WHERE status = 'approved') as approved_count,
                        COUNT(*) FILTER (WHERE status = 'rejected') as rejected_count,
                        COUNT(*) as total_count
                    FROM moderation_queue
                """)
            else:
                cursor.execute("""
                    SELECT
                        COUNT(*) FILTER (WHERE mq.status = 'pending') as pending_count,
                        COUNT(*) FILTER (WHERE mq.status = 'approved') as approved_count,
                        COUNT(*) FILTER (WHERE mq.status = 'rejected') as rejected_count,
                        COUNT(*) as total_count
                    FROM moderation_queue mq
                    LEFT JOIN blog_posts bp ON mq.content_type = 'blog_post' AND mq.content_id = bp.id
                    LEFT JOIN pages p ON mq.content_type = 'page' AND mq.content_id = p.id
                    WHERE (bp.group_id = %s OR p.group_id = %s)
                """, (group_id, group_id))

            stats = cursor.fetchone()

            cursor.close()
            conn.close()

            return render_template('admin/moderation.html', queue_items=queue_items, stats=stats)
        else:
            flash('Database connection error', 'danger')
            return render_template('admin/moderation.html', queue_items=[], stats={})

    except Exception as e:
        flash('Error loading moderation queue', 'danger')
        logger.error(f"Error loading moderation queue: {e}")
        return render_template('admin/moderation.html', queue_items=[], stats={})


@bp.route('/moderation/<int:queue_id>/approve', methods=['POST'])
@login_required
@role_required(['SuperAdmin', 'Admin'])
def approve_moderation(queue_id):
    """Approve content in moderation queue"""
    try:
        review_notes = request.form.get('review_notes', '')

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Get queue item
            cursor.execute("""
                SELECT mq.*, u.email, u.first_name, u.last_name
                FROM moderation_queue mq
                LEFT JOIN blog_posts bp ON mq.content_type = 'blog_post' AND mq.content_id = bp.id
                LEFT JOIN pages p ON mq.content_type = 'page' AND mq.content_id = p.id
                LEFT JOIN users u ON (bp.author_id = u.id OR p.author_id = u.id)
                WHERE mq.id = %s
            """, (queue_id,))
            item = cursor.fetchone()

            if not item:
                flash('Moderation item not found', 'danger')
                return redirect(url_for('admin.moderation_queue'))

            # Update moderation queue
            cursor.execute("""
                UPDATE moderation_queue
                SET status = 'approved', reviewed_by = %s, reviewed_at = %s, review_notes = %s
                WHERE id = %s
            """, (session['user_id'], datetime.utcnow(), review_notes, queue_id))

            # Publish the content
            if item['content_type'] == 'blog_post':
                cursor.execute("""
                    UPDATE blog_posts SET is_published = TRUE, published_at = %s
                    WHERE id = %s
                """, (datetime.utcnow(), item['content_id']))
            elif item['content_type'] == 'page':
                cursor.execute("""
                    UPDATE pages SET is_published = TRUE, published_at = %s
                    WHERE id = %s
                """, (datetime.utcnow(), item['content_id']))

            conn.commit()

            # Log activity
            log_user_activity(session['user_id'], 'approve_content', item['content_type'], item['content_id'])

            # Send notification email to author
            if item.get('email'):
                from email_service import send_moderation_decision_email
                from flask import current_app
                send_moderation_decision_email(
                    item['email'],
                    f"{item['first_name']} {item['last_name']}",
                    item['content_type'],
                    'approved',
                    review_notes,
                    app=current_app._get_current_object()
                )

            cursor.close()
            conn.close()

            flash('Content approved and published successfully', 'success')
            return redirect(url_for('admin.moderation_queue'))

    except Exception as e:
        flash('Error approving content', 'danger')
        logger.error(f"Error approving content: {e}")
        return redirect(url_for('admin.moderation_queue'))


@bp.route('/moderation/<int:queue_id>/reject', methods=['POST'])
@login_required
@role_required(['SuperAdmin', 'Admin'])
def reject_moderation(queue_id):
    """Reject content in moderation queue"""
    try:
        review_notes = request.form.get('review_notes', '')

        if not review_notes:
            flash('Please provide a reason for rejection', 'warning')
            return redirect(url_for('admin.moderation_queue'))

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Get queue item
            cursor.execute("""
                SELECT mq.*, u.email, u.first_name, u.last_name
                FROM moderation_queue mq
                LEFT JOIN blog_posts bp ON mq.content_type = 'blog_post' AND mq.content_id = bp.id
                LEFT JOIN pages p ON mq.content_type = 'page' AND mq.content_id = p.id
                LEFT JOIN users u ON (bp.author_id = u.id OR p.author_id = u.id)
                WHERE mq.id = %s
            """, (queue_id,))
            item = cursor.fetchone()

            if not item:
                flash('Moderation item not found', 'danger')
                return redirect(url_for('admin.moderation_queue'))

            # Update moderation queue
            cursor.execute("""
                UPDATE moderation_queue
                SET status = 'rejected', reviewed_by = %s, reviewed_at = %s, review_notes = %s
                WHERE id = %s
            """, (session['user_id'], datetime.utcnow(), review_notes, queue_id))

            conn.commit()

            # Log activity
            log_user_activity(session['user_id'], 'reject_content', item['content_type'], item['content_id'])

            # Send notification email to author
            if item.get('email'):
                from email_service import send_moderation_decision_email
                from flask import current_app
                send_moderation_decision_email(
                    item['email'],
                    f"{item['first_name']} {item['last_name']}",
                    item['content_type'],
                    'rejected',
                    review_notes,
                    app=current_app._get_current_object()
                )

            cursor.close()
            conn.close()

            flash('Content rejected', 'success')
            return redirect(url_for('admin.moderation_queue'))

    except Exception as e:
        flash('Error rejecting content', 'danger')
        logger.error(f"Error rejecting content: {e}")
        return redirect(url_for('admin.moderation_queue'))


@bp.route('/moderation/bulk-action', methods=['POST'])
@login_required
@role_required(['SuperAdmin', 'Admin'])
def bulk_moderation_action():
    """Perform bulk moderation actions"""
    try:
        action = request.form.get('action')
        queue_ids = request.form.getlist('queue_ids[]')
        review_notes = request.form.get('bulk_review_notes', '')

        if not queue_ids:
            flash('No items selected', 'warning')
            return redirect(url_for('admin.moderation_queue'))

        if action not in ['approve', 'reject']:
            flash('Invalid action', 'danger')
            return redirect(url_for('admin.moderation_queue'))

        if action == 'reject' and not review_notes:
            flash('Please provide a reason for bulk rejection', 'warning')
            return redirect(url_for('admin.moderation_queue'))

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            success_count = 0
            for queue_id in queue_ids:
                try:
                    # Get queue item
                    cursor.execute("""
                        SELECT * FROM moderation_queue WHERE id = %s
                    """, (queue_id,))
                    item = cursor.fetchone()

                    if not item:
                        continue

                    # Update moderation queue
                    status = 'approved' if action == 'approve' else 'rejected'
                    cursor.execute("""
                        UPDATE moderation_queue
                        SET status = %s, reviewed_by = %s, reviewed_at = %s, review_notes = %s
                        WHERE id = %s
                    """, (status, session['user_id'], datetime.utcnow(), review_notes, queue_id))

                    # Publish content if approved
                    if action == 'approve':
                        if item['content_type'] == 'blog_post':
                            cursor.execute("""
                                UPDATE blog_posts SET is_published = TRUE, published_at = %s
                                WHERE id = %s
                            """, (datetime.utcnow(), item['content_id']))
                        elif item['content_type'] == 'page':
                            cursor.execute("""
                                UPDATE pages SET is_published = TRUE, published_at = %s
                                WHERE id = %s
                            """, (datetime.utcnow(), item['content_id']))

                    success_count += 1

                except Exception as e:
                    logger.error(f"Error processing queue item {queue_id}: {e}")
                    continue

            conn.commit()
            cursor.close()
            conn.close()

            # Log activity
            log_user_activity(session['user_id'], f'bulk_{action}_content', 'moderation', None,
                            {'count': success_count})

            flash(f'Bulk action completed: {success_count} items {action}ed', 'success')
            return redirect(url_for('admin.moderation_queue'))

    except Exception as e:
        flash('Error performing bulk action', 'danger')
        logger.error(f"Error in bulk moderation: {e}")
        return redirect(url_for('admin.moderation_queue'))

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

@bp.route('/settings', methods=['GET', 'POST'])
@login_required
@role_required(['Admin'])
def organization_settings():
    """Organization settings page for Admin users

    Allows Admin users to:
    - View their organization details
    - Select and apply themes to their organization
    - Edit Contact Us and About Us pages
    """
    group_id = session.get('group_id')

    if not group_id:
        flash('You must be assigned to an organization to access settings.', 'danger')
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()

                # Get form data
                theme_id = request.form.get('theme_id')
                contact_page_content = request.form.get('contact_page_content')
                about_page_content = request.form.get('about_page_content')

                # Convert theme_id to int or None
                if theme_id and theme_id != '' and theme_id != '0':
                    try:
                        theme_id = int(theme_id)
                    except ValueError:
                        theme_id = None
                else:
                    theme_id = None

                # Update organization settings
                cursor.execute("""
                    UPDATE groups
                    SET theme_id = %s,
                        contact_page_content = %s,
                        about_page_content = %s,
                        updated_at = %s
                    WHERE id = %s
                """, (theme_id, contact_page_content, about_page_content,
                      datetime.utcnow(), group_id))

                conn.commit()
                cursor.close()
                conn.close()

                # Log activity
                log_user_activity(session['user_id'], 'update_organization_settings', 'group', group_id)

                flash('Organization settings updated successfully!', 'success')
                return redirect(url_for('admin.organization_settings'))

        except Exception as e:
            flash(f'Error updating settings: {str(e)}', 'danger')
            logger.error(f"Error updating organization settings: {e}")

    # GET request - show settings form
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Get organization details
            cursor.execute("""
                SELECT g.*, t.name as theme_name, u.username as admin_username, u.email as admin_email
                FROM groups g
                LEFT JOIN themes t ON g.theme_id = t.id
                LEFT JOIN users u ON g.admin_user_id = u.id
                WHERE g.id = %s
            """, (group_id,))
            organization = cursor.fetchone()

            if not organization:
                flash('Organization not found.', 'danger')
                cursor.close()
                conn.close()
                return redirect(url_for('admin.dashboard'))

            # Get themes available for this organization
            cursor.execute("""
                SELECT id, name, description, theme_type, created_at
                FROM themes
                WHERE group_id = %s AND is_active = TRUE
                ORDER BY name
            """, (group_id,))
            themes = cursor.fetchall()

            # Get organization statistics
            cursor.execute("""
                SELECT
                    (SELECT COUNT(*) FROM users WHERE group_id = %s) as total_users,
                    (SELECT COUNT(*) FROM blog_posts WHERE group_id = %s) as total_posts,
                    (SELECT COUNT(*) FROM pages WHERE group_id = %s) as total_pages
            """, (group_id, group_id, group_id))
            stats = cursor.fetchone()

            cursor.close()
            conn.close()

            return render_template('admin/settings.html',
                                 organization=organization,
                                 themes=themes,
                                 stats=stats)
        else:
            flash('Database connection error', 'danger')
            return redirect(url_for('admin.dashboard'))

    except Exception as e:
        flash('Error loading settings', 'danger')
        logger.error(f"Error loading organization settings: {e}")
        return redirect(url_for('admin.dashboard'))


# ============== ANALYTICS ROUTES ==============

@bp.route('/analytics')
@login_required
@role_required(['SuperAdmin', 'Admin'])
def analytics():
    """Analytics dashboard with detailed metrics"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            user_role = session['user_role']
            group_id = session.get('group_id')

            # ===== OVERVIEW STATS =====
            if user_role == 'SuperAdmin':
                cursor.execute("""
                    SELECT
                        (SELECT COUNT(*) FROM users WHERE is_active = TRUE) as total_users,
                        (SELECT COUNT(*) FROM groups WHERE is_active = TRUE) as total_groups,
                        (SELECT COUNT(*) FROM blog_posts WHERE is_published = TRUE) as total_blog_posts,
                        (SELECT COUNT(*) FROM pages WHERE is_published = TRUE) as total_pages,
                        (SELECT COUNT(*) FROM comments WHERE is_deleted = FALSE) as total_comments,
                        (SELECT COALESCE(SUM(view_count), 0) FROM blog_posts) as total_blog_views,
                        (SELECT COALESCE(SUM(view_count), 0) FROM pages) as total_page_views
                """)
            else:
                cursor.execute("""
                    SELECT
                        (SELECT COUNT(*) FROM users WHERE group_id = %s AND is_active = TRUE) as total_users,
                        (SELECT COUNT(*) FROM blog_posts WHERE group_id = %s AND is_published = TRUE) as total_blog_posts,
                        (SELECT COUNT(*) FROM pages WHERE group_id = %s AND is_published = TRUE) as total_pages,
                        (SELECT COUNT(*) FROM comments c
                         JOIN blog_posts bp ON c.blog_post_id = bp.id
                         WHERE bp.group_id = %s AND c.is_deleted = FALSE) as total_comments,
                        (SELECT COALESCE(SUM(view_count), 0) FROM blog_posts WHERE group_id = %s) as total_blog_views,
                        (SELECT COALESCE(SUM(view_count), 0) FROM pages WHERE group_id = %s) as total_page_views
                """, (group_id, group_id, group_id, group_id, group_id, group_id))

            overview_stats = cursor.fetchone()

            # ===== POPULAR BLOG POSTS (Top 10) =====
            if user_role == 'SuperAdmin':
                cursor.execute("""
                    SELECT bp.id, bp.title, bp.slug, bp.view_count, bp.created_at,
                           u.username as author_username, u.first_name, u.last_name,
                           g.name as group_name,
                           (SELECT COUNT(*) FROM comments WHERE blog_post_id = bp.id AND is_deleted = FALSE) as comment_count
                    FROM blog_posts bp
                    JOIN users u ON bp.author_id = u.id
                    LEFT JOIN groups g ON bp.group_id = g.id
                    WHERE bp.is_published = TRUE
                    ORDER BY bp.view_count DESC
                    LIMIT 10
                """)
            else:
                cursor.execute("""
                    SELECT bp.id, bp.title, bp.slug, bp.view_count, bp.created_at,
                           u.username as author_username, u.first_name, u.last_name,
                           (SELECT COUNT(*) FROM comments WHERE blog_post_id = bp.id AND is_deleted = FALSE) as comment_count
                    FROM blog_posts bp
                    JOIN users u ON bp.author_id = u.id
                    WHERE bp.group_id = %s AND bp.is_published = TRUE
                    ORDER BY bp.view_count DESC
                    LIMIT 10
                """, (group_id,))

            popular_posts = cursor.fetchall()

            # ===== POPULAR PAGES (Top 10) =====
            if user_role == 'SuperAdmin':
                cursor.execute("""
                    SELECT p.id, p.title, p.slug, p.view_count, p.created_at,
                           u.username as author_username, u.first_name, u.last_name,
                           g.name as group_name
                    FROM pages p
                    JOIN users u ON p.author_id = u.id
                    LEFT JOIN groups g ON p.group_id = g.id
                    WHERE p.is_published = TRUE
                    ORDER BY p.view_count DESC
                    LIMIT 10
                """)
            else:
                cursor.execute("""
                    SELECT p.id, p.title, p.slug, p.view_count, p.created_at,
                           u.username as author_username, u.first_name, u.last_name
                    FROM pages p
                    JOIN users u ON p.author_id = u.id
                    WHERE p.group_id = %s AND p.is_published = TRUE
                    ORDER BY p.view_count DESC
                    LIMIT 10
                """, (group_id,))

            popular_pages = cursor.fetchall()

            # ===== RECENT ACTIVITY (Last 30 days) =====
            if user_role == 'SuperAdmin':
                cursor.execute("""
                    SELECT
                        DATE(created_at) as date,
                        COUNT(*) FILTER (WHERE action = 'create_blog_post') as new_posts,
                        COUNT(*) FILTER (WHERE action = 'create_page') as new_pages,
                        COUNT(*) FILTER (WHERE action = 'register') as new_users
                    FROM user_activity_logs
                    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                    LIMIT 30
                """)
            else:
                cursor.execute("""
                    SELECT
                        DATE(ual.created_at) as date,
                        COUNT(*) FILTER (WHERE ual.action = 'create_blog_post') as new_posts,
                        COUNT(*) FILTER (WHERE ual.action = 'create_page') as new_pages,
                        COUNT(*) FILTER (WHERE ual.action = 'register') as new_users
                    FROM user_activity_logs ual
                    JOIN users u ON ual.user_id = u.id
                    WHERE u.group_id = %s AND ual.created_at >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY DATE(ual.created_at)
                    ORDER BY date DESC
                    LIMIT 30
                """, (group_id,))

            activity_timeline = cursor.fetchall()

            # ===== USER ENGAGEMENT =====
            if user_role == 'SuperAdmin':
                cursor.execute("""
                    SELECT u.id, u.username, u.first_name, u.last_name,
                           (SELECT COUNT(*) FROM blog_posts WHERE author_id = u.id) as post_count,
                           (SELECT COUNT(*) FROM comments WHERE user_id = u.id AND is_deleted = FALSE) as comment_count,
                           (SELECT COALESCE(SUM(view_count), 0) FROM blog_posts WHERE author_id = u.id) as total_views
                    FROM users u
                    WHERE u.is_active = TRUE
                    ORDER BY total_views DESC
                    LIMIT 10
                """)
            else:
                cursor.execute("""
                    SELECT u.id, u.username, u.first_name, u.last_name,
                           (SELECT COUNT(*) FROM blog_posts WHERE author_id = u.id) as post_count,
                           (SELECT COUNT(*) FROM comments WHERE user_id = u.id AND is_deleted = FALSE) as comment_count,
                           (SELECT COALESCE(SUM(view_count), 0) FROM blog_posts WHERE author_id = u.id) as total_views
                    FROM users u
                    WHERE u.group_id = %s AND u.is_active = TRUE
                    ORDER BY total_views DESC
                    LIMIT 10
                """, (group_id,))

            top_contributors = cursor.fetchall()

            # ===== CONTENT PERFORMANCE BY TAG =====
            if user_role == 'SuperAdmin':
                cursor.execute("""
                    SELECT
                        unnest(tags) as tag,
                        COUNT(*) as post_count,
                        AVG(view_count) as avg_views
                    FROM blog_posts
                    WHERE is_published = TRUE AND tags IS NOT NULL AND array_length(tags, 1) > 0
                    GROUP BY tag
                    ORDER BY post_count DESC
                    LIMIT 15
                """)
            else:
                cursor.execute("""
                    SELECT
                        unnest(tags) as tag,
                        COUNT(*) as post_count,
                        AVG(view_count) as avg_views
                    FROM blog_posts
                    WHERE group_id = %s AND is_published = TRUE AND tags IS NOT NULL AND array_length(tags, 1) > 0
                    GROUP BY tag
                    ORDER BY post_count DESC
                    LIMIT 15
                """, (group_id,))

            tag_stats = cursor.fetchall()

            # ===== COMMENT ENGAGEMENT =====
            if user_role == 'SuperAdmin':
                cursor.execute("""
                    SELECT bp.id, bp.title, bp.slug,
                           COUNT(c.id) as comment_count,
                           bp.view_count,
                           u.username as author_username
                    FROM blog_posts bp
                    JOIN users u ON bp.author_id = u.id
                    LEFT JOIN comments c ON bp.id = c.blog_post_id AND c.is_deleted = FALSE
                    WHERE bp.is_published = TRUE
                    GROUP BY bp.id, bp.title, bp.slug, bp.view_count, u.username
                    ORDER BY comment_count DESC
                    LIMIT 10
                """)
            else:
                cursor.execute("""
                    SELECT bp.id, bp.title, bp.slug,
                           COUNT(c.id) as comment_count,
                           bp.view_count,
                           u.username as author_username
                    FROM blog_posts bp
                    JOIN users u ON bp.author_id = u.id
                    LEFT JOIN comments c ON bp.id = c.blog_post_id AND c.is_deleted = FALSE
                    WHERE bp.group_id = %s AND bp.is_published = TRUE
                    GROUP BY bp.id, bp.title, bp.slug, bp.view_count, u.username
                    ORDER BY comment_count DESC
                    LIMIT 10
                """, (group_id,))

            most_commented = cursor.fetchall()

            cursor.close()
            conn.close()

            return render_template('admin/analytics.html',
                                 overview_stats=overview_stats,
                                 popular_posts=popular_posts,
                                 popular_pages=popular_pages,
                                 activity_timeline=activity_timeline,
                                 top_contributors=top_contributors,
                                 tag_stats=tag_stats,
                                 most_commented=most_commented,
                                 user_role=user_role)
        else:
            flash('Database connection error', 'danger')
            return render_template('admin/analytics.html')

    except Exception as e:
        flash('Error loading analytics', 'danger')
        logger.error(f"Error loading analytics: {e}")
        return render_template('admin/analytics.html')


# ============== COMMENT MODERATION ROUTES ==============

@bp.route('/comments')
@login_required
@role_required(['SuperAdmin', 'Admin'])
def manage_comments():
    """View and manage comments"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            user_role = session['user_role']
            group_id = session.get('group_id')

            # Build query based on role
            if user_role == 'SuperAdmin':
                cursor.execute("""
                    SELECT c.*, u.username, u.first_name, u.last_name,
                           bp.title as post_title, bp.slug as post_slug,
                           g.name as group_name
                    FROM comments c
                    JOIN users u ON c.user_id = u.id
                    JOIN blog_posts bp ON c.blog_post_id = bp.id
                    LEFT JOIN groups g ON bp.group_id = g.id
                    WHERE c.is_deleted = FALSE
                    ORDER BY c.created_at DESC
                    LIMIT 100
                """)
            else:
                cursor.execute("""
                    SELECT c.*, u.username, u.first_name, u.last_name,
                           bp.title as post_title, bp.slug as post_slug,
                           g.name as group_name
                    FROM comments c
                    JOIN users u ON c.user_id = u.id
                    JOIN blog_posts bp ON c.blog_post_id = bp.id
                    LEFT JOIN groups g ON bp.group_id = g.id
                    WHERE c.is_deleted = FALSE AND bp.group_id = %s
                    ORDER BY c.created_at DESC
                    LIMIT 100
                """, (group_id,))

            comments = cursor.fetchall()

            # Get stats
            if user_role == 'SuperAdmin':
                cursor.execute("""
                    SELECT
                        COUNT(*) FILTER (WHERE is_deleted = FALSE) as total_comments,
                        COUNT(*) FILTER (WHERE is_approved = FALSE AND is_deleted = FALSE) as pending_comments,
                        COUNT(*) FILTER (WHERE is_deleted = TRUE) as deleted_comments
                    FROM comments
                """)
            else:
                cursor.execute("""
                    SELECT
                        COUNT(*) FILTER (WHERE c.is_deleted = FALSE) as total_comments,
                        COUNT(*) FILTER (WHERE c.is_approved = FALSE AND c.is_deleted = FALSE) as pending_comments,
                        COUNT(*) FILTER (WHERE c.is_deleted = TRUE) as deleted_comments
                    FROM comments c
                    JOIN blog_posts bp ON c.blog_post_id = bp.id
                    WHERE bp.group_id = %s
                """, (group_id,))

            stats = cursor.fetchone()

            cursor.close()
            conn.close()

            return render_template('admin/comments.html', comments=comments, stats=stats)
        else:
            flash('Database connection error', 'danger')
            return render_template('admin/comments.html', comments=[], stats={})

    except Exception as e:
        flash('Error loading comments', 'danger')
        logger.error(f"Error loading comments: {e}")
        return render_template('admin/comments.html', comments=[], stats={})


@bp.route('/comments/<int:comment_id>/approve', methods=['POST'])
@login_required
@role_required(['SuperAdmin', 'Admin'])
def approve_comment(comment_id):
    """Approve a comment"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Verify permission
            cursor.execute("""
                SELECT c.*, bp.group_id FROM comments c
                JOIN blog_posts bp ON c.blog_post_id = bp.id
                WHERE c.id = %s
            """, (comment_id,))
            comment = cursor.fetchone()

            if not comment:
                flash('Comment not found', 'danger')
                cursor.close()
                conn.close()
                return redirect(url_for('admin.manage_comments'))

            # Check group permission for Admin
            if session['user_role'] == 'Admin' and comment['group_id'] != session.get('group_id'):
                flash('You do not have permission to moderate this comment', 'danger')
                cursor.close()
                conn.close()
                return redirect(url_for('admin.manage_comments'))

            cursor.execute("""
                UPDATE comments SET is_approved = TRUE, updated_at = %s
                WHERE id = %s
            """, (datetime.utcnow(), comment_id))
            conn.commit()

            log_user_activity(session['user_id'], 'approve_comment', 'comment', comment_id)

            cursor.close()
            conn.close()

            flash('Comment approved successfully', 'success')
            return redirect(url_for('admin.manage_comments'))
        else:
            flash('Database connection error', 'danger')
            return redirect(url_for('admin.manage_comments'))

    except Exception as e:
        flash('Error approving comment', 'danger')
        logger.error(f"Error approving comment: {e}")
        return redirect(url_for('admin.manage_comments'))


@bp.route('/comments/<int:comment_id>/unapprove', methods=['POST'])
@login_required
@role_required(['SuperAdmin', 'Admin'])
def unapprove_comment(comment_id):
    """Unapprove/hide a comment"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Verify permission
            cursor.execute("""
                SELECT c.*, bp.group_id FROM comments c
                JOIN blog_posts bp ON c.blog_post_id = bp.id
                WHERE c.id = %s
            """, (comment_id,))
            comment = cursor.fetchone()

            if not comment:
                flash('Comment not found', 'danger')
                cursor.close()
                conn.close()
                return redirect(url_for('admin.manage_comments'))

            # Check group permission for Admin
            if session['user_role'] == 'Admin' and comment['group_id'] != session.get('group_id'):
                flash('You do not have permission to moderate this comment', 'danger')
                cursor.close()
                conn.close()
                return redirect(url_for('admin.manage_comments'))

            cursor.execute("""
                UPDATE comments SET is_approved = FALSE, updated_at = %s
                WHERE id = %s
            """, (datetime.utcnow(), comment_id))
            conn.commit()

            log_user_activity(session['user_id'], 'unapprove_comment', 'comment', comment_id)

            cursor.close()
            conn.close()

            flash('Comment hidden successfully', 'success')
            return redirect(url_for('admin.manage_comments'))
        else:
            flash('Database connection error', 'danger')
            return redirect(url_for('admin.manage_comments'))

    except Exception as e:
        flash('Error hiding comment', 'danger')
        logger.error(f"Error hiding comment: {e}")
        return redirect(url_for('admin.manage_comments'))


@bp.route('/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
@role_required(['SuperAdmin', 'Admin'])
def admin_delete_comment(comment_id):
    """Delete a comment (soft delete)"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Verify permission
            cursor.execute("""
                SELECT c.*, bp.group_id FROM comments c
                JOIN blog_posts bp ON c.blog_post_id = bp.id
                WHERE c.id = %s
            """, (comment_id,))
            comment = cursor.fetchone()

            if not comment:
                flash('Comment not found', 'danger')
                cursor.close()
                conn.close()
                return redirect(url_for('admin.manage_comments'))

            # Check group permission for Admin
            if session['user_role'] == 'Admin' and comment['group_id'] != session.get('group_id'):
                flash('You do not have permission to delete this comment', 'danger')
                cursor.close()
                conn.close()
                return redirect(url_for('admin.manage_comments'))

            cursor.execute("""
                UPDATE comments SET is_deleted = TRUE, updated_at = %s
                WHERE id = %s
            """, (datetime.utcnow(), comment_id))
            conn.commit()

            log_user_activity(session['user_id'], 'admin_delete_comment', 'comment', comment_id)

            cursor.close()
            conn.close()

            flash('Comment deleted successfully', 'success')
            return redirect(url_for('admin.manage_comments'))
        else:
            flash('Database connection error', 'danger')
            return redirect(url_for('admin.manage_comments'))

    except Exception as e:
        flash('Error deleting comment', 'danger')
        logger.error(f"Error deleting comment: {e}")
        return redirect(url_for('admin.manage_comments'))