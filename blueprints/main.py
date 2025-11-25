"""
Main routes blueprint (homepage, post viewing)
"""
from flask import Blueprint, render_template, request
from sqlalchemy import or_, desc
from extensions import db
from models import BlogPost, User, Comment, Like
from flask_login import current_user

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Homepage with blog posts"""
    # Get search and filter parameters
    search_query = request.args.get('search', '').strip()
    author_filter = request.args.get('author', '').strip()
    page = request.args.get('page', 1, type=int)

    # Base query for published posts
    query = BlogPost.query.filter_by(status='published')

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
            query = query.filter_by(user_id=author_user.id)

    # Order by creation date (newest first)
    query = query.order_by(desc(BlogPost.created_at))

    # Get app from current_app context
    from flask import current_app

    # Paginate results
    posts = query.paginate(
        page=page,
        per_page=current_app.config.get('POSTS_PER_PAGE', 10),
        error_out=False
    )

    # Get all authors for filter dropdown
    authors = User.query.join(BlogPost).filter(BlogPost.status == 'published').distinct().all()

    return render_template('index.html',
                         posts=posts,
                         authors=authors,
                         search_query=search_query,
                         author_filter=author_filter)


@main_bp.route('/post/<slug>')
def view_post(slug):
    """View single blog post with comments"""
    post = BlogPost.query.filter_by(slug=slug).first_or_404()

    if post.status != 'published' and (not current_user.is_authenticated or current_user.id != post.user_id):
        from flask import flash, redirect, url_for
        flash('This post is not available', 'error')
        return redirect(url_for('main.index'))

    # Get comments for this post
    comments = Comment.query.filter_by(post_id=post.id).order_by(desc(Comment.created_at)).all()

    # Check if current user has liked this post
    user_liked = False
    if current_user.is_authenticated:
        user_liked = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first() is not None

    return render_template('post.html', post=post, comments=comments, user_liked=user_liked)


@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

