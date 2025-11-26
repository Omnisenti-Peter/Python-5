#!/usr/bin/env python3
"""
Entry point for the Opinian Flask application
"""

import os
import sys
from app import app
from config import config

def main():
    """Main function to run the application"""
    # Get configuration from environment or use default
    config_name = os.environ.get('FLASK_ENV') or 'development'
    
    # Apply configuration
    app.config.from_object(config[config_name])
    
    # Print startup message
    print(f"Starting Opinian Platform in {config_name} mode...")
    print(f"Database: {config[config_name].DB_NAME}")
    print(f"Upload folder: {config[config_name].UPLOAD_FOLDER}")
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=config[config_name].DEBUG
    )

if __name__ == '__main__':
    main()