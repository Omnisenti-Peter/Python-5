"""
Blog routes for Opinian platform
Handles blog post creation, editing, and viewing
"""

import os
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from app import get_db_connection, login_required, role_required, allowed_file, log_user_activity
from ai_service import ai_service

logger = logging.getLogger(__name__)

bp = Blueprint('blog', __name__, url_prefix='/blog')

def get_upload_path():
    """Get upload path for blog images"""
    return os.path.join('uploads', 'blog_images')

@bp.route('/')
def blog_index():
    """Blog index page - list all published blog posts"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get all published blog posts from active groups
            cursor.execute("""
                SELECT bp.*, u.username, u.first_name, u.last_name, g.name as group_name
                FROM blog_posts bp
                JOIN users u ON bp.author_id = u.id
                LEFT JOIN groups g ON bp.group_id = g.id
                WHERE bp.is_published = TRUE AND (g.is_active = TRUE OR bp.group_id IS NULL)
                ORDER BY bp.published_at DESC
            """)
            blog_posts = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return render_template('blog/index.html', blog_posts=blog_posts)
        else:
            flash('Database connection error', 'danger')
            return render_template('blog/index.html', blog_posts=[])
            
    except Exception as e:
        flash('Error loading blog posts', 'danger')
        return render_template('blog/index.html', blog_posts=[])

@bp.route('/post/<slug>')
def view_post(slug):
    """View a single blog post"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get blog post
            cursor.execute("""
                SELECT bp.*, u.username, u.first_name, u.last_name, g.name as group_name
                FROM blog_posts bp
                JOIN users u ON bp.author_id = u.id
                LEFT JOIN groups g ON bp.group_id = g.id
                WHERE bp.slug = %s AND bp.is_published = TRUE
            """, (slug,))
            
            post = cursor.fetchone()
            
            if not post:
                flash('Blog post not found', 'danger')
                return redirect(url_for('blog.blog_index'))
            
            # Increment view count
            cursor.execute("UPDATE blog_posts SET view_count = view_count + 1 WHERE id = %s", (post['id'],))
            conn.commit()
            
            # Get related posts (same group or same tags)
            cursor.execute("""
                SELECT id, title, slug, published_at, excerpt
                FROM blog_posts
                WHERE group_id = %s AND id != %s AND is_published = TRUE
                ORDER BY published_at DESC
                LIMIT 5
            """, (post['group_id'], post['id']))
            related_posts = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return render_template('blog/view.html', post=post, related_posts=related_posts)
        else:
            flash('Database connection error', 'danger')
            return redirect(url_for('blog.blog_index'))
            
    except Exception as e:
        flash('Error loading blog post', 'danger')
        return redirect(url_for('blog.blog_index'))

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    """Create a new blog post"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        excerpt = request.form.get('excerpt')
        tags = request.form.get('tags', '')
        meta_description = request.form.get('meta_description')
        meta_keywords = request.form.get('meta_keywords')

        # Check action button (publish or draft)
        action = request.form.get('action', 'draft')
        is_published = (action == 'publish')

        # Handle publish scheduling
        publish_type = request.form.get('publish_type', 'immediate')
        scheduled_date = request.form.get('publish_date')

        # Determine published_at timestamp
        published_at = None
        if is_published:
            if publish_type == 'scheduled' and scheduled_date:
                try:
                    # Parse the scheduled date
                    from dateutil import parser
                    published_at = parser.parse(scheduled_date)
                except:
                    published_at = datetime.utcnow()
            else:
                published_at = datetime.utcnow()
        
        # Handle file upload
        featured_image_url = None
        if 'featured_image' in request.files:
            file = request.files['featured_image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_path = get_upload_path()
                os.makedirs(upload_path, exist_ok=True)
                
                # Generate unique filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_filename = f"{timestamp}_{filename}"
                file_path = os.path.join(upload_path, unique_filename)
                
                file.save(file_path)
                featured_image_url = file_path
        
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                
                # Generate slug from title
                import re
                slug = re.sub(r'[^a-zA-Z0-9-]+', '-', title.lower()).strip('-')
                
                # Ensure unique slug
                cursor.execute("SELECT id FROM blog_posts WHERE slug = %s", (slug,))
                if cursor.fetchone():
                    slug = f"{slug}-{int(datetime.now().timestamp())}"
                
                # Insert blog post
                cursor.execute("""
                    INSERT INTO blog_posts
                    (title, slug, content, excerpt, author_id, group_id, featured_image_url,
                     tags, meta_description, meta_keywords, is_published, published_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    title, slug, content, excerpt, session['user_id'], session.get('group_id'),
                    featured_image_url, tags.split(',') if tags else [], meta_description, meta_keywords,
                    is_published, published_at
                ))
                
                post_id = cursor.fetchone()[0]
                conn.commit()
                cursor.close()
                conn.close()
                
                # Log activity
                log_user_activity(session['user_id'], 'create_blog_post', 'blog_post', post_id)
                
                flash('Blog post created successfully!', 'success')
                if is_published:
                    return redirect(url_for('blog.view_post', slug=slug))
                else:
                    return redirect(url_for('blog.my_posts'))
            else:
                flash('Database connection error', 'danger')
                
        except Exception as e:
            flash('Error creating blog post', 'danger')
            logger.error(f"Error creating blog post: {e}")
    
    return render_template('blog/create.html')

