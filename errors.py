"""
Error handlers for Flask application
"""
from flask import render_template
from extensions import db


def register_error_handlers(app):
    """Register error handlers with the Flask app"""
    
    @app.errorhandler(404)
    def not_found(error):
        """404 error handler"""
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """500 error handler"""
        db.session.rollback()
        return render_template('500.html'), 500

