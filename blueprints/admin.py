"""
Admin routes blueprint
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from extensions import db
from models import User, BlogPost, AIUsage, Comment, Like, APIConfiguration
from sqlalchemy import desc

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin', methods=['GET'])
@admin_bp.route('/admin-dashboard', methods=['GET'])
@login_required
def admin_dashboard():
    """Admin panel/dashboard"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))

    # Get statistics
    total_users = User.query.count()
    total_blogs = BlogPost.query.filter_by(is_published=True).count()
    total_drafts = BlogPost.query.filter_by(is_published=False).count()
    ai_usage_count = AIUsage.query.count()
    total_comments = Comment.query.count()
    total_likes = Like.query.count()

    # Get API configuration
    api_config = APIConfiguration.query.first()

    # Get recent activity
    recent_posts = BlogPost.query.order_by(desc(BlogPost.created_at)).limit(5).all()
    recent_users = User.query.order_by(desc(User.created_at)).limit(5).all()

    # Create stats dict for template
    stats = {
        'total_users': total_users,
        'total_blogs': total_blogs,
        'total_drafts': total_drafts,
        'ai_usage_count': ai_usage_count,
        'total_comments': total_comments,
        'total_likes': total_likes,
        'recent_posts': recent_posts,
        'recent_users': recent_users
    }

    return render_template('admin.html', stats=stats, api_config=api_config)


@admin_bp.route('/admin/api-config', methods=['POST'])
@login_required
def save_api_config():
    """Save API configuration"""
    if not current_user.is_admin:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))

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
    current_app.logger.info(f'API config saved - OpenAI: {bool(openai_key)}, Anthropic: {bool(anthropic_key)}')

    # Reset AI service to use new configuration
    # The AI service will be reinitialized on next use

    if request.is_json:
        return jsonify({'success': True, 'message': 'API configuration saved successfully'})

    flash('API configuration saved successfully! You can now use the AI enhancement feature.', 'success')
    return redirect(url_for('admin.admin_dashboard'))

