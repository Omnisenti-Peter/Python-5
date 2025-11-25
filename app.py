"""
Opinian - Flask Blogging Platform with AI Enhancement
Main application file
"""
import os
from flask import Flask
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from extensions import db, login_manager
from models import User
from config import config
from database import init_db
from filters import register_filters
from errors import register_error_handlers

# Import blueprints
from blueprints.auth import auth_bp
from blueprints.main import main_bp
from blueprints.blog import blog_bp
from blueprints.comments import comments_bp
from blueprints.likes import likes_bp
from blueprints.ai import ai_bp
from blueprints.admin import admin_bp


def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    env = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[env])
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    
    # Configure user loader
    @login_manager.user_loader
    def load_user(user_id):
        """Load user for Flask-Login"""
        return db.session.get(User, int(user_id))
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(blog_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(likes_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(admin_bp)
    
    # Register template filters
    register_filters(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Initialize database on first request
    @app.before_request
    def create_tables():
        """Create database tables and demo data on first request"""
        if not hasattr(app, 'tables_created'):
            init_db(app)
            app.tables_created = True
    
    return app


# Create app instance
app = create_app()

# ===== RUN APPLICATION =====
if __name__ == '__main__':
    # Create instance folder if it doesn't exist
    instance_path = os.path.join(os.path.dirname(__file__), 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)

    app.run(debug=True, host='0.0.0.0', port=5000)
