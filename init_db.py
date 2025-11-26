#!/usr/bin/env python3
"""
Database initialization script for Opinian platform
Creates database tables and initial data
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
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
                created_by INTEGER,
                group_id INTEGER REFERENCES groups(id),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Update groups table to reference themes
        cursor.execute("""
            ALTER TABLE groups 
            ADD CONSTRAINT fk_groups_theme 
            FOREIGN KEY (theme_id) REFERENCES themes(id) 
            ON DELETE SET NULL
        """)
        
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
        cursor.execute("""
            ALTER TABLE groups 
            ADD CONSTRAINT fk_groups_admin 
            FOREIGN KEY (admin_user_id) REFERENCES users(id) 
            ON DELETE SET NULL
        """)
        
        # Update themes table to reference creator
        cursor.execute("""
            ALTER TABLE themes 
            ADD CONSTRAINT fk_themes_creator 
            FOREIGN KEY (created_by) REFERENCES users(id) 
            ON DELETE SET NULL
        """)
        
        # Update templates table to reference creator
        cursor.execute("""
            ALTER TABLE templates 
            ADD CONSTRAINT fk_templates_creator 
            FOREIGN KEY (created_by) REFERENCES users(id) 
            ON DELETE SET NULL
        """)
        
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
        print(f"Error creating tables: {e}")
        sys.exit(1)

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
        cursor.execute("""
            INSERT INTO roles (name, description, permissions) VALUES
            ('SuperAdmin', 'Full platform administration access', 
             '{"platform_manage": true, "user_manage": true, "content_manage": true, "theme_manage": true, "api_manage": true}'::jsonb),
            ('Admin', 'Group administration access', 
             '{"group_manage": true, "user_manage": true, "content_manage": true, "theme_manage": true}'::jsonb),
            ('SuperUser', 'Extended content creation access', 
             '{"content_create": true, "page_create": true, "theme_view": true}'::jsonb),
            ('User', 'Basic user access', 
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
            "CREATE INDEX IF NOT EXISTS idx_user_activity_logs_created_at ON user_activity_logs(created_at)"
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

if __name__ == "__main__":
    print("Starting database initialization...")
    create_database()
    create_tables()
    insert_initial_data()
    create_indexes()
    print("Database initialization completed successfully!")