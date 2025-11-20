"""
Quick start script for Opinian Flask Application
This script handles initial setup and runs the application
"""
import os
import sys

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import flask
        import flask_sqlalchemy
        import flask_login
        print("✓ All required packages are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing required packages: {e}")
        print("\nPlease install dependencies:")
        print("  pip install -r requirements.txt")
        return False

def check_env_file():
    """Check if .env file exists"""
    if not os.path.exists('.env'):
        print("⚠ .env file not found")
        print("\nCreating .env from template...")
        if os.path.exists('.env.example'):
            # Generate a secret key
            import secrets
            secret_key = secrets.token_hex(32)

            with open('.env.example', 'r') as example:
                content = example.read()
                content = content.replace('your-secret-key-here-change-in-production', secret_key)

            with open('.env', 'w') as env_file:
                env_file.write(content)
            print("✓ .env file created with generated secret key")
        else:
            print("✗ .env.example not found")
            return False
    else:
        print("✓ .env file exists")
    return True

def check_directories():
    """Ensure required directories exist"""
    dirs = ['instance', 'static/uploads', 'templates', 'static/css', 'static/js']
    for directory in dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✓ Created directory: {directory}")
        else:
            print(f"✓ Directory exists: {directory}")
    return True

def main():
    """Main setup and run function"""
    print("=" * 50)
    print("Opinian Flask Application - Quick Start")
    print("=" * 50)
    print()

    print("Checking setup...")
    print("-" * 50)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Check .env file
    if not check_env_file():
        sys.exit(1)

    # Check directories
    if not check_directories():
        sys.exit(1)

    print()
    print("=" * 50)
    print("Setup complete! Starting application...")
    print("=" * 50)
    print()
    print("Demo accounts:")
    print("  Admin: admin / admin123")
    print("  User:  user / user123")
    print()
    print("The application will be available at:")
    print("  http://localhost:5000")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    print()

    # Import and run the app
    from app import app
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()
