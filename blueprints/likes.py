"""
Like routes blueprint
"""
from flask import Blueprint, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Like, BlogPost

likes_bp = Blueprint('likes', __name__)


@likes_bp.route('/post/<int:post_id>/like', methods=['POST'])
@likes_bp.route('/blog/like/<int:post_id>', methods=['POST'])
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
    return redirect(url_for('main.view_post', slug=post.slug))

