#!/usr/bin/env python3
"""
Setup script for Opinian SaaS Blogging Platform
Installs dependencies and sets up the initial environment
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✓ Python version {sys.version_info.major}.{sys.version_info.minor} is compatible")

def check_postgresql():
    """Check if PostgreSQL is available"""
    try:
        result = subprocess.run(['psql', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✓ PostgreSQL is available: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠ PostgreSQL not found in PATH. Please ensure PostgreSQL is installed and accessible.")
        return False

def install_dependencies():
    """Install Python dependencies"""
    print("\nInstalling Python dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True)
        print("✓ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        sys.exit(1)

def setup_environment():
    """Setup environment files and directories"""
    print("\nSetting up environment...")
    
    # Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        print("Creating .env file from template...")
        shutil.copy('.env.example', '.env')
        print("✓ .env file created. Please edit it with your configuration.")
    else:
        print("✓ .env file already exists")
    
    # Create necessary directories
    directories = ['uploads', 'uploads/blog_images', 'logs', 'flask_session']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✓ Created directory: {directory}")
        else:
            print(f"✓ Directory already exists: {directory}")

def create_database():
    """Create and initialize the database"""
    print("\nSetting up database...")
    try:
        # Run database initialization
        subprocess.run([sys.executable, 'init_db.py'], check=True)
        print("✓ Database initialized successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to initialize database: {e}")
        print("Please ensure PostgreSQL is running and your database credentials are correct.")
        sys.exit(1)

def test_imports():
    """Test if all required imports work"""
    print("\nTesting imports...")
    try:
        import flask
        import psycopg2
        import jwt
        import bcrypt
        import werkzeug
        print("✓ All required imports are working")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        sys.exit(1)

def main():
    """Main setup function"""
    print("🚀 Opinian SaaS Blogging Platform Setup")
    print("=" * 50)
    
    # Step 1: Check Python version
    check_python_version()
    
    # Step 2: Check PostgreSQL
    postgres_available = check_postgresql()
    
    # Step 3: Install dependencies
    install_dependencies()
    
    # Step 4: Test imports
    test_imports()
    
    # Step 5: Setup environment
    setup_environment()
    
    # Step 6: Initialize database
    create_database()
    
    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit the .env file with your database credentials")
    print("2. Ensure PostgreSQL is running")
    print("3. Run 'python run.py' to start the application")
    print("4. Visit http://localhost:5000 in your browser")
    print("\nFirst user to register will become the SuperAdmin!")
    
    if not postgres_available:
        print("\n⚠️  Warning: PostgreSQL was not found in your PATH.")
        print("Please ensure PostgreSQL is installed and accessible.")
        print("You can download it from: https://www.postgresql.org/download/")

if __name__ == '__main__':
    main()