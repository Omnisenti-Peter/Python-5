"""
Theme routes for Opinian platform
Handles theme creation, editing, and management
"""

import os
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from app import get_db_connection, login_required, role_required, log_user_activity

bp = Blueprint('themes', __name__, url_prefix='/themes')

@bp.route('/')
@login_required
@role_required(['SuperAdmin', 'Admin', 'SuperUser'])
def index():
    """Theme management page"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            user_role = session['user_role']
            group_id = session.get('group_id')
            
            if user_role == 'SuperAdmin':
                # SuperAdmin sees all themes
                cursor.execute("""
                    SELECT t.*, u.username as creator_name, g.name as group_name
                    FROM themes t
                    LEFT JOIN users u ON t.created_by = u.id
                    LEFT JOIN groups g ON t.group_id = g.id
                    ORDER BY t.created_at DESC
                """)
            else:
                # Others see themes for their group
                cursor.execute("""
                    SELECT t.*, u.username as creator_name, g.name as group_name
                    FROM themes t
                    LEFT JOIN users u ON t.created_by = u.id
                    JOIN groups g ON t.group_id = g.id
                    WHERE t.group_id = %s
                    ORDER BY t.created_at DESC
                """, (group_id,))
            
            themes = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return render_template('themes/index.html', themes=themes)
        else:
            flash('Database connection error', 'danger')
            return render_template('themes/index.html', themes=[])
            
    except Exception as e:
        flash('Error loading themes', 'danger')
        return render_template('themes/index.html', themes=[])

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required(['SuperAdmin', 'Admin'])
def create_theme():
    """Create a new theme"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        # Get theme configuration
        css_variables = {
            'primary_color': request.form.get('primary_color', '#1a1a1a'),
            'secondary_color': request.form.get('secondary_color', '#d4af37'),
            'accent_color': request.form.get('accent_color', '#8b4513'),
            'background_color': request.form.get('background_color', '#f5f5dc'),
            'text_color': request.form.get('text_color', '#2c2c2c'),
            'heading_font': request.form.get('heading_font', 'Playfair Display'),
            'body_font': request.form.get('body_font', 'Source Sans Pro'),
            'border_radius': request.form.get('border_radius', '8px'),
            'shadow_strength': request.form.get('shadow_strength', '0.3')
        }
        
        custom_css = request.form.get('custom_css', '')
        
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                
                # Insert theme
                cursor.execute("""
                    INSERT INTO themes 
                    (name, description, css_variables, custom_css, created_by, group_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    name, description, json.dumps(css_variables), custom_css,
                    session['user_id'], session.get('group_id')
                ))
                
                theme_id = cursor.fetchone()[0]
                conn.commit()
                cursor.close()
                conn.close()
                
                # Log activity
                log_user_activity(session['user_id'], 'create_theme', 'theme', theme_id)
                
                flash('Theme created successfully!', 'success')
                return redirect(url_for('themes.index'))
            else:
                flash('Database connection error', 'danger')
                
        except Exception as e:
            flash('Error creating theme', 'danger')
            logger.error(f"Error creating theme: {e}")
    
    return render_template('themes/create.html')

@bp.route('/ai-create', methods=['GET', 'POST'])
@login_required
@role_required(['SuperAdmin', 'Admin'])
def ai_create_theme():
    """Create theme using AI prompt"""
    if request.method == 'POST':
        prompt = request.form.get('prompt')
        name = request.form.get('name')
        description = request.form.get('description')
        
        try:
            # TODO: Integrate with actual AI service
            # For now, generate a mock theme based on prompt
            if 'noir' in prompt.lower() or 'dark' in prompt.lower():
                css_variables = {
                    'primary_color': '#1a1a1a',
                    'secondary_color': '#d4af37',
                    'accent_color': '#8b4513',
                    'background_color': '#2c2c2c',
                    'text_color': '#f5f5dc',
                    'heading_font': 'Playfair Display',
                    'body_font': 'Source Sans Pro',
                    'border_radius': '4px',
                    'shadow_strength': '0.5'
                }
                custom_css = """
                /* Noir theme styling */
                .noir-element {
                    filter: contrast(1.2) brightness(0.9);
                }
                """
            else:
                css_variables = {
                    'primary_color': '#8b4513',
                    'secondary_color': '#d4af37',
                    'accent_color': '#1a1a1a',
                    'background_color': '#f5f5dc',
                    'text_color': '#2c2c2c',
                    'heading_font': 'Playfair Display',
                    'body_font': 'Source Sans Pro',
                    'border_radius': '12px',
                    'shadow_strength': '0.2'
                }
                custom_css = """
                /* Flapper theme styling */
                .flapper-element {
                    filter: sepia(0.1) saturate(1.1);
                }
                """
            
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO themes 
                    (name, description, css_variables, custom_css, created_by, group_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    name, description, json.dumps(css_variables), custom_css,
                    session['user_id'], session.get('group_id')
                ))
                
                theme_id = cursor.fetchone()[0]
                conn.commit()
                cursor.close()
                conn.close()
                
                # Log activity
                log_user_activity(session['user_id'], 'ai_create_theme', 'theme', theme_id)
                
                flash('AI-generated theme created successfully!', 'success')
                return redirect(url_for('themes.index'))
            else:
                flash('Database connection error', 'danger')
                
        except Exception as e:
            flash('Error creating AI theme', 'danger')
            logger.error(f"Error creating AI theme: {e}")
    
    return render_template('themes/ai_create.html')

@bp.route('/edit/<int:theme_id>', methods=['GET', 'POST'])
@login_required
@role_required(['SuperAdmin', 'Admin'])
def edit_theme(theme_id):
    """Edit an existing theme"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get theme
            cursor.execute("SELECT * FROM themes WHERE id = %s", (theme_id,))
            theme = cursor.fetchone()
            
            if not theme:
                flash('Theme not found', 'danger')
                return redirect(url_for('themes.index'))
            
            # Check permissions
            if session['user_role'] == 'Admin' and theme['group_id'] != session.get('group_id'):
                flash('You cannot edit themes from other groups', 'danger')
                return redirect(url_for('themes.index'))
            
            if request.method == 'POST':
                name = request.form.get('name')
                description = request.form.get('description')
                
                css_variables = {
                    'primary_color': request.form.get('primary_color'),
                    'secondary_color': request.form.get('secondary_color'),
                    'accent_color': request.form.get('accent_color'),
                    'background_color': request.form.get('background_color'),
                    'text_color': request.form.get('text_color'),
                    'heading_font': request.form.get('heading_font'),
                    'body_font': request.form.get('body_font'),
                    'border_radius': request.form.get('border_radius'),
                    'shadow_strength': request.form.get('shadow_strength')
                }
                
                custom_css = request.form.get('custom_css')
                
                cursor.execute("""
                    UPDATE themes 
                    SET name = %s, description = %s, css_variables = %s, 
                        custom_css = %s, updated_at = %s
                    WHERE id = %s
                """, (
                    name, description, json.dumps(css_variables), custom_css,
                    datetime.utcnow(), theme_id
                ))
                
                conn.commit()
                cursor.close()
                conn.close()
                
                # Log activity
                log_user_activity(session['user_id'], 'edit_theme', 'theme', theme_id)
                
                flash('Theme updated successfully!', 'success')
                return redirect(url_for('themes.index'))
            
            cursor.close()
            conn.close()
            
            return render_template('themes/edit.html', theme=theme)
        else:
            flash('Database connection error', 'danger')
            return redirect(url_for('themes.index'))
            
    except Exception as e:
        flash('Error loading theme', 'danger')
        logger.error(f"Error editing theme: {e}")
        return redirect(url_for('themes.index'))

@bp.route('/visual-editor/<int:theme_id>')
@login_required
@role_required(['SuperAdmin', 'Admin'])
def visual_editor(theme_id):
    """Visual theme editor"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("SELECT * FROM themes WHERE id = %s", (theme_id,))
            theme = cursor.fetchone()
            
            if not theme:
                flash('Theme not found', 'danger')
                return redirect(url_for('themes.index'))
            
            # Check permissions
            if session['user_role'] == 'Admin' and theme['group_id'] != session.get('group_id'):
                flash('You cannot edit themes from other groups', 'danger')
                return redirect(url_for('themes.index'))
            
            cursor.close()
            conn.close()
            
            return render_template('themes/visual_editor.html', theme=theme)
        else:
            flash('Database connection error', 'danger')
            return redirect(url_for('themes.index'))
            
    except Exception as e:
        flash('Error loading visual editor', 'danger')
        logger.error(f"Error loading visual editor: {e}")
        return redirect(url_for('themes.index'))

@bp.route('/apply/<int:theme_id>', methods=['POST'])
@login_required
@role_required(['SuperAdmin', 'Admin'])
def apply_theme(theme_id):
    """Apply theme to group"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get theme
            cursor.execute("SELECT * FROM themes WHERE id = %s", (theme_id,))
            theme = cursor.fetchone()
            
            if not theme:
                return jsonify({'success': False, 'message': 'Theme not found'}), 404
            
            # Check permissions
            if session['user_role'] == 'Admin' and theme['group_id'] != session.get('group_id'):
                return jsonify({'success': False, 'message': 'Permission denied'}), 403
            
            # Apply theme to group
            group_id = theme['group_id']
            cursor.execute("UPDATE groups SET theme_id = %s WHERE id = %s", (theme_id, group_id))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            # Log activity
            log_user_activity(session['user_id'], 'apply_theme', 'theme', theme_id, {'group_id': group_id})
            
            return jsonify({
                'success': True, 
                'message': 'Theme applied successfully'
            })
            
    except Exception as e:
        logger.error(f"Error applying theme: {e}")
        return jsonify({'success': False, 'message': 'Error applying theme'}), 500

@bp.route('/preview/<int:theme_id>')
def preview_theme(theme_id):
    """Preview theme"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("SELECT * FROM themes WHERE id = %s", (theme_id,))
            theme = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if not theme:
                flash('Theme not found', 'danger')
                return redirect(url_for('themes.index'))
            
            return render_template('themes/preview.html', theme=theme)
        else:
            flash('Database connection error', 'danger')
            return redirect(url_for('themes.index'))
            
    except Exception as e:
        flash('Error loading theme preview', 'danger')
        logger.error(f"Error previewing theme: {e}")
        return redirect(url_for('themes.index'))

@bp.route('/delete/<int:theme_id>', methods=['POST'])
@login_required
@role_required(['SuperAdmin', 'Admin'])
def delete_theme(theme_id):
    """Delete a theme"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get theme
            cursor.execute("SELECT * FROM themes WHERE id = %s", (theme_id,))
            theme = cursor.fetchone()
            
            if not theme:
                return jsonify({'success': False, 'message': 'Theme not found'}), 404
            
            # Check permissions
            if session['user_role'] == 'Admin' and theme['group_id'] != session.get('group_id'):
                return jsonify({'success': False, 'message': 'Permission denied'}), 403
            
            # Delete theme
            cursor.execute("DELETE FROM themes WHERE id = %s", (theme_id,))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            # Log activity
            log_user_activity(session['user_id'], 'delete_theme', 'theme', theme_id)
            
            return jsonify({
                'success': True, 
                'message': 'Theme deleted successfully'
            })
            
    except Exception as e:
        logger.error(f"Error deleting theme: {e}")
        return jsonify({'success': False, 'message': 'Error deleting theme'}), 500