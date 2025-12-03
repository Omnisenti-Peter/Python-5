"""
Theme routes for Opinian platform
Handles theme creation, editing, and management
"""

import os
import json
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from app import get_db_connection, login_required, role_required, log_user_activity

logger = logging.getLogger(__name__)

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

                flash('Theme created! Now customize it in the Visual Builder.', 'success')
                return redirect(url_for('themes.visual_builder', theme_id=theme_id))
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

        try:
            # Import AI service
            from ai_service import ai_service

            # Generate theme using AI
            ai_result = ai_service.generate_theme_design(prompt)

            if ai_result.get('success'):
                theme_data = ai_result.get('theme')

                # Extract theme info
                name = theme_data.get('name', 'AI Generated Theme')
                description = theme_data.get('description', prompt[:200])
                css_variables = theme_data.get('css_variables', {})
                custom_css = theme_data.get('custom_css', '')
                design_notes = theme_data.get('design_notes', '')

                # Add design notes to custom CSS as a comment
                if design_notes:
                    custom_css = f"/* AI Design Notes:\n{design_notes}\n*/\n\n{custom_css}"

                # Add AI attribution to description
                if ai_result.get('is_fallback'):
                    flash(f'Theme created with keyword-based design. {ai_result.get("message", "")}', 'info')
                else:
                    flash(f'AI-generated theme created successfully! {design_notes[:100]}...', 'success')

                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()

                    cursor.execute("""
                        INSERT INTO themes
                        (name, description, css_variables, custom_css, created_by, group_id, theme_type)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        name, description, json.dumps(css_variables), custom_css,
                        session['user_id'], session.get('group_id'), 'ai_generated'
                    ))

                    theme_id = cursor.fetchone()[0]
                    conn.commit()
                    cursor.close()
                    conn.close()

                    # Log activity
                    log_user_activity(session['user_id'], 'ai_create_theme', 'theme', theme_id)

                    return redirect(url_for('themes.edit_theme', theme_id=theme_id))
                else:
                    flash('Database connection error', 'danger')
            else:
                error_msg = ai_result.get('message', 'AI generation failed')
                flash(f'AI theme generation error: {error_msg}', 'warning')
                logger.error(f"AI theme generation failed: {ai_result.get('error')}")

        except Exception as e:
            flash('Error creating AI theme. Please try again.', 'danger')
            logger.error(f"Error creating AI theme: {e}")
            import traceback
            logger.debug(traceback.format_exc())

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
                flash('Theme not found', 'danger')
                return redirect(url_for('themes.index'))

            # Check permissions
            if session['user_role'] == 'Admin' and theme['group_id'] != session.get('group_id'):
                flash('Permission denied - cannot apply themes from other groups', 'danger')
                return redirect(url_for('themes.index'))

            # Apply theme to group
            group_id = theme['group_id'] if theme['group_id'] else session.get('group_id')

            cursor.execute("UPDATE groups SET theme_id = %s, updated_at = %s WHERE id = %s",
                          (theme_id, datetime.utcnow(), group_id))
            conn.commit()

            cursor.close()
            conn.close()

            # Log activity
            log_user_activity(session['user_id'], 'apply_theme', 'theme', theme_id, {'group_id': group_id})

            flash(f'✅ Theme "{theme["name"]}" is now active! It will be used for all your organization\'s pages and blog posts.', 'success')
            return redirect(url_for('themes.index'))

    except Exception as e:
        logger.error(f"Error applying theme: {e}")
        flash('Error applying theme. Please try again.', 'danger')
        return redirect(url_for('themes.index'))

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

@bp.route('/visual-builder', methods=['GET'])
@bp.route('/visual-builder/<int:theme_id>', methods=['GET'])
@login_required
@role_required(['SuperAdmin', 'Admin'])
def visual_builder(theme_id=None):
    """Simple drag & drop theme builder"""
    theme = None

    if theme_id:
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

                # Permission check
                if session['user_role'] == 'Admin' and theme['group_id'] != session.get('group_id'):
                    flash('Permission denied', 'danger')
                    return redirect(url_for('themes.index'))
        except Exception as e:
            flash('Error loading theme', 'danger')
            return redirect(url_for('themes.index'))

    return render_template('themes/simple_builder.html', theme=theme)


@bp.route('/advanced-builder', methods=['GET'])
@bp.route('/advanced-builder/<int:theme_id>', methods=['GET'])
@login_required
@role_required(['SuperAdmin', 'Admin'])
def advanced_builder(theme_id=None):
    """Advanced GrapesJS theme builder (for developers)"""
    theme = None

    if theme_id:
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

                # Permission check
                if session['user_role'] == 'Admin' and theme['group_id'] != session.get('group_id'):
                    flash('Permission denied', 'danger')
                    return redirect(url_for('themes.index'))
        except Exception as e:
            flash('Error loading theme', 'danger')
            return redirect(url_for('themes.index'))

    return render_template('themes/visual_builder.html', theme=theme)


@bp.route('/visual-save', methods=['POST'])
@login_required
@role_required(['SuperAdmin', 'Admin'])
def visual_save():
    """Save theme from visual builder"""
    try:
        data = request.get_json()

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO themes
                (name, description, gjs_data, gjs_assets, html_export,
                 theme_type, created_by, group_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                data['name'],
                data.get('description', ''),
                json.dumps(data['gjs_data']),
                json.dumps(data.get('gjs_assets', [])),
                data.get('html_export', ''),
                data.get('theme_type', 'visual'),
                session['user_id'],
                session.get('group_id')
            ))

            theme_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()

            log_user_activity(session['user_id'], 'create_visual_theme', 'theme', theme_id)

            return jsonify({'success': True, 'theme_id': theme_id})
        else:
            return jsonify({'success': False, 'message': 'Database connection error'}), 500

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/update/<int:theme_id>', methods=['POST'])
@login_required
@role_required(['SuperAdmin', 'Admin'])
def update_theme(theme_id):
    """Update existing theme from visual builder"""
    try:
        data = request.get_json()

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()

            # Check permissions
            cursor.execute("SELECT group_id FROM themes WHERE id = %s", (theme_id,))
            theme_row = cursor.fetchone()

            if not theme_row:
                return jsonify({'success': False, 'message': 'Theme not found'}), 404

            if session['user_role'] == 'Admin' and theme_row[0] != session.get('group_id'):
                return jsonify({'success': False, 'message': 'Permission denied'}), 403

            cursor.execute("""
                UPDATE themes
                SET name = %s, description = %s, gjs_data = %s,
                    gjs_assets = %s, html_export = %s, updated_at = %s
                WHERE id = %s
            """, (
                data['name'],
                data.get('description', ''),
                json.dumps(data['gjs_data']),
                json.dumps(data.get('gjs_assets', [])),
                data.get('html_export', ''),
                datetime.utcnow(),
                theme_id
            ))

            conn.commit()
            cursor.close()
            conn.close()

            log_user_activity(session['user_id'], 'update_visual_theme', 'theme', theme_id)

            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Database connection error'}), 500

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/live-preview/<int:theme_id>')
def live_preview(theme_id):
    """Render theme in full-page preview"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM themes WHERE id = %s", (theme_id,))
            theme = cursor.fetchone()
            cursor.close()
            conn.close()

            if not theme:
                return "Theme not found", 404

            gjs_data = theme.get('gjs_data')
            if not gjs_data:
                return "Theme has no visual data", 400

            html = gjs_data.get('html', '')
            css = gjs_data.get('css', '')

            preview_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{theme['name']} - Preview</title>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Source+Sans+Pro:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        {css}
    </style>
</head>
<body>
    {html}
</body>
</html>"""

            return preview_html
        else:
            return "Database connection error", 500

    except Exception as e:
        return f"Error loading preview: {str(e)}", 500


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