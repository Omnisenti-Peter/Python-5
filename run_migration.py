"""
Database migration script for GrapesJS theme builder
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    try:
        # Database connection
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'opinian_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '')
        )

        cursor = conn.cursor()

        # Read and execute migration
        with open('migrations/001_add_grapesjs_columns.sql', 'r') as f:
            migration_sql = f.read()
            cursor.execute(migration_sql)

        conn.commit()
        print('[OK] Database migration completed successfully')

        # Verify columns were added
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'themes'
            AND column_name IN ('gjs_data', 'gjs_assets', 'html_export', 'react_export', 'theme_type', 'ai_prompt')
            ORDER BY column_name
        """)

        print('\nNew columns added to themes table:')
        for row in cursor.fetchall():
            print(f'  - {row[0]}: {row[1]}')

        cursor.close()
        conn.close()

    except Exception as e:
        print(f'Error running migration: {e}')
        raise

if __name__ == '__main__':
    run_migration()
