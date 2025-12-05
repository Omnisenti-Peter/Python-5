#!/usr/bin/env python3
"""
Database initialization script for Opinian platform
Creates database tables and initial data
"""

import os
import sys
import re
import getpass
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            port=os.getenv('DB_PORT', '5432'),
            database='postgres'  # Connect to default postgres database first
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", 
                      (os.getenv('DB_NAME', 'opinian'),))
        
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE {os.getenv('DB_NAME', 'opinian')}")
            print(f"Database {os.getenv('DB_NAME', 'opinian')} created successfully")
        else:
            print(f"Database {os.getenv('DB_NAME', 'opinian')} already exists")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error creating database: {e}")
        sys.exit(1)

def create_tables():
    """Create all database tables"""
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'opinian'),
            port=os.getenv('DB_PORT', '5432')
        )
        cursor = conn.cursor()

        # Create tables in order (respecting foreign key constraints)

        print("Creating roles table...")
        # Create roles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                description TEXT,
                permissions JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  - roles table OK")
        
        # Create permissions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS permissions (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                resource VARCHAR(50),
                action VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create groups table
        # NOTE: Groups (Organizations) are automatically created when SuperAdmin creates an Admin user
        # Groups represent tenant boundaries for multi-tenant architecture
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                admin_user_id INTEGER,
                theme_id INTEGER,
                contact_page_content TEXT,
                about_page_content TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create themes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS themes (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                css_variables JSONB,
                custom_css TEXT,
                gjs_data JSONB DEFAULT NULL,
                gjs_assets JSONB DEFAULT '[]'::jsonb,
                html_export TEXT DEFAULT NULL,
                react_export TEXT DEFAULT NULL,
                theme_type VARCHAR(50) DEFAULT 'manual',
                ai_prompt TEXT DEFAULT NULL,
                created_by INTEGER,
                group_id INTEGER REFERENCES groups(id),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Update groups table to reference themes
        try:
            cursor.execute("""
                ALTER TABLE groups
                ADD CONSTRAINT fk_groups_theme
                FOREIGN KEY (theme_id) REFERENCES themes(id)
                ON DELETE SET NULL
            """)
        except Exception:
            pass  # Constraint already exists
        
        # Create templates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                html_content TEXT,
                css_content TEXT,
                js_content TEXT,
                created_by INTEGER,
                group_id INTEGER REFERENCES groups(id),
                is_default BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                profile_image_url VARCHAR(255),
                bio TEXT,
                role_id INTEGER REFERENCES roles(id),
                group_id INTEGER REFERENCES groups(id),
                is_active BOOLEAN DEFAULT TRUE,
                is_banned BOOLEAN DEFAULT FALSE,
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Update groups table to reference admin user
        try:
            cursor.execute("""
                ALTER TABLE groups
                ADD CONSTRAINT fk_groups_admin
                FOREIGN KEY (admin_user_id) REFERENCES users(id)
                ON DELETE SET NULL
            """)
        except Exception:
            pass  # Constraint already exists
        
        # Update themes table to reference creator
        try:
            cursor.execute("""
                ALTER TABLE themes
                ADD CONSTRAINT fk_themes_creator
                FOREIGN KEY (created_by) REFERENCES users(id)
                ON DELETE SET NULL
            """)
        except Exception:
            pass  # Constraint already exists
        
        # Update templates table to reference creator
        try:
            cursor.execute("""
                ALTER TABLE templates
                ADD CONSTRAINT fk_templates_creator
                FOREIGN KEY (created_by) REFERENCES users(id)
                ON DELETE SET NULL
            """)
        except Exception:
            pass  # Constraint already exists
        
        # Create role_permissions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS role_permissions (
                id SERIAL PRIMARY KEY,
                role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
                permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create pages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pages (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                slug VARCHAR(200) NOT NULL,
                content TEXT,
                author_id INTEGER REFERENCES users(id),
                group_id INTEGER REFERENCES groups(id),
                template_id INTEGER REFERENCES templates(id),
                is_published BOOLEAN DEFAULT FALSE,
                meta_description TEXT,
                meta_keywords TEXT,
                published_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create blog_posts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blog_posts (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                slug VARCHAR(200) NOT NULL,
                content TEXT NOT NULL,
                excerpt TEXT,
                author_id INTEGER REFERENCES users(id),
                group_id INTEGER REFERENCES groups(id),
                page_id INTEGER REFERENCES pages(id),
                featured_image_url VARCHAR(255),
                is_published BOOLEAN DEFAULT FALSE,
                tags TEXT[],
                meta_description TEXT,
                meta_keywords TEXT,
                view_count INTEGER DEFAULT 0,
                published_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create categories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                slug VARCHAR(100) NOT NULL,
                description TEXT,
                group_id INTEGER REFERENCES groups(id),
                parent_id INTEGER REFERENCES categories(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create blog_categories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blog_categories (
                id SERIAL PRIMARY KEY,
                blog_post_id INTEGER REFERENCES blog_posts(id) ON DELETE CASCADE,
                category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE
            )
        """)
        
        # Create media_files table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS media_files (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                original_filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                file_size INTEGER,
                mime_type VARCHAR(100),
                uploaded_by INTEGER REFERENCES users(id),
                group_id INTEGER REFERENCES groups(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create user_activity_logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_activity_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                action VARCHAR(100) NOT NULL,
                resource_type VARCHAR(50),
                resource_id INTEGER,
                ip_address INET,
                user_agent TEXT,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create moderation_queue table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS moderation_queue (
                id SERIAL PRIMARY KEY,
                content_type VARCHAR(50) NOT NULL,
                content_id INTEGER NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                reviewed_by INTEGER REFERENCES users(id),
                review_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TIMESTAMP
            )
        """)
        
        # Create api_settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_settings (
                id SERIAL PRIMARY KEY,
                setting_key VARCHAR(100) UNIQUE NOT NULL,
                setting_value TEXT,
                description TEXT,
                is_encrypted BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create system_settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                id SERIAL PRIMARY KEY,
                setting_key VARCHAR(100) UNIQUE NOT NULL,
                setting_value TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print("All tables created successfully")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Note: Some tables may already exist - {e}")
        if conn:
            conn.rollback()
            if cursor:
                cursor.close()
            conn.close()
        print("Continuing to schema update which will handle existing tables...")

def update_schema():
    """Update existing schema by adding missing columns"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'opinian'),
            port=os.getenv('DB_PORT', '5432')
        )
        cursor = conn.cursor()

        print("Checking and updating schema...")

        # Helper function to check if column exists
        def column_exists(table_name, column_name):
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = %s AND column_name = %s
                )
            """, (table_name, column_name))
            return cursor.fetchone()[0]

        # Add missing columns to themes table
        if not column_exists('themes', 'gjs_data'):
            cursor.execute("ALTER TABLE themes ADD COLUMN gjs_data JSONB DEFAULT NULL")
            print("  - Added column: themes.gjs_data")

        if not column_exists('themes', 'gjs_assets'):
            cursor.execute("ALTER TABLE themes ADD COLUMN gjs_assets JSONB DEFAULT '[]'::jsonb")
            print("  - Added column: themes.gjs_assets")

        if not column_exists('themes', 'html_export'):
            cursor.execute("ALTER TABLE themes ADD COLUMN html_export TEXT DEFAULT NULL")
            print("  - Added column: themes.html_export")

        if not column_exists('themes', 'react_export'):
            cursor.execute("ALTER TABLE themes ADD COLUMN react_export TEXT DEFAULT NULL")
            print("  - Added column: themes.react_export")

        if not column_exists('themes', 'theme_type'):
            cursor.execute("ALTER TABLE themes ADD COLUMN theme_type VARCHAR(50) DEFAULT 'manual'")
            print("  - Added column: themes.theme_type")

        if not column_exists('themes', 'ai_prompt'):
            cursor.execute("ALTER TABLE themes ADD COLUMN ai_prompt TEXT DEFAULT NULL")
            print("  - Added column: themes.ai_prompt")

        # Add missing columns to groups table
        if not column_exists('groups', 'contact_page_content'):
            cursor.execute("ALTER TABLE groups ADD COLUMN contact_page_content TEXT")
            print("  - Added column: groups.contact_page_content")

        if not column_exists('groups', 'about_page_content'):
            cursor.execute("ALTER TABLE groups ADD COLUMN about_page_content TEXT")
            print("  - Added column: groups.about_page_content")

        # Add missing columns to templates table
        if not column_exists('templates', 'js_content'):
            cursor.execute("ALTER TABLE templates ADD COLUMN js_content TEXT")
            print("  - Added column: templates.js_content")

        # Add missing columns to pages table
        if not column_exists('pages', 'slug'):
            cursor.execute("ALTER TABLE pages ADD COLUMN slug VARCHAR(200) NOT NULL DEFAULT ''")
            print("  - Added column: pages.slug")

        if not column_exists('pages', 'template_id'):
            cursor.execute("ALTER TABLE pages ADD COLUMN template_id INTEGER REFERENCES templates(id)")
            print("  - Added column: pages.template_id")

        if not column_exists('pages', 'meta_description'):
            cursor.execute("ALTER TABLE pages ADD COLUMN meta_description TEXT")
            print("  - Added column: pages.meta_description")

        if not column_exists('pages', 'meta_keywords'):
            cursor.execute("ALTER TABLE pages ADD COLUMN meta_keywords TEXT")
            print("  - Added column: pages.meta_keywords")

        # Add missing columns to blog_posts table
        if not column_exists('blog_posts', 'page_id'):
            cursor.execute("ALTER TABLE blog_posts ADD COLUMN page_id INTEGER REFERENCES pages(id)")
            print("  - Added column: blog_posts.page_id")

        if not column_exists('blog_posts', 'featured_image_url'):
            cursor.execute("ALTER TABLE blog_posts ADD COLUMN featured_image_url VARCHAR(255)")
            print("  - Added column: blog_posts.featured_image_url")

        if not column_exists('blog_posts', 'tags'):
            cursor.execute("ALTER TABLE blog_posts ADD COLUMN tags TEXT[]")
            print("  - Added column: blog_posts.tags")

        if not column_exists('blog_posts', 'view_count'):
            cursor.execute("ALTER TABLE blog_posts ADD COLUMN view_count INTEGER DEFAULT 0")
            print("  - Added column: blog_posts.view_count")

        # Add missing columns to users table
        if not column_exists('users', 'profile_image_url'):
            cursor.execute("ALTER TABLE users ADD COLUMN profile_image_url VARCHAR(255)")
            print("  - Added column: users.profile_image_url")

        if not column_exists('users', 'bio'):
            cursor.execute("ALTER TABLE users ADD COLUMN bio TEXT")
            print("  - Added column: users.bio")

        if not column_exists('users', 'is_banned'):
            cursor.execute("ALTER TABLE users ADD COLUMN is_banned BOOLEAN DEFAULT FALSE")
            print("  - Added column: users.is_banned")

        # Add missing columns to media_files table
        if not column_exists('media_files', 'file_size'):
            cursor.execute("ALTER TABLE media_files ADD COLUMN file_size INTEGER")
            print("  - Added column: media_files.file_size")

        if not column_exists('media_files', 'mime_type'):
            cursor.execute("ALTER TABLE media_files ADD COLUMN mime_type VARCHAR(100)")
            print("  - Added column: media_files.mime_type")

        # Helper function to check if constraint exists
        def constraint_exists(constraint_name):
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.table_constraints
                    WHERE constraint_name = %s
                )
            """, (constraint_name,))
            return cursor.fetchone()[0]

        # Add missing foreign key constraints
        if not constraint_exists('fk_groups_theme'):
            try:
                cursor.execute("""
                    ALTER TABLE groups
                    ADD CONSTRAINT fk_groups_theme
                    FOREIGN KEY (theme_id) REFERENCES themes(id)
                    ON DELETE SET NULL
                """)
                print("  - Added constraint: fk_groups_theme")
            except Exception as e:
                print(f"  - Note: Could not add fk_groups_theme constraint: {e}")

        if not constraint_exists('fk_groups_admin'):
            try:
                cursor.execute("""
                    ALTER TABLE groups
                    ADD CONSTRAINT fk_groups_admin
                    FOREIGN KEY (admin_user_id) REFERENCES users(id)
                    ON DELETE SET NULL
                """)
                print("  - Added constraint: fk_groups_admin")
            except Exception as e:
                print(f"  - Note: Could not add fk_groups_admin constraint: {e}")

        if not constraint_exists('fk_themes_creator'):
            try:
                cursor.execute("""
                    ALTER TABLE themes
                    ADD CONSTRAINT fk_themes_creator
                    FOREIGN KEY (created_by) REFERENCES users(id)
                    ON DELETE SET NULL
                """)
                print("  - Added constraint: fk_themes_creator")
            except Exception as e:
                print(f"  - Note: Could not add fk_themes_creator constraint: {e}")

        if not constraint_exists('fk_templates_creator'):
            try:
                cursor.execute("""
                    ALTER TABLE templates
                    ADD CONSTRAINT fk_templates_creator
                    FOREIGN KEY (created_by) REFERENCES users(id)
                    ON DELETE SET NULL
                """)
                print("  - Added constraint: fk_templates_creator")
            except Exception as e:
                print(f"  - Note: Could not add fk_templates_creator constraint: {e}")

        conn.commit()
        print("Schema update completed successfully")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error updating schema: {e}")
        # Don't exit on schema update errors - the table might already be correct
        pass

def insert_initial_data():
    """Insert initial data (roles, permissions, default theme)"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'opinian'),
            port=os.getenv('DB_PORT', '5432')
        )
        cursor = conn.cursor()
        
        # Insert default roles
        # NOTE: Only SuperAdmin can create Admin users (which auto-creates organizations)
        # Admin users can only create User and SuperUser roles within their organization
        cursor.execute("""
            INSERT INTO roles (name, description, permissions) VALUES
            ('SuperAdmin', 'Full platform administration access - Can create Admin users and manage all organizations',
             '{"platform_manage": true, "user_manage": true, "content_manage": true, "theme_manage": true, "api_manage": true}'::jsonb),
            ('Admin', 'Organization administration access - Can create User and SuperUser within their organization',
             '{"group_manage": true, "user_manage": true, "content_manage": true, "theme_manage": true}'::jsonb),
            ('SuperUser', 'Extended content creation access - Can create pages and content',
             '{"content_create": true, "page_create": true, "theme_view": true}'::jsonb),
            ('User', 'Basic user access - Can create and view content',
             '{"content_create": true, "content_view": true}'::jsonb)
            ON CONFLICT (name) DO NOTHING
        """)
        
        # Insert default permissions
        cursor.execute("""
            INSERT INTO permissions (name, description, resource, action) VALUES
            ('platform_manage', 'Manage entire platform', 'platform', 'manage'),
            ('user_manage', 'Manage users', 'users', 'manage'),
            ('content_manage', 'Manage all content', 'content', 'manage'),
            ('content_create', 'Create content', 'content', 'create'),
            ('content_view', 'View content', 'content', 'view'),
            ('page_create', 'Create pages', 'pages', 'create'),
            ('theme_manage', 'Manage themes', 'themes', 'manage'),
            ('theme_view', 'View themes', 'themes', 'view'),
            ('group_manage', 'Manage groups', 'groups', 'manage'),
            ('api_manage', 'Manage API settings', 'api', 'manage')
            ON CONFLICT (name) DO NOTHING
        """)
        
        # Insert role permissions relationships
        cursor.execute("""
            INSERT INTO role_permissions (role_id, permission_id) 
            SELECT r.id, p.id FROM roles r, permissions p
            WHERE r.name = 'SuperAdmin' AND p.name IN (
                'platform_manage', 'user_manage', 'content_manage', 'theme_manage', 'api_manage'
            )
            ON CONFLICT DO NOTHING
        """)
        
        cursor.execute("""
            INSERT INTO role_permissions (role_id, permission_id) 
            SELECT r.id, p.id FROM roles r, permissions p
            WHERE r.name = 'Admin' AND p.name IN (
                'group_manage', 'user_manage', 'content_manage', 'theme_manage'
            )
            ON CONFLICT DO NOTHING
        """)
        
        cursor.execute("""
            INSERT INTO role_permissions (role_id, permission_id) 
            SELECT r.id, p.id FROM roles r, permissions p
            WHERE r.name = 'SuperUser' AND p.name IN (
                'content_create', 'page_create', 'theme_view', 'content_view'
            )
            ON CONFLICT DO NOTHING
        """)
        
        cursor.execute("""
            INSERT INTO role_permissions (role_id, permission_id) 
            SELECT r.id, p.id FROM roles r, permissions p
            WHERE r.name = 'User' AND p.name IN ('content_create', 'content_view')
            ON CONFLICT DO NOTHING
        """)
        
        # Insert default system settings
        cursor.execute("""
            INSERT INTO system_settings (setting_key, setting_value, description) VALUES
            ('site_name', 'Opinian', 'Platform name'),
            ('site_description', 'SaaS Blogging Platform', 'Platform description'),
            ('max_upload_size', '10485760', 'Maximum file upload size in bytes (10MB)'),
            ('allowed_file_types', 'image/jpeg,image/png,image/gif,image/webp', 'Allowed file types for upload')
            ON CONFLICT (setting_key) DO NOTHING
        """)
        
        # Insert default page templates
        cursor.execute("""
            INSERT INTO templates (name, description, html_content, css_content, is_default) VALUES
            ('Default Page', 'Simple clean page template',
             '<div class="page-wrapper"><div class="page-content">{{content}}</div></div>',
             '.page-wrapper { max-width: 1200px; margin: 0 auto; padding: 40px 20px; } .page-content { background: white; padding: 40px; border-radius: 8px; }',
             TRUE),
            ('Full Width', 'Full width page without sidebar',
             '<div class="full-width-wrapper">{{content}}</div>',
             '.full-width-wrapper { width: 100%; padding: 20px; }',
             TRUE),
            ('Two Column', 'Two column layout with sidebar',
             '<div class="two-column-layout"><main class="main-content">{{content}}</main><aside class="sidebar"><div class="sidebar-widget">Sidebar content</div></aside></div>',
             '.two-column-layout { display: grid; grid-template-columns: 2fr 1fr; gap: 30px; max-width: 1200px; margin: 0 auto; padding: 40px 20px; } .main-content { background: white; padding: 40px; border-radius: 8px; } .sidebar { padding: 20px; }',
             TRUE),
            ('Landing Page', 'Hero section with content area',
             '<div class="hero-section"><h1 class="hero-title">{{title}}</h1></div><div class="content-section">{{content}}</div>',
             '.hero-section { background: linear-gradient(135deg, #1a1a1a, #2c2c2c); color: white; padding: 100px 20px; text-align: center; } .hero-title { font-size: 3rem; margin-bottom: 20px; } .content-section { max-width: 1000px; margin: 60px auto; padding: 0 20px; }',
             TRUE)
            ON CONFLICT DO NOTHING
        """)

        conn.commit()
        print("Initial data inserted successfully")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error inserting initial data: {e}")
        sys.exit(1)

