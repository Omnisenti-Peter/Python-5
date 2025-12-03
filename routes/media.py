"""
Media routes for Opinian platform
Handles file uploads for theme builder and general media management
"""

import os
import uuid
from flask import Blueprint, request, jsonify, session, send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from app import get_db_connection, login_required, log_user_activity
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('media', __name__, url_prefix='/media')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'ico', 'bmp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size(file):
    """Get file size"""
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    return size

@bp.route('/upload', methods=['POST'])
@login_required
def upload_media():
    """Handle file uploads for theme builder and general media"""
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        file = request.files['file']

        # Check if filename is empty
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        # Validate file extension
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # Check file size
        file_size = get_file_size(file)
        if file_size > MAX_FILE_SIZE:
            return jsonify({
                'success': False,
                'error': f'File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024)}MB'
            }), 400

        # Generate unique filename
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"

        # Create upload directory if it doesn't exist
        upload_dir = os.path.join('static', 'uploads', 'themes')
        os.makedirs(upload_dir, exist_ok=True)

        # Save file
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)

        # Store in database
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO media_files
                (filename, original_filename, file_path, file_size, mime_type, uploaded_by, group_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                unique_filename,
                original_filename,
                file_path,
                file_size,
                file.content_type,
                session['user_id'],
                session.get('group_id')
            ))

            media_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()

            # Log activity
            log_user_activity(session['user_id'], 'upload_media', 'media_file', media_id, {
                'filename': original_filename,
                'size': file_size
            })

            # Return success with file URL
            file_url = f'/static/uploads/themes/{unique_filename}'
            return jsonify({
                'success': True,
                'url': file_url,
                'id': media_id,
                'filename': original_filename,
                'size': file_size
            })
        else:
            # Clean up file if database insert fails
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'success': False, 'error': 'Database connection error'}), 500

    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return jsonify({'success': False, 'error': 'Error uploading file'}), 500


@bp.route('/list', methods=['GET'])
@login_required
def list_media():
    """List media files for current user's group"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Get media files for user's group
            group_id = session.get('group_id')
            user_role = session.get('user_role')

            if user_role == 'SuperAdmin':
                # SuperAdmin sees all media
                cursor.execute("""
                    SELECT m.*, u.username as uploaded_by_name
                    FROM media_files m
                    LEFT JOIN users u ON m.uploaded_by = u.id
                    ORDER BY m.created_at DESC
                """)
            else:
                # Others see only their group's media
                cursor.execute("""
                    SELECT m.*, u.username as uploaded_by_name
                    FROM media_files m
                    LEFT JOIN users u ON m.uploaded_by = u.id
                    WHERE m.group_id = %s
                    ORDER BY m.created_at DESC
                """, (group_id,))

            media_files = cursor.fetchall()

            # Format for GrapesJS asset manager
            assets = []
            for media in media_files:
                assets.append({
                    'id': media['id'],
                    'src': f"/static/uploads/themes/{media['filename']}",
                    'name': media['original_filename'],
                    'size': media['file_size'],
                    'type': media['mime_type'],
                    'uploaded_at': media['created_at'].isoformat() if media['created_at'] else None
                })

            cursor.close()
            conn.close()

            return jsonify({
                'success': True,
                'assets': assets
            })
        else:
            return jsonify({'success': False, 'error': 'Database connection error'}), 500

    except Exception as e:
        logger.error(f"Error listing media: {e}")
        return jsonify({'success': False, 'error': 'Error listing media'}), 500


@bp.route('/delete/<int:media_id>', methods=['DELETE'])
@login_required
def delete_media(media_id):
    """Delete a media file"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Get media file details
            cursor.execute("SELECT * FROM media_files WHERE id = %s", (media_id,))
            media = cursor.fetchone()

            if not media:
                return jsonify({'success': False, 'error': 'Media file not found'}), 404

            # Check permissions
            user_role = session.get('user_role')
            group_id = session.get('group_id')

            if user_role != 'SuperAdmin' and media['group_id'] != group_id:
                return jsonify({'success': False, 'error': 'Permission denied'}), 403

            # Delete file from filesystem
            file_path = media['file_path']
            if os.path.exists(file_path):
                os.remove(file_path)

            # Delete from database
            cursor.execute("DELETE FROM media_files WHERE id = %s", (media_id,))
            conn.commit()
            cursor.close()
            conn.close()

            # Log activity
            log_user_activity(session['user_id'], 'delete_media', 'media_file', media_id, {
                'filename': media['original_filename']
            })

            return jsonify({
                'success': True,
                'message': 'Media file deleted successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Database connection error'}), 500

    except Exception as e:
        logger.error(f"Error deleting media: {e}")
        return jsonify({'success': False, 'error': 'Error deleting media'}), 500
