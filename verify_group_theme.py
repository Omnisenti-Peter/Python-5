#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verification script to check group membership and theme application
Run this to verify which users belong to which groups
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'opinian'),
            port=os.getenv('DB_PORT', '5432')
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def verify_group_membership():
    """Verify group membership and theme assignments"""
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database")
        return

    cursor = conn.cursor(cursor_factory=RealDictCursor)

    print("\n" + "="*80)
    print("GROUP MEMBERSHIP AND THEME VERIFICATION")
    print("="*80 + "\n")

    # Get all groups with their themes
    cursor.execute("""
        SELECT
            g.id as group_id,
            g.name as group_name,
            g.theme_id,
            t.name as theme_name,
            t.theme_type,
            COUNT(u.id) as member_count
        FROM groups g
        LEFT JOIN themes t ON g.theme_id = t.id
        LEFT JOIN users u ON u.group_id = g.id
        WHERE g.is_active = TRUE
        GROUP BY g.id, g.name, g.theme_id, t.name, t.theme_type
        ORDER BY g.name
    """)

    groups = cursor.fetchall()

    print("📊 GROUPS OVERVIEW:")
    print("-" * 80)
    for group in groups:
        print(f"\n🏢 Group: {group['group_name']} (ID: {group['group_id']})")
        print(f"   👥 Members: {group['member_count']}")
        if group['theme_id']:
            print(f"   🎨 Theme: {group['theme_name']} ({group['theme_type']})")
        else:
            print(f"   🎨 Theme: None (using default)")
        print("-" * 80)

    # Get detailed member list for each group
    print("\n\n📋 DETAILED MEMBERSHIP BY GROUP:")
    print("="*80)

    for group in groups:
        print(f"\n🏢 Group: {group['group_name']}")
        print("-" * 80)

        cursor.execute("""
            SELECT
                u.id,
                u.username,
                u.email,
                u.first_name,
                u.last_name,
                u.role,
                u.is_active,
                u.group_id
            FROM users u
            WHERE u.group_id = %s
            ORDER BY u.role, u.username
        """, (group['group_id'],))

        members = cursor.fetchall()

        if members:
            for member in members:
                status = "✅ Active" if member['is_active'] else "❌ Inactive"
                print(f"   👤 {member['username']} ({member['role']}) - {member['email']} - {status}")
        else:
            print("   ⚠️  No members in this group!")

    # Check for users not in any group
    print("\n\n⚠️  USERS NOT IN ANY GROUP:")
    print("="*80)

    cursor.execute("""
        SELECT
            u.id,
            u.username,
            u.email,
            u.role,
            u.group_id
        FROM users u
        WHERE u.group_id IS NULL OR u.group_id NOT IN (SELECT id FROM groups WHERE is_active = TRUE)
        ORDER BY u.role, u.username
    """)

    orphan_users = cursor.fetchall()

    if orphan_users:
        for user in orphan_users:
            print(f"   👤 {user['username']} ({user['role']}) - Email: {user['email']}")
            print(f"      Group ID: {user['group_id']} (may be invalid)")
    else:
        print("   ✅ All users belong to active groups!")

    # Check theme application logic
    print("\n\n🎨 THEME APPLICATION LOGIC:")
    print("="*80)
    print("Theme is applied based on: session['group_id']")
    print("When a user logs in, their user.group_id is stored in session['group_id']")
    print("The get_active_theme() function loads the theme assigned to that group")
    print("\nFor multi-tenant theming to work:")
    print("  1. User must have group_id set in users table")
    print("  2. That group must have theme_id set in groups table")
    print("  3. When user logs in, session['group_id'] = user.group_id")
    print("  4. Theme loads from: SELECT * FROM themes WHERE id = (SELECT theme_id FROM groups WHERE id = session['group_id'])")

    cursor.close()
    conn.close()

    print("\n" + "="*80)
    print("VERIFICATION COMPLETE")
    print("="*80 + "\n")

if __name__ == '__main__':
    verify_group_membership()