def create_indexes():
    """Create database indexes for performance"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'opinian'),
            port=os.getenv('DB_PORT', '5432')
        )
        cursor = conn.cursor()
        
        # Create performance indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_group_id ON users(group_id)",
            "CREATE INDEX IF NOT EXISTS idx_users_role_id ON users(role_id)",
            "CREATE INDEX IF NOT EXISTS idx_blog_posts_author_id ON blog_posts(author_id)",
            "CREATE INDEX IF NOT EXISTS idx_blog_posts_group_id ON blog_posts(group_id)",
            "CREATE INDEX IF NOT EXISTS idx_blog_posts_published ON blog_posts(is_published)",
            "CREATE INDEX IF NOT EXISTS idx_pages_group_id ON pages(group_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_activity_logs_user_id ON user_activity_logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_activity_logs_created_at ON user_activity_logs(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_themes_group_id ON themes(group_id)",
            "CREATE INDEX IF NOT EXISTS idx_themes_theme_type ON themes(theme_type)",
            "CREATE INDEX IF NOT EXISTS idx_themes_created_by ON themes(created_by)"
        ]
        
        for index in indexes:
            cursor.execute(index)
        
        conn.commit()
        print("Database indexes created successfully")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error creating indexes: {e}")
        sys.exit(1)

def validate_email(email):
    """Basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def create_superadmin():
    """Create the first SuperAdmin user if none exists"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'opinian'),
            port=os.getenv('DB_PORT', '5432')
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check if SuperAdmin already exists
        cursor.execute("""
            SELECT u.id, u.username, u.email
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE r.name = 'SuperAdmin' AND u.is_active = TRUE
        """)

        existing_superadmins = cursor.fetchall()

        if existing_superadmins:
            print("\n[WARNING] SuperAdmin user(s) already exist:")
            for sa in existing_superadmins:
                print(f"   - {sa['username']} ({sa['email']})")
            print("\nSkipping SuperAdmin creation.")
            cursor.close()
            conn.close()
            return

        print("\n" + "="*60)
        print("SuperAdmin Creation")
        print("="*60)

        # Check for environment variables first
        env_username = os.getenv('SUPERADMIN_USERNAME')
        env_email = os.getenv('SUPERADMIN_EMAIL')
        env_password = os.getenv('SUPERADMIN_PASSWORD')

        if env_username and env_email and env_password:
            # Use environment variables
            print("Using SuperAdmin credentials from environment variables...")
            username = env_username
            email = env_email
            password = env_password
            first_name = os.getenv('SUPERADMIN_FIRST_NAME', 'Super')
            last_name = os.getenv('SUPERADMIN_LAST_NAME', 'Admin')
        else:
            # Interactive mode
            print("No SuperAdmin credentials found in environment variables.")
            print("Please provide SuperAdmin details:\n")

            # Username
            while True:
                username = input("Username: ").strip()
                if len(username) < 3:
                    print("[ERROR] Username must be at least 3 characters long.")
                    continue
                if ' ' in username:
                    print("[ERROR] Username cannot contain spaces.")
                    continue
                break

            # Email
            while True:
                email = input("Email: ").strip()
                if not validate_email(email):
                    print("[ERROR] Invalid email format.")
                    continue
                break

            # Password
            while True:
                password = getpass.getpass("Password: ")
                if len(password) < 8:
                    print("[ERROR] Password must be at least 8 characters long.")
                    continue

                password_confirm = getpass.getpass("Confirm Password: ")
                if password != password_confirm:
                    print("[ERROR] Passwords do not match.")
                    continue
                break

            # Names
            first_name = input("First Name (default: Super): ").strip() or "Super"
            last_name = input("Last Name (default: Admin): ").strip() or "Admin"

        # Check if username or email already exists
        cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s",
                      (username, email))
        if cursor.fetchone():
            print(f"\n[ERROR] Username '{username}' or email '{email}' already exists.")
            cursor.close()
            conn.close()
            return

        # Get SuperAdmin role ID
        cursor.execute("SELECT id FROM roles WHERE name = 'SuperAdmin'")
        role_result = cursor.fetchone()

        if not role_result:
            print("\n[ERROR] SuperAdmin role not found in database.")
            cursor.close()
            conn.close()
            return

        superadmin_role_id = role_result['id']

        # Create the SuperAdmin user
        password_hash = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, first_name, last_name, role_id, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, TRUE)
            RETURNING id
        """, (username, email, password_hash, first_name, last_name, superadmin_role_id))

        user_id = cursor.fetchone()['id']
        conn.commit()
        cursor.close()
        conn.close()

        print(f"\n[SUCCESS] SuperAdmin user created successfully!")
        print(f"   User ID: {user_id}")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Name: {first_name} {last_name}")

    except Exception as e:
        print(f"\n[ERROR] Error creating SuperAdmin: {e}")
        print("You can create a SuperAdmin later using: python create_superadmin.py")

if __name__ == "__main__":
    print("="*60)
    print("Opinian Platform - Database Initialization")
    print("="*60)

    create_database()
    create_tables()
    update_schema()  # Add missing columns to existing tables
    insert_initial_data()
    create_indexes()

    print("\n" + "="*60)
    print("[SUCCESS] Database initialization completed successfully!")
    print("="*60)

    # Create SuperAdmin user
    create_superadmin()

    print("\n" + "="*60)
    print("Setup Complete!")
    print("="*60)
    print("\nYou can now start the application with:")
    print("  python app.py")
    print("\nThen navigate to: http://localhost:5000")
    print("="*60)