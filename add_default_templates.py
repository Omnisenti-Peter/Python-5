#!/usr/bin/env python3
"""
Add default page templates to existing database
"""

import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def add_default_templates():
    """Insert default page templates"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'opinian'),
            port=os.getenv('DB_PORT', '5432')
        )
        cursor = conn.cursor()

        print("Adding default page templates...")

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

        # Check how many templates were added
        cursor.execute("SELECT COUNT(*) FROM templates WHERE is_default = TRUE")
        count = cursor.fetchone()[0]

        print(f"[SUCCESS] Default templates added successfully!")
        print(f"   Total default templates in database: {count}")

        # List all templates
        cursor.execute("SELECT id, name, description FROM templates ORDER BY id")
        templates = cursor.fetchall()

        print("\n[TEMPLATES] Available templates:")
        for template in templates:
            print(f"   ID: {template[0]} - {template[1]}")
            if template[2]:
                print(f"      {template[2]}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"[ERROR] Error adding default templates: {e}")
        return False

    return True

if __name__ == "__main__":
    print("="*60)
    print("Adding Default Page Templates")
    print("="*60)
    print()

    if add_default_templates():
        print("\n" + "="*60)
        print("[SUCCESS] Templates added successfully!")
        print("="*60)
        print("\nYou can now select templates when creating pages.")
    else:
        print("\n" + "="*60)
        print("[ERROR] Failed to add templates")
        print("="*60)
