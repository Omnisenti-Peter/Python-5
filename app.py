"""
Opinian - Flask Blogging Platform with AI Enhancement
Main application file
"""
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_, desc
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from models import db, User, BlogPost, Comment, Like, AIUsage, APIConfiguration
from config import config
from ai_service import AIService

# Initialize Flask app
app = Flask(__name__)

# Load configuration
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[env])

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

# Initialize AI Service
ai_service = None

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    return db.session.get(User, int(user_id))

# ===== DATABASE INITIALIZATION =====
@app.before_request
def create_tables():
    """Create database tables and demo data on first request"""
    if not hasattr(app, 'tables_created'):
        with app.app_context():
            db.create_all()

            # Create demo users if they don't exist
            if User.query.count() == 0:
                admin = User(
                    username='admin',
                    email='admin@opinian.com',
                    is_admin=True
                )
                admin.set_password('admin123')

                user = User(
                    username='user',
                    email='user@opinian.com',
                    is_admin=False
                )
                user.set_password('user123')

                db.session.add(admin)
                db.session.add(user)
                db.session.commit()

                # Create demo blog posts
                post1 = BlogPost(
                    title="The Jazz Age Chronicles: A Night at the Speakeasy",
                    content="The year was 1925, and the air was thick with cigarette smoke and the sweet sounds of jazz. Sarah adjusted her feathered headband and stepped into the dimly lit speakeasy, her beaded dress catching the golden light from the chandeliers above. The password had been 'butterscotch' - a detail she wouldn't soon forget.",
                    author_id=admin.id,
                    is_published=True
                )

                post2 = BlogPost(
                    title="Midnight in Chicago: A Detective's Tale",
                    content="The rain fell in sheets as Detective Murphy lit his fifth cigarette of the night. The dame in the red dress had promised him answers, but all he'd gotten so far was a headache and an empty wallet. This city had a way of chewing people up and spitting them out, and tonight, he was feeling particularly chewed.",
                    author_id=user.id,
                    is_published=True
                )

                db.session.add(post1)
                db.session.add(post2)
                db.session.commit()

                app.logger.info('Database initialized with demo data')

        app.tables_created = True

# ===== AUTHENTICATION ROUTES =====
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Please enter both username and password', 'error')
            return redirect(url_for('login'))

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=True)
            flash(f'Welcome back, {user.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password', 'error')

    return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()

    # Validation
    if not username or not email or not password:
        flash('Please fill in all fields', 'error')
        return redirect(url_for('index'))

    if len(username) < 3:
        flash('Username must be at least 3 characters long', 'error')
        return redirect(url_for('index'))

    if len(password) < 6:
        flash('Password must be at least 6 characters long', 'error')
        return redirect(url_for('index'))

    if '@' not in email:
        flash('Please enter a valid email address', 'error')
        return redirect(url_for('index'))

    # Check if user already exists
    if User.query.filter((User.username == username) | (User.email == email)).first():
        flash('Username or email already exists', 'error')
        return redirect(url_for('index'))

    # Create new user
    new_user = User(username=username, email=email, is_admin=False)
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    # Auto-login after registration
    login_user(new_user, remember=True)
    flash(f'Welcome to Opinian, {username}! Your account has been created.', 'success')

    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('index'))

# ===== MAIN ROUTES =====
@app.route('/')
def index():
    """Homepage with blog posts"""
    # Get search and filter parameters
    search_query = request.args.get('search', '').strip()
    author_filter = request.args.get('author', '').strip()
    page = request.args.get('page', 1, type=int)

    # Base query for published posts
    query = BlogPost.query.filter_by(is_published=True)

    # Apply search filter
    if search_query:
        query = query.filter(
            or_(
                BlogPost.title.ilike(f'%{search_query}%'),
                BlogPost.content.ilike(f'%{search_query}%')
            )
        )

    # Apply author filter
    if author_filter:
        author_user = User.query.filter_by(username=author_filter).first()
        if author_user:
            query = query.filter_by(author_id=author_user.id)

    # Order by creation date (newest first)
    query = query.order_by(desc(BlogPost.created_at))

    # Paginate results
    posts = query.paginate(
        page=page,
        per_page=app.config['POSTS_PER_PAGE'],
        error_out=False
    )

    # Get all authors for filter dropdown
    authors = User.query.join(BlogPost).filter(BlogPost.is_published == True).distinct().all()

    return render_template('index.html',
                         posts=posts,
                         authors=authors,
                         search_query=search_query,
                         author_filter=author_filter)

