"""
AI routes blueprint
"""
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from extensions import db
from models import AIUsage, APIConfiguration
from ai_service import AIService

ai_bp = Blueprint('ai', __name__)

# Global AI service instance (will be reset when config changes)
ai_service = None


@ai_bp.route('/ai', methods=['GET'])
@ai_bp.route('/ai-tools', methods=['GET'])
@login_required
def ai_tools():
    """AI enhancement page"""
    return render_template('ai_tools.html')


@ai_bp.route('/ai/enhance', methods=['POST'])
@login_required
def enhance_with_ai():
    """Enhance text with AI"""
    global ai_service

    # Get request data
    if request.is_json:
        data = request.get_json()
        input_text = data.get('text', '').strip()
        content_type = data.get('content_type', 'story')
        writing_style = data.get('writing_style', 'noir')
        content_length = data.get('content_length', 'medium')
        target_audience = data.get('target_audience', 'general')
    else:
        input_text = request.form.get('text', '').strip()
        content_type = request.form.get('content_type', 'story')
        writing_style = request.form.get('writing_style', 'noir')
        content_length = request.form.get('content_length', 'medium')
        target_audience = request.form.get('target_audience', 'general')

    if not input_text:
        if request.is_json:
            return jsonify({'success': False, 'message': 'No text provided'}), 400
        flash('Please enter some text to enhance', 'warning')
        return redirect(url_for('ai.ai_tools'))

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
        current_app.logger.info(f'Loaded API config from database: OpenAI={bool(openai_key)}, Anthropic={bool(anthropic_key)}')

    # If no keys in database, try environment variables
    if not openai_key and not anthropic_key:
        openai_key = os.environ.get('OPENAI_API_KEY') or current_app.config.get('OPENAI_API_KEY')
        anthropic_key = os.environ.get('ANTHROPIC_API_KEY') or current_app.config.get('ANTHROPIC_API_KEY')
        current_app.logger.info(f'Loaded API keys from environment: OpenAI={bool(openai_key)}, Anthropic={bool(anthropic_key)}')

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
        current_app.logger.error(error_msg)
        if request.is_json:
            return jsonify({'success': False, 'message': error_msg}), 500
        flash(error_msg, 'error')
        return redirect(url_for('ai.ai_tools'))

    try:
        # Enhance text with AI using all parameters
        enhanced_text = ai_service.enhance_story(
            input_text,
            content_type=content_type,
            writing_style=writing_style,
            content_length=content_length,
            target_audience=target_audience
        )

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

        return render_template('ai_tools.html',
                             input_text=input_text,
                             enhanced_text=enhanced_text,
                             message='Story enhanced successfully!')

    except Exception as e:
        current_app.logger.error(f'AI enhancement error: {str(e)}')
        error_message = 'AI service error. Please check your API configuration or try again later.'

        if request.is_json:
            return jsonify({'success': False, 'message': error_message}), 500

        flash(error_message, 'error')
        return redirect(url_for('ai.ai_tools'))