@bp.route('/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    """Edit an existing blog post"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get blog post
            cursor.execute("""
                SELECT * FROM blog_posts WHERE id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                flash('Blog post not found', 'danger')
                return redirect(url_for('blog.my_posts'))
            
            # Check permissions
            if session['user_role'] not in ['SuperAdmin', 'Admin'] and post['author_id'] != session['user_id']:
                flash('You do not have permission to edit this post', 'danger')
                return redirect(url_for('blog.my_posts'))
            
            if request.method == 'POST':
                title = request.form.get('title')
                content = request.form.get('content')
                excerpt = request.form.get('excerpt')
                tags = request.form.get('tags', '')
                meta_description = request.form.get('meta_description')
                meta_keywords = request.form.get('meta_keywords')

                # Check action button (publish or draft)
                action = request.form.get('action', 'draft')
                is_published = (action == 'publish')

                # Handle publish scheduling
                publish_type = request.form.get('publish_type', 'immediate')
                scheduled_date = request.form.get('publish_date')

                # Determine published_at timestamp
                published_at = post['published_at']  # Keep existing if already set
                if is_published:
                    if publish_type == 'scheduled' and scheduled_date:
                        try:
                            from dateutil import parser
                            published_at = parser.parse(scheduled_date)
                        except:
                            published_at = datetime.utcnow()
                    elif not published_at:  # Only set if not already published
                        published_at = datetime.utcnow()
                else:
                    published_at = None  # Clear if saving as draft
                
                # Handle file upload
                featured_image_url = post['featured_image_url']
                if 'featured_image' in request.files:
                    file = request.files['featured_image']
                    if file and file.filename and allowed_file(file.filename):
                        # Delete old image if exists
                        if featured_image_url and os.path.exists(featured_image_url):
                            os.remove(featured_image_url)
                        
                        filename = secure_filename(file.filename)
                        upload_path = get_upload_path()
                        os.makedirs(upload_path, exist_ok=True)
                        
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        unique_filename = f"{timestamp}_{filename}"
                        file_path = os.path.join(upload_path, unique_filename)
                        
                        file.save(file_path)
                        featured_image_url = file_path
                
                # Update slug if title changed
                import re
                slug = re.sub(r'[^a-zA-Z0-9-]+', '-', title.lower()).strip('-')
                if slug != post['slug']:
                    cursor.execute("SELECT id FROM blog_posts WHERE slug = %s AND id != %s", (slug, post_id))
                    if cursor.fetchone():
                        slug = f"{slug}-{int(datetime.now().timestamp())}"
                
                # Update blog post
                cursor.execute("""
                    UPDATE blog_posts
                    SET title = %s, slug = %s, content = %s, excerpt = %s,
                        featured_image_url = %s, tags = %s, meta_description = %s,
                        meta_keywords = %s, is_published = %s, published_at = %s,
                        updated_at = %s
                    WHERE id = %s
                """, (
                    title, slug, content, excerpt, featured_image_url,
                    tags.split(',') if tags else [],
                    meta_description, meta_keywords, is_published, published_at,
                    datetime.utcnow(), post_id
                ))
                
                conn.commit()
                cursor.close()
                conn.close()
                
                # Log activity
                log_user_activity(session['user_id'], 'edit_blog_post', 'blog_post', post_id)
                
                flash('Blog post updated successfully!', 'success')
                if is_published:
                    return redirect(url_for('blog.view_post', slug=slug))
                else:
                    return redirect(url_for('blog.my_posts'))
            
            cursor.close()
            conn.close()
            
            return render_template('blog/edit.html', post=post)
        else:
            flash('Database connection error', 'danger')
            return redirect(url_for('blog.my_posts'))
            
    except Exception as e:
        flash('Error loading blog post', 'danger')
        logger.error(f"Error editing blog post: {e}")
        return redirect(url_for('blog.my_posts'))

@bp.route('/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    """Delete a blog post"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get blog post
            cursor.execute("SELECT * FROM blog_posts WHERE id = %s", (post_id,))
            post = cursor.fetchone()
            
            if not post:
                flash('Blog post not found', 'danger')
                return redirect(url_for('blog.my_posts'))
            
            # Check permissions
            if session['user_role'] not in ['SuperAdmin', 'Admin'] and post['author_id'] != session['user_id']:
                flash('You do not have permission to delete this post', 'danger')
                return redirect(url_for('blog.my_posts'))
            
            # Delete featured image if exists
            if post['featured_image_url'] and os.path.exists(post['featured_image_url']):
                os.remove(post['featured_image_url'])
            
            # Delete blog post
            cursor.execute("DELETE FROM blog_posts WHERE id = %s", (post_id,))
            conn.commit()
            cursor.close()
            conn.close()
            
            # Log activity
            log_user_activity(session['user_id'], 'delete_blog_post', 'blog_post', post_id)
            
            flash('Blog post deleted successfully!', 'success')
            return redirect(url_for('blog.my_posts'))
        else:
            flash('Database connection error', 'danger')
            return redirect(url_for('blog.my_posts'))
            
    except Exception as e:
        flash('Error deleting blog post', 'danger')
        logger.error(f"Error deleting blog post: {e}")
        return redirect(url_for('blog.my_posts'))

@bp.route('/my-posts')
@login_required
def my_posts():
    """List user's blog posts"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            user_role = session['user_role']
            user_id = session['user_id']
            
            if user_role in ['SuperAdmin', 'Admin']:
                # Admins can see all posts in their group
                group_id = session.get('group_id')
                if group_id is not None:
                    cursor.execute("""
                        SELECT bp.*, u.username
                        FROM blog_posts bp
                        JOIN users u ON bp.author_id = u.id
                        WHERE bp.group_id = %s
                        ORDER BY bp.created_at DESC
                    """, (group_id,))
                else:
                    cursor.execute("""
                        SELECT bp.*, u.username
                        FROM blog_posts bp
                        JOIN users u ON bp.author_id = u.id
                        WHERE bp.group_id IS NULL
                        ORDER BY bp.created_at DESC
                    """)
            else:
                # Regular users can only see their own posts
                cursor.execute("""
                    SELECT * FROM blog_posts 
                    WHERE author_id = %s
                    ORDER BY created_at DESC
                """, (user_id,))
            
            blog_posts = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return render_template('blog/my_posts.html', blog_posts=blog_posts)
        else:
            flash('Database connection error', 'danger')
            return render_template('blog/my_posts.html', blog_posts=[])
            
    except Exception as e:
        flash('Error loading blog posts', 'danger')
        logger.error(f"Error loading my posts: {e}")
        return render_template('blog/my_posts.html', blog_posts=[])

@bp.route('/ai-assistant')
@login_required
def ai_assistant():
    """AI writing assistant page"""
    return render_template('blog/ai_assistant.html')

@bp.route('/ai-generate', methods=['POST'])
@login_required
def ai_generate():
    """Generate or improve content using AI for the embedded modal"""
    try:
        data = request.get_json()
        input_text = data.get('input')
        style = data.get('style', 'professional')
        action = data.get('action', 'generate')

        if not input_text:
            return jsonify({
                'success': False,
                'error': 'Input text is required'
            }), 400

        # Build prompt based on action and style
        if action == 'improve':
            prompt = f"Improve the following content in a {style} style:\n\n{input_text}"
        else:
            prompt = f"Write a blog post in a {style} style based on this idea:\n\n{input_text}"

        # Use AI service to generate content
        result = ai_service.generate_blog_content(prompt, 'blog_post')

        # Log activity
        log_user_activity(
            session['user_id'],
            f'ai_{action}_content',
            'blog_content',
            None,
            {'style': style, 'action': action}
        )

        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"Error in AI generate: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate content',
            'message': str(e)
        }), 500

@bp.route('/generate-content', methods=['POST'])
@login_required
def generate_content():
    """Generate content using AI"""
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        content_type = data.get('content_type', 'blog_post')

        if not prompt:
            return jsonify({
                'success': False,
                'error': 'Prompt is required'
            }), 400

        # Use AI service to generate content
        result = ai_service.generate_blog_content(prompt, content_type)

        # Log activity
        log_user_activity(
            session['user_id'],
            'generate_ai_content',
            'blog_content',
            None,
            {'prompt': prompt[:100], 'content_type': content_type}
        )

        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"Error generating content: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate content',
            'message': str(e)
        }), 500

@bp.route('/generate-titles', methods=['POST'])
@login_required
def generate_titles():
    """Generate title suggestions using AI"""
    try:
        data = request.get_json()
        topic = data.get('topic')
        count = data.get('count', 5)

        if not topic:
            return jsonify({
                'success': False,
                'error': 'Topic is required'
            }), 400

        # Use AI service to generate titles
        result = ai_service.generate_title_suggestions(topic, count)

        # Log activity
        log_user_activity(
            session['user_id'],
            'generate_ai_titles',
            'blog_titles',
            None,
            {'topic': topic[:100]}
        )

        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"Error generating titles: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate titles',
            'message': str(e)
        }), 500

@bp.route('/improve-content', methods=['POST'])
@login_required
def improve_content():
    """Improve existing content using AI"""
    try:
        data = request.get_json()
        content = data.get('content')
        instructions = data.get('instructions', 'Improve the writing quality and engagement')

        if not content:
            return jsonify({
                'success': False,
                'error': 'Content is required'
            }), 400

        # Use AI service to improve content
        result = ai_service.improve_content(content, instructions)

        # Log activity
        log_user_activity(
            session['user_id'],
            'improve_ai_content',
            'blog_content',
            None,
            {'instructions': instructions[:100]}
        )

        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"Error improving content: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to improve content',
            'message': str(e)
        }), 500

@bp.route('/generate-excerpt', methods=['POST'])
@login_required
def generate_excerpt():
    """Generate excerpt from full content using AI"""
    try:
        data = request.get_json()
        content = data.get('content')
        max_length = data.get('max_length', 200)

        if not content:
            return jsonify({
                'success': False,
                'error': 'Content is required'
            }), 400

        # Use AI service to generate excerpt
        result = ai_service.generate_excerpt(content, max_length)

        # Log activity
        log_user_activity(
            session['user_id'],
            'generate_ai_excerpt',
            'blog_excerpt',
            None
        )

        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"Error generating excerpt: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate excerpt',
            'message': str(e)
        }), 500