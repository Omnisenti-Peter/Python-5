"""
Page routes for Opinian platform
Handles static page creation and management
"""

import os
import re
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from app import get_db_connection, login_required, role_required, allowed_file, log_user_activity

logger = logging.getLogger(__name__)

bp = Blueprint('pages', __name__, url_prefix='/pages')

@bp.route('/<slug>')
def view_page(slug):
    """View a static page"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT p.*, u.username, u.first_name, u.last_name, u.bio,
                       g.name as group_name,
                       th.css_variables, th.custom_css,
                       tpl.name as template_name, tpl.html_content, tpl.css_content, tpl.js_content
                FROM pages p
                JOIN users u ON p.author_id = u.id
                LEFT JOIN groups g ON p.group_id = g.id
                LEFT JOIN themes th ON g.theme_id = th.id
                LEFT JOIN templates tpl ON p.template_id = tpl.id
                WHERE p.slug = %s AND p.is_published = TRUE
            """, (slug,))
            
            page = cursor.fetchone()

            if not page:
                flash('Page not found', 'danger')
                cursor.close()
                conn.close()
                return redirect(url_for('index'))

            # Increment view count
            cursor.execute("UPDATE pages SET view_count = view_count + 1 WHERE id = %s", (page['id'],))
            conn.commit()

            # Process template if one is assigned
            rendered_content = page['content']
            if page.get('html_content'):
                # Apply template HTML with variable substitution
                template_html = page['html_content']
                template_html = template_html.replace('{{content}}', page['content'] or '')
                template_html = template_html.replace('{{title}}', page['title'] or '')
                rendered_content = template_html

            cursor.close()
            conn.close()

            return render_template('pages/view.html', page=page, rendered_content=rendered_content)
        else:
            flash('Database connection error', 'danger')
            return redirect(url_for('index'))
            
    except Exception as e:
        flash('Error loading page', 'danger')
        return redirect(url_for('index'))

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required(['SuperAdmin', 'Admin', 'SuperUser'])
def create_page():
    """Create a new page"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        meta_description = request.form.get('meta_description')
        meta_keywords = request.form.get('meta_keywords')
        is_published = request.form.get('is_published') == 'on'
        template_id = request.form.get('template_id') or None
        
        # Generate slug from title
        slug = re.sub(r'[^a-zA-Z0-9-]+', '-', title.lower()).strip('-')
        
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                
                # Ensure unique slug
                cursor.execute("SELECT id FROM pages WHERE slug = %s", (slug,))
                if cursor.fetchone():
                    slug = f"{slug}-{int(datetime.now().timestamp())}"
                
                # Insert page
                cursor.execute("""
                    INSERT INTO pages 
                    (title, slug, content, author_id, group_id, template_id, 
                     meta_description, meta_keywords, is_published, published_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    title, slug, content, session['user_id'], session.get('group_id'),
                    template_id, meta_description, meta_keywords,
                    is_published, datetime.utcnow() if is_published else None
                ))
                
                page_id = cursor.fetchone()[0]
                conn.commit()
                cursor.close()
                conn.close()
                
                # Log activity
                log_user_activity(session['user_id'], 'create_page', 'page', page_id)
                
                flash('Page created successfully!', 'success')
                if is_published:
                    return redirect(url_for('pages.view_page', slug=slug))
                else:
                    return redirect(url_for('pages.my_pages'))
            else:
                flash('Database connection error', 'danger')
                
        except Exception as e:
            flash('Error creating page', 'danger')
            logger.error(f"Error creating page: {e}")
    
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get available templates
            cursor.execute("SELECT id, name FROM templates WHERE group_id = %s OR is_default = TRUE", 
                         (session.get('group_id'),))
            templates = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return render_template('pages/create.html', templates=templates)
        else:
            flash('Database connection error', 'danger')
            return render_template('pages/create.html', templates=[])
            
    except Exception as e:
        flash('Error loading templates', 'danger')
        return render_template('pages/create.html', templates=[])

