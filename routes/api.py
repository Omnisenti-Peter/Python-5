"""
API routes for Opinian platform
RESTful API endpoints for frontend integration
"""

import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.security import check_password_hash, generate_password_hash
import psycopg2
from psycopg2.extras import RealDictCursor
from app import get_db_connection, log_user_activity

bp = Blueprint('api', __name__, url_prefix='/api')

def token_required(f):
    """Decorator to require JWT token for API endpoints"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        
        return f(current_user_id, *args, **kwargs)
    
    return decorated

@bp.route('/auth/login', methods=['POST'])
def api_login():
    """API login endpoint"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'message': 'Username and password required'}), 400
        
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
                    return jsonify({'message': 'Account is banned'}), 403
                
                # Generate JWT token
                token = jwt.encode({
                    'user_id': user['id'],
                    'username': user['username'],
                    'role': user['role_name'],
                    'exp': datetime.utcnow() + timedelta(hours=24)
                }, current_app.config['SECRET_KEY'], algorithm='HS256')
                
                # Log login activity
                log_user_activity(user['id'], 'api_login')
                
                return jsonify({
                    'message': 'Login successful',
                    'token': token,
                    'user': {
                        'id': user['id'],
                        'username': user['username'],
                        'email': user['email'],
                        'first_name': user['first_name'],
                        'last_name': user['last_name'],
                        'role': user['role_name'],
                        'group_id': user['group_id']
                    }
                })
            else:
                return jsonify({'message': 'Invalid credentials'}), 401
        else:
            return jsonify({'message': 'Database connection error'}), 500
            
    except Exception as e:
        return jsonify({'message': 'Login failed'}), 500

@bp.route('/auth/register', methods=['POST'])
def api_register():
    """API registration endpoint"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        
        if not all([username, email, password]):
            return jsonify({'message': 'Username, email, and password required'}), 400
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", 
                         (username, email))
            if cursor.fetchone():
                return jsonify({'message': 'Username or email already exists'}), 409
            
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
            
            # Log registration
            log_user_activity(user_id, 'api_register')
            
            return jsonify({
                'message': 'Registration successful',
                'user_id': user_id
            }), 201
        else:
            return jsonify({'message': 'Database connection error'}), 500
            
    except Exception as e:
        return jsonify({'message': 'Registration failed'}), 500

@bp.route('/blog/posts', methods=['GET'])
def get_blog_posts():
    """Get blog posts with pagination and filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        group_id = request.args.get('group_id', type=int)
        search = request.args.get('search', '')
        
        offset = (page - 1) * per_page
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Build query
            query = """
                SELECT bp.*, u.username, u.first_name, u.last_name, g.name as group_name
                FROM blog_posts bp
                JOIN users u ON bp.author_id = u.id
                JOIN groups g ON bp.group_id = g.id
                WHERE bp.is_published = TRUE AND g.is_active = TRUE
            """
            params = []
            
            if group_id:
                query += " AND bp.group_id = %s"
                params.append(group_id)
            
            if search:
                query += " AND (bp.title ILIKE %s OR bp.content ILIKE %s)"
                params.extend([f'%{search}%', f'%{search}%'])
            
            query += " ORDER BY bp.published_at DESC LIMIT %s OFFSET %s"
            params.extend([per_page, offset])
            
            cursor.execute(query, params)
            posts = cursor.fetchall()
            
            # Get total count
            count_query = """
                SELECT COUNT(*) 
                FROM blog_posts bp
                JOIN groups g ON bp.group_id = g.id
                WHERE bp.is_published = TRUE AND g.is_active = TRUE
            """
            count_params = []
            
            if group_id:
                count_query += " AND bp.group_id = %s"
                count_params.append(group_id)
            
            if search:
                count_query += " AND (bp.title ILIKE %s OR bp.content ILIKE %s)"
                count_params.extend([f'%{search}%', f'%{search}%'])
            
            cursor.execute(count_query, count_params)
            total = cursor.fetchone()['count']
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'posts': posts,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            })
        else:
            return jsonify({'message': 'Database connection error'}), 500
            
    except Exception as e:
        return jsonify({'message': 'Failed to fetch blog posts'}), 500

@bp.route('/blog/posts/<int:post_id>', methods=['GET'])
def get_blog_post(post_id):
    """Get a single blog post"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT bp.*, u.username, u.first_name, u.last_name, g.name as group_name
                FROM blog_posts bp
                JOIN users u ON bp.author_id = u.id
                JOIN groups g ON bp.group_id = g.id
                WHERE bp.id = %s AND bp.is_published = TRUE
            """, (post_id,))
            
            post = cursor.fetchone()
            
            if not post:
                return jsonify({'message': 'Post not found'}), 404
            
            # Increment view count
            cursor.execute("UPDATE blog_posts SET view_count = view_count + 1 WHERE id = %s", (post_id,))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return jsonify(post)
        else:
            return jsonify({'message': 'Database connection error'}), 500
            
    except Exception as e:
        return jsonify({'message': 'Failed to fetch blog post'}), 500