@app.route('/post/<int:post_id>')
def view_post(post_id):
    """View single blog post with comments"""
    post = BlogPost.query.get_or_404(post_id)

    if not post.is_published and (not current_user.is_authenticated or current_user.id != post.author_id):
        flash('This post is not available', 'error')
        return redirect(url_for('index'))

    # Get comments for this post
    comments = Comment.query.filter_by(post_id=post_id).order_by(desc(Comment.created_at)).all()

    return render_template('post.html', post=post, comments=comments)

# ===== BLOG CRUD ROUTES =====
@app.route('/blog/write', methods=['GET'])
@login_required
def write_blog():
    """Blog writing page"""
    return render_template('write.html')

@app.route('/blog/my-posts', methods=['GET'])
@login_required
def my_posts():
    """Show user's own posts (published and drafts)"""
    published_posts = BlogPost.query.filter_by(
        author_id=current_user.id,
        is_published=True
    ).order_by(desc(BlogPost.created_at)).all()

    draft_posts = BlogPost.query.filter_by(
        author_id=current_user.id,
        is_published=False
    ).order_by(desc(BlogPost.updated_at)).all()

    return render_template('my_posts.html',
                         published_posts=published_posts,
                         draft_posts=draft_posts)

@app.route('/blog/create', methods=['POST'])
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
        return redirect(url_for('write_blog'))

    new_post = BlogPost(
        title=title,
        content=content,
        author_id=current_user.id,
        is_published=is_published,
        ai_enhanced=ai_enhanced
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
        return redirect(url_for('view_post', post_id=new_post.id))
    else:
        flash('Draft saved successfully! You can edit and publish it later.', 'success')
        return redirect(url_for('edit_blog', post_id=new_post.id))

@app.route('/blog/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_blog(post_id):
    """Edit existing blog post"""
    post = BlogPost.query.get_or_404(post_id)

    # Check if user is authorized to edit
    if post.author_id != current_user.id:
        flash('You are not authorized to edit this post', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        is_published = request.form.get('publish', 'false') == 'true'

        if not title or not content:
            flash('Please enter both title and content', 'error')
            return render_template('edit.html', post=post)

        post.title = title
        post.content = content
        post.is_published = is_published
        post.updated_at = datetime.utcnow()

        db.session.commit()

        flash('Blog post updated successfully!', 'success')
        return redirect(url_for('view_post', post_id=post.id))

    return render_template('edit.html', post=post)

@app.route('/blog/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_blog(post_id):
    """Delete blog post"""
    post = BlogPost.query.get_or_404(post_id)

    # Check if user is authorized to delete
    if post.author_id != current_user.id and not current_user.is_admin:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        flash('You are not authorized to delete this post', 'error')
        return redirect(url_for('index'))

    db.session.delete(post)
    db.session.commit()

    if request.is_json:
        return jsonify({'success': True, 'message': 'Blog post deleted successfully'})

    flash('Blog post deleted successfully', 'success')
    return redirect(url_for('index'))

# ===== COMMENT ROUTES =====
@app.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    """Add comment to blog post"""
    post = BlogPost.query.get_or_404(post_id)
    content = request.form.get('content', '').strip()

    if not content:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Comment cannot be empty'}), 400
        flash('Comment cannot be empty', 'error')
        return redirect(url_for('view_post', post_id=post_id))

    new_comment = Comment(
        content=content,
        author_id=current_user.id,
        post_id=post_id
    )

    db.session.add(new_comment)
    db.session.commit()

    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Comment added successfully',
            'comment': {
                'id': new_comment.id,
                'content': new_comment.content,
                'author': new_comment.author.username,
                'created_at': new_comment.created_at.strftime('%B %d, %Y at %I:%M %p')
            }
        })

    flash('Comment added successfully', 'success')
    return redirect(url_for('view_post', post_id=post_id))

# ===== LIKE ROUTES =====
@app.route('/post/<int:post_id>/like', methods=['POST'])
@login_required
def toggle_like(post_id):
    """Toggle like on blog post"""
    post = BlogPost.query.get_or_404(post_id)

    # Check if user already liked this post
    existing_like = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()

    if existing_like:
        # Unlike
        db.session.delete(existing_like)
        db.session.commit()
        liked = False
        message = 'Post unliked'
    else:
        # Like
        new_like = Like(user_id=current_user.id, post_id=post_id)
        db.session.add(new_like)
        db.session.commit()
        liked = True
        message = 'Post liked'

    if request.is_json:
        return jsonify({
            'success': True,
            'liked': liked,
            'like_count': post.like_count,
            'message': message
        })

    flash(message, 'success')
    return redirect(url_for('view_post', post_id=post_id))

# ===== AI ROUTES =====
@app.route('/ai', methods=['GET'])
@login_required
def ai_page():
    """AI enhancement page"""
    return render_template('ai.html')

@app.route('/ai/enhance', methods=['POST'])
@login_required
def enhance_with_ai():
    """Enhance text with AI"""
    global ai_service

    # Get request data
    if request.is_json:
        data = request.get_json()
        input_text = data.get('text', '').strip()
    else:
        input_text = request.form.get('text', '').strip()

    if not input_text:
        if request.is_json:
            return jsonify({'success': False, 'message': 'No text provided'}), 400
        flash('Please enter some text to enhance', 'warning')
        return redirect(url_for('ai_page'))

    # Always reinitialize AI service to get latest configuration
    openai_key = None
    anthropic_key = None
    preferred_model = 'gpt-3.5-turbo'
    temperature = 0.7

    # First, try to get from database (admin panel configuration)
    api_config = APIConfiguration.query.first()
    if api_config:
        openai_key = api_config.openai_key if api_config.openai_key else None
        anthropic_key = api_config.anthropic_key if api_config.anthropic_key else None
        preferred_model = api_config.preferred_model
        temperature = api_config.temperature
        app.logger.info(f'Loaded API config from database: OpenAI={bool(openai_key)}, Anthropic={bool(anthropic_key)}')

    # If no keys in database, try environment variables
    if not openai_key and not anthropic_key:
        openai_key = os.environ.get('OPENAI_API_KEY') or app.config.get('OPENAI_API_KEY')
        anthropic_key = os.environ.get('ANTHROPIC_API_KEY') or app.config.get('ANTHROPIC_API_KEY')
        app.logger.info(f'Loaded API keys from environment: OpenAI={bool(openai_key)}, Anthropic={bool(anthropic_key)}')

    # Initialize AI service with the keys
    ai_service = AIService(
        openai_key=openai_key,
        anthropic_key=anthropic_key,
        preferred_model=preferred_model,
        temperature=temperature
    )

    # Check if AI service is configured
    if not ai_service.is_configured():
        error_msg = 'No AI service configured. Please add your OpenAI or Anthropic API key in the Admin Panel or .env file.'
        app.logger.error(error_msg)
        if request.is_json:
            return jsonify({'success': False, 'message': error_msg}), 500
        flash(error_msg, 'error')
        return redirect(url_for('ai_page'))

    try:
        # Enhance text with AI
        enhanced_text = ai_service.enhance_story(input_text)

        # Log AI usage
        ai_usage = AIUsage(
            user_id=current_user.id,
            model_used=ai_service.preferred_model,
            input_length=len(input_text),
            output_length=len(enhanced_text)
        )
        db.session.add(ai_usage)
        db.session.commit()

        if request.is_json:
            return jsonify({
                'success': True,
                'enhanced_text': enhanced_text,
                'message': 'Story enhanced successfully!'
            })

        return render_template('ai.html',
                             input_text=input_text,
                             enhanced_text=enhanced_text,
                             message='Story enhanced successfully!')

    except Exception as e:
        app.logger.error(f'AI enhancement error: {str(e)}')
        error_message = 'AI service error. Please check your API configuration or try again later.'

        if request.is_json:
            return jsonify({'success': False, 'message': error_message}), 500

        flash(error_message, 'error')
        return redirect(url_for('ai_page'))

# ===== ADMIN ROUTES =====
@app.route('/admin', methods=['GET'])
@login_required
def admin_panel():
    """Admin panel"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))

    # Get statistics
    total_users = User.query.count()
    total_blogs = BlogPost.query.filter_by(is_published=True).count()
    ai_usage_count = AIUsage.query.count()

    # Get API configuration
    api_config = APIConfiguration.query.first()

    return render_template('admin.html',
                         total_users=total_users,
                         total_blogs=total_blogs,
                         ai_usage_count=ai_usage_count,
                         api_config=api_config)

@app.route('/admin/api-config', methods=['POST'])
@login_required
def save_api_config():
    """Save API configuration"""
    if not current_user.is_admin:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        flash('Access denied', 'error')
        return redirect(url_for('index'))

    openai_key = request.form.get('openai_key', '').strip()
    anthropic_key = request.form.get('anthropic_key', '').strip()
    huggingface_key = request.form.get('huggingface_key', '').strip()
    preferred_model = request.form.get('preferred_model', 'gpt-3.5-turbo')
    temperature = float(request.form.get('temperature', 0.7))

    # Convert empty strings to None to avoid storing empty strings
    openai_key = openai_key if openai_key else None
    anthropic_key = anthropic_key if anthropic_key else None
    huggingface_key = huggingface_key if huggingface_key else None

    # Get or create API configuration
    api_config = APIConfiguration.query.first()
    if api_config:
        api_config.openai_key = openai_key
        api_config.anthropic_key = anthropic_key
        api_config.huggingface_key = huggingface_key
        api_config.preferred_model = preferred_model
        api_config.temperature = temperature
    else:
        api_config = APIConfiguration(
            openai_key=openai_key,
            anthropic_key=anthropic_key,
            huggingface_key=huggingface_key,
            preferred_model=preferred_model,
            temperature=temperature
        )
        db.session.add(api_config)

    db.session.commit()

    # Log for debugging
    app.logger.info(f'API config saved - OpenAI: {bool(openai_key)}, Anthropic: {bool(anthropic_key)}')

    # Reset AI service to use new configuration
    global ai_service
    ai_service = None

    if request.is_json:
        return jsonify({'success': True, 'message': 'API configuration saved successfully'})

    flash('API configuration saved successfully! You can now use the AI enhancement feature.', 'success')
    return redirect(url_for('admin_panel'))

# ===== ERROR HANDLERS =====
@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    db.session.rollback()
    return render_template('500.html'), 500

# ===== TEMPLATE FILTERS =====
@app.template_filter('truncate_words')
def truncate_words(text, length=50):
    """Truncate text to specified number of words"""
    words = text.split()
    if len(words) > length:
        return ' '.join(words[:length]) + '...'
    return text

@app.template_filter('format_date')
def format_date(date):
    """Format date for display"""
    return date.strftime('%B %d, %Y')

@app.template_filter('format_datetime')
def format_datetime(date):
    """Format datetime for display"""
    return date.strftime('%B %d, %Y at %I:%M %p')

# ===== RUN APPLICATION =====
if __name__ == '__main__':
    # Create instance folder if it doesn't exist
    instance_path = os.path.join(os.path.dirname(__file__), 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)

    app.run(debug=True, host='0.0.0.0', port=5000)
