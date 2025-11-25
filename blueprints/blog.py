"""
Blog CRUD routes blueprint
"""
from datetime import datetime
import os
import hashlib
import re
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import BlogPost, MediaFile
from sqlalchemy import desc

blog_bp = Blueprint('blog', __name__)

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_slug(title):
    """Generate URL-friendly slug from title"""
    # Convert to lowercase and replace spaces with hyphens
    slug = title.lower().strip()
    # Remove special characters except hyphens
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    # Replace multiple spaces/hyphens with single hyphen
    slug = re.sub(r'[\s-]+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')

    # Ensure uniqueness
    original_slug = slug
    counter = 1
    while BlogPost.query.filter_by(slug=slug).first():
        slug = f"{original_slug}-{counter}"
        counter += 1

    return slug


@blog_bp.route('/blog/write', methods=['GET'])
@blog_bp.route('/editor', methods=['GET'])
@login_required
def editor():
    """Blog writing/editor page"""
    return render_template('editor.html')


@blog_bp.route('/blog/my-posts', methods=['GET'])
@blog_bp.route('/my-posts', methods=['GET'])
@login_required
def my_posts():
    """Show user's own posts (published and drafts)"""
    published_posts = BlogPost.query.filter_by(
        user_id=current_user.id,
        status='published'
    ).order_by(desc(BlogPost.created_at)).all()

    draft_posts = BlogPost.query.filter_by(
        user_id=current_user.id,
        status='draft'
    ).order_by(desc(BlogPost.updated_at)).all()

    # Calculate stats for the user's posts
    published_count = len(published_posts)
    draft_count = len(draft_posts)

    # Get total likes and comments for user's posts
    total_likes = sum(post.like_count for post in published_posts)
    total_comments = sum(post.comment_count for post in published_posts)

    return render_template('my_posts.html',
                         published_posts=published_posts,
                         draft_posts=draft_posts,
                         published_count=published_count,
                         draft_count=draft_count,
                         total_likes=total_likes,
                         total_comments=total_comments)


@blog_bp.route('/blog/create', methods=['POST'])
@login_required
def create_blog():
    """Create new blog post"""
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    is_published = request.form.get('publish', 'false') == 'true'
    ai_enhanced = request.form.get('ai_enhanced', 'false') == 'true'

    if not title or not content:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Title and content are required'}), 400
        flash('Please enter both title and content', 'error')
        return redirect(url_for('blog.editor'))

    # Generate slug from title
    slug = generate_slug(title)

    # Calculate word count and reading time
    word_count = len(content.split())
    reading_time = max(1, word_count // 200)  # Assume 200 words per minute

    new_post = BlogPost(
        user_id=current_user.id,
        title=title,
        slug=slug,
        content=content,
        word_count=word_count,
        reading_time=reading_time,
        status='published' if is_published else 'draft',
        ai_assisted=ai_enhanced,
        published_at=datetime.utcnow() if is_published else None
    )

    db.session.add(new_post)
    db.session.commit()

    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Blog post published successfully!' if is_published else 'Draft saved successfully!',
            'post_id': new_post.id
        })

    if is_published:
        flash('Blog post published successfully! You can see it on the homepage.', 'success')
        return redirect(url_for('main.view_post', slug=new_post.slug))
    else:
        flash('Draft saved successfully! You can edit and publish it later.', 'success')
        return redirect(url_for('blog.edit_blog', post_id=new_post.id))


@blog_bp.route('/blog/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_blog(post_id):
    """Edit existing blog post"""
    post = BlogPost.query.get_or_404(post_id)

    # Check if user is authorized to edit
    if post.user_id != current_user.id:
        flash('You are not authorized to edit this post', 'error')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        is_published = request.form.get('publish', 'false') == 'true'

        if not title or not content:
            flash('Please enter both title and content', 'error')
            return render_template('editor.html', post=post)

        # Update title and regenerate slug if title changed
        if post.title != title:
            post.title = title
            post.slug = generate_slug(title)

        post.content = content
        post.status = 'published' if is_published else 'draft'
        post.updated_at = datetime.utcnow()

        # Update word count and reading time
        post.word_count = len(content.split())
        post.reading_time = max(1, post.word_count // 200)

        # Set published_at if publishing for the first time
        if is_published and not post.published_at:
            post.published_at = datetime.utcnow()

        db.session.commit()

        flash('Blog post updated successfully!', 'success')
        return redirect(url_for('main.view_post', slug=post.slug) if is_published else url_for('blog.my_posts'))

    return render_template('editor.html', post=post)


@blog_bp.route('/blog/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_blog(post_id):
    """Delete blog post"""
    post = BlogPost.query.get_or_404(post_id)

    # Check if user is authorized to delete
    if post.user_id != current_user.id and not current_user.is_admin:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        flash('You are not authorized to delete this post', 'error')
        return redirect(url_for('main.index'))

    db.session.delete(post)
    db.session.commit()

    if request.is_json:
        return jsonify({'success': True, 'message': 'Blog post deleted successfully'})

    flash('Blog post deleted successfully', 'success')
    return redirect(url_for('main.index'))


@blog_bp.route('/blog/publish/<int:post_id>', methods=['POST'])
@login_required
def publish_draft(post_id):
    """Publish a draft blog post"""
    post = BlogPost.query.get_or_404(post_id)

    # Check if user is authorized to publish
    if post.user_id != current_user.id:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        flash('You are not authorized to publish this post', 'error')
        return redirect(url_for('blog.my_posts'))

    post.status = 'published'
    post.published_at = datetime.utcnow()
    post.updated_at = datetime.utcnow()
    db.session.commit()

    if request.is_json:
        return jsonify({'success': True, 'message': 'Draft published successfully'})

    flash('Draft published successfully!', 'success')
    return redirect(url_for('main.view_post', slug=post.slug))


@blog_bp.route('/blog/upload-image', methods=['POST'])
@login_required
def upload_image():
    """Upload image for blog post"""
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'No image file provided'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF, WEBP'}), 400

    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_FILE_SIZE:
        return jsonify({'success': False, 'message': 'File size exceeds 5MB limit'}), 400

    try:
        # Generate secure filename
        original_filename = secure_filename(file.filename)
        file_ext = original_filename.rsplit('.', 1)[1].lower()

        # Create unique filename using hash
        file_content = file.read()
        file.seek(0)
        file_hash = hashlib.md5(file_content).hexdigest()
        filename = f"{file_hash}.{file_ext}"

        # Create upload directory if it doesn't exist
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        # Save file
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # Get file URL (relative to static folder)
        file_url = f"/static/uploads/{filename}"

        # Save to database
        media_file = MediaFile(
            user_id=current_user.id,
            filename=filename,
            original_name=original_filename,
            mime_type=file.content_type,
            file_size=file_size,
            file_hash=file_hash,
            url=file_url
        )

        db.session.add(media_file)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Image uploaded successfully',
            'url': file_url,
            'filename': original_filename,
            'media_id': media_file.id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Upload failed: {str(e)}'}), 500