@bp.route('/blog/posts', methods=['POST'])
@token_required
def create_blog_post(current_user_id):
    """Create a new blog post via API"""
    try:
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')
        excerpt = data.get('excerpt', '')
        tags = data.get('tags', [])
        is_published = data.get('is_published', False)
        
        if not title or not content:
            return jsonify({'message': 'Title and content are required'}), 400
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            # Generate slug
            import re
            slug = re.sub(r'[^a-zA-Z0-9-]+', '-', title.lower()).strip('-')
            
            # Ensure unique slug
            cursor.execute("SELECT id FROM blog_posts WHERE slug = %s", (slug,))
            if cursor.fetchone():
                slug = f"{slug}-{int(datetime.now().timestamp())}"
            
            # Get user group
            cursor.execute("SELECT group_id FROM users WHERE id = %s", (current_user_id,))
            group_id = cursor.fetchone()[0]
            
            # Insert blog post
            cursor.execute("""
                INSERT INTO blog_posts 
                (title, slug, content, excerpt, author_id, group_id, tags, is_published, published_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                title, slug, content, excerpt, current_user_id, group_id,
                tags, is_published, datetime.utcnow() if is_published else None
            ))
            
            post_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            
            # Log activity
            log_user_activity(current_user_id, 'api_create_blog_post', 'blog_post', post_id)
            
            return jsonify({
                'message': 'Blog post created successfully',
                'post_id': post_id,
                'slug': slug
            }), 201
        else:
            return jsonify({'message': 'Database connection error'}), 500
            
    except Exception as e:
        return jsonify({'message': 'Failed to create blog post'}), 500

@bp.route('/users/profile', methods=['GET'])
@token_required
def get_user_profile(current_user_id):
    """Get current user profile"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT u.id, u.username, u.email, u.first_name, u.last_name, 
                       u.bio, u.profile_image_url, u.created_at,
                       r.name as role_name, g.name as group_name
                FROM users u
                JOIN roles r ON u.role_id = r.id
                LEFT JOIN groups g ON u.group_id = g.id
                WHERE u.id = %s
            """, (current_user_id,))
            
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not user:
                return jsonify({'message': 'User not found'}), 404
            
            return jsonify(user)
        else:
            return jsonify({'message': 'Database connection error'}), 500
            
    except Exception as e:
        return jsonify({'message': 'Failed to fetch user profile'}), 500

@bp.route('/users/profile', methods=['PUT'])
@token_required
def update_user_profile(current_user_id):
    """Update user profile"""
    try:
        data = request.get_json()
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        bio = data.get('bio', '')
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users 
                SET first_name = %s, last_name = %s, bio = %s, updated_at = %s
                WHERE id = %s
            """, (first_name, last_name, bio, datetime.utcnow(), current_user_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Log activity
            log_user_activity(current_user_id, 'api_update_profile', 'user', current_user_id)
            
            return jsonify({'message': 'Profile updated successfully'})
        else:
            return jsonify({'message': 'Database connection error'}), 500
            
    except Exception as e:
        return jsonify({'message': 'Failed to update profile'}), 500

@bp.route('/ai/generate', methods=['POST'])
@token_required
def generate_ai_content(current_user_id):
    """Generate content using AI"""
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        content_type = data.get('content_type', 'blog_post')
        
        if not prompt:
            return jsonify({'message': 'Prompt is required'}), 400
        
        # TODO: Integrate with actual LLM API
        # Mock response for now
        generated_content = f"""
        <h2>Generated Content</h2>
        <p>This content was generated based on your prompt: "{prompt}"</p>
        <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. This is placeholder content that would be replaced by actual AI-generated text based on your specific requirements and the capabilities of the integrated AI service.</p>
        """
        
        # Log activity
        log_user_activity(current_user_id, 'api_ai_generate', 'ai_content', None, {'prompt': prompt[:100]})
        
        return jsonify({
            'content': generated_content,
            'word_count': len(generated_content.split()),
            'estimated_reading_time': len(generated_content.split()) // 200  # 200 words per minute
        })
        
    except Exception as e:
        return jsonify({'message': 'Failed to generate content'}), 500

@bp.route('/system/settings', methods=['GET'])
def get_system_settings():
    """Get public system settings"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("SELECT setting_key, setting_value FROM system_settings")
            settings = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            # Convert to dictionary
            settings_dict = {s['setting_key']: s['setting_value'] for s in settings}
            
            return jsonify(settings_dict)
        else:
            return jsonify({'message': 'Database connection error'}), 500
            
    except Exception as e:
        return jsonify({'message': 'Failed to fetch settings'}), 500