@bp.route('/edit/<int:page_id>', methods=['GET', 'POST'])
@login_required
@role_required(['SuperAdmin', 'Admin', 'SuperUser'])
def edit_page(page_id):
    """Edit an existing page"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get page
            cursor.execute("SELECT * FROM pages WHERE id = %s", (page_id,))
            page = cursor.fetchone()
            
            if not page:
                flash('Page not found', 'danger')
                return redirect(url_for('pages.my_pages'))
            
            # Check permissions
            if session['user_role'] not in ['SuperAdmin', 'Admin'] and page['author_id'] != session['user_id']:
                flash('You do not have permission to edit this page', 'danger')
                return redirect(url_for('pages.my_pages'))
            
            if request.method == 'POST':
                title = request.form.get('title')
                content = request.form.get('content')
                meta_description = request.form.get('meta_description')
                meta_keywords = request.form.get('meta_keywords')
                is_published = request.form.get('is_published') == 'on'
                template_id = request.form.get('template_id') or None
                
                # Update slug if title changed
                slug = re.sub(r'[^a-zA-Z0-9-]+', '-', title.lower()).strip('-')
                if slug != page['slug']:
                    cursor.execute("SELECT id FROM pages WHERE slug = %s AND id != %s", (slug, page_id))
                    if cursor.fetchone():
                        slug = f"{slug}-{int(datetime.now().timestamp())}"
                
                # Update page
                cursor.execute("""
                    UPDATE pages 
                    SET title = %s, slug = %s, content = %s, template_id = %s,
                        meta_description = %s, meta_keywords = %s, is_published = %s,
                        published_at = %s, updated_at = %s
                    WHERE id = %s
                """, (
                    title, slug, content, template_id, meta_description, meta_keywords,
                    is_published,
                    datetime.utcnow() if is_published and not page['published_at'] else page['published_at'],
                    datetime.utcnow(), page_id
                ))
                
                conn.commit()
                cursor.close()
                conn.close()
                
                # Log activity
                log_user_activity(session['user_id'], 'edit_page', 'page', page_id)
                
                flash('Page updated successfully!', 'success')
                if is_published:
                    return redirect(url_for('pages.view_page', slug=slug))
                else:
                    return redirect(url_for('pages.my_pages'))
            
            # Get available templates
            cursor.execute("SELECT id, name FROM templates WHERE group_id = %s OR is_default = TRUE", 
                         (session.get('group_id'),))
            templates = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return render_template('pages/edit.html', page=page, templates=templates)
        else:
            flash('Database connection error', 'danger')
            return redirect(url_for('pages.my_pages'))
            
    except Exception as e:
        flash('Error loading page', 'danger')
        logger.error(f"Error editing page: {e}")
        return redirect(url_for('pages.my_pages'))

@bp.route('/delete/<int:page_id>', methods=['POST'])
@login_required
@role_required(['SuperAdmin', 'Admin', 'SuperUser'])
def delete_page(page_id):
    """Delete a page"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get page
            cursor.execute("SELECT * FROM pages WHERE id = %s", (page_id,))
            page = cursor.fetchone()
            
            if not page:
                flash('Page not found', 'danger')
                return redirect(url_for('pages.my_pages'))
            
            # Check permissions
            if session['user_role'] not in ['SuperAdmin', 'Admin'] and page['author_id'] != session['user_id']:
                flash('You do not have permission to delete this page', 'danger')
                return redirect(url_for('pages.my_pages'))
            
            # Delete page
            cursor.execute("DELETE FROM pages WHERE id = %s", (page_id,))
            conn.commit()
            cursor.close()
            conn.close()
            
            # Log activity
            log_user_activity(session['user_id'], 'delete_page', 'page', page_id)
            
            flash('Page deleted successfully!', 'success')
            return redirect(url_for('pages.my_pages'))
        else:
            flash('Database connection error', 'danger')
            return redirect(url_for('pages.my_pages'))
            
    except Exception as e:
        flash('Error deleting page', 'danger')
        logger.error(f"Error deleting page: {e}")
        return redirect(url_for('pages.my_pages'))

@bp.route('/my-pages')
@login_required
def my_pages():
    """List user's pages"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            user_role = session['user_role']
            user_id = session['user_id']
            
            if user_role in ['SuperAdmin', 'Admin']:
                # Admins can see all pages in their group
                group_id = session.get('group_id')
                if group_id is not None:
                    cursor.execute("""
                        SELECT p.*, u.username
                        FROM pages p
                        JOIN users u ON p.author_id = u.id
                        WHERE p.group_id = %s
                        ORDER BY p.created_at DESC
                    """, (group_id,))
                else:
                    cursor.execute("""
                        SELECT p.*, u.username
                        FROM pages p
                        JOIN users u ON p.author_id = u.id
                        WHERE p.group_id IS NULL
                        ORDER BY p.created_at DESC
                    """)
            else:
                # Regular users can only see their own pages
                cursor.execute("""
                    SELECT * FROM pages 
                    WHERE author_id = %s
                    ORDER BY created_at DESC
                """, (user_id,))
            
            pages = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return render_template('pages/my_pages.html', pages=pages)
        else:
            flash('Database connection error', 'danger')
            return render_template('pages/my_pages.html', pages=[])
            
    except Exception as e:
        flash('Error loading pages', 'danger')
        logger.error(f"Error loading my pages: {e}")
        return render_template('pages/my_pages.html', pages=[])

@bp.route('/contact-us')
def contact_us():
    """Contact Us page (group-specific)"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get the default group or first active group
            cursor.execute("""
                SELECT g.contact_page_content, g.name as group_name, t.css_variables, t.custom_css
                FROM groups g
                LEFT JOIN themes t ON g.theme_id = t.id
                WHERE g.is_active = TRUE
                ORDER BY g.id
                LIMIT 1
            """)
            group = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if not group or not group['contact_page_content']:
                # Use default contact page
                return render_template('pages/contact_us.html')
            
            return render_template('pages/contact_us.html', 
                                 content=group['contact_page_content'],
                                 group_name=group['group_name'],
                                 theme=group)
        else:
            return render_template('pages/contact_us.html')
            
    except Exception as e:
        logger.error(f"Error loading contact page: {e}")
        return render_template('pages/contact_us.html')

@bp.route('/about-us')
def about_us():
    """About Us page (group-specific)"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get the default group or first active group
            cursor.execute("""
                SELECT g.about_page_content, g.name as group_name, t.css_variables, t.custom_css
                FROM groups g
                LEFT JOIN themes t ON g.theme_id = t.id
                WHERE g.is_active = TRUE
                ORDER BY g.id
                LIMIT 1
            """)
            group = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if not group or not group['about_page_content']:
                # Use default about page
                return render_template('pages/about_us.html')
            
            return render_template('pages/about_us.html', 
                                 content=group['about_page_content'],
                                 group_name=group['group_name'],
                                 theme=group)
        else:
            return render_template('pages/about_us.html')
            
    except Exception as e:
        logger.error(f"Error loading about page: {e}")
        return render_template('pages/about_us.html')

@bp.route('/profile/<username>')
def user_profile(username):
    """Public user profile page"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT u.*, r.name as role_name, g.name as group_name
                FROM users u
                JOIN roles r ON u.role_id = r.id
                LEFT JOIN groups g ON u.group_id = g.id
                WHERE u.username = %s AND u.is_active = TRUE
            """, (username,))
            user = cursor.fetchone()
            
            if not user:
                flash('User not found', 'danger')
                return redirect(url_for('index'))
            
            # Get user's published blog posts
            cursor.execute("""
                SELECT id, title, slug, published_at, excerpt, view_count,
                       featured_image_url, tags
                FROM blog_posts
                WHERE author_id = %s AND is_published = TRUE
                ORDER BY published_at DESC
                LIMIT 9
            """, (user['id'],))
            blog_posts = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return render_template('pages/profile.html', user=user, blog_posts=blog_posts)
        else:
            flash('Database connection error', 'danger')
            return redirect(url_for('index'))
            
    except Exception as e:
        flash(f'Error loading profile: {str(e)}', 'danger')
        logger.error(f"Error loading user profile for {username}: {e}", exc_info=True)
        return redirect(url_for('index'))