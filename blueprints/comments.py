"""
Comment routes blueprint
"""
from flask import Blueprint, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Comment, BlogPost
from sqlalchemy import desc

comments_bp = Blueprint('comments', __name__)


@comments_bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    """Add comment to blog post"""
    post = BlogPost.query.get_or_404(post_id)
    content = request.form.get('content', '').strip()

    if not content:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Comment cannot be empty'}), 400
        flash('Comment cannot be empty', 'error')
        return redirect(url_for('main.view_post', slug=post.slug))

    new_comment = Comment(
        content=content,
        user_id=current_user.id,
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
    return redirect(url_for('main.view_post', slug=post.slug))


@comments_bp.route('/comment/delete/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    """Delete a comment"""
    comment = Comment.query.get_or_404(comment_id)

    # Check if user is authorized to delete (comment author or post author)
    if comment.user_id != current_user.id and comment.post.user_id != current_user.id and not current_user.is_admin:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        flash('You are not authorized to delete this comment', 'error')
        return redirect(url_for('main.view_post', slug=comment.post.slug))

    post_slug = comment.post.slug
    db.session.delete(comment)
    db.session.commit()

    if request.is_json:
        return jsonify({'success': True, 'message': 'Comment deleted successfully'})

    flash('Comment deleted successfully', 'success')
    return redirect(url_for('main.view_post', slug=post_slug))

