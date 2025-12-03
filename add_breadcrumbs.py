#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to add breadcrumbs to admin and theme templates
"""

import os
import sys
import re

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Template breadcrumb configurations
BREADCRUMB_CONFIGS = {
    'templates/admin/manage_users.html': [
        ('Home', "url_for('index')"),
        ('Admin', "url_for('admin.dashboard')"),
        ('Manage Users', None)
    ],
    'templates/admin/manage_groups.html': [
        ('Home', "url_for('index')"),
        ('Admin', "url_for('admin.dashboard')"),
        ('Manage Groups', None)
    ],
    'templates/admin/create_user.html': [
        ('Home', "url_for('index')"),
        ('Admin', "url_for('admin.dashboard')"),
        ('Users', "url_for('admin.manage_users')"),
        ('Create User', None)
    ],
    'templates/admin/edit_user.html': [
        ('Home', "url_for('index')"),
        ('Admin', "url_for('admin.dashboard')"),
        ('Users', "url_for('admin.manage_users')"),
        ('Edit User', None)
    ],
    'templates/admin/create_group.html': [
        ('Home', "url_for('index')"),
        ('Admin', "url_for('admin.dashboard')"),
        ('Groups', "url_for('admin.manage_groups')"),
        ('Create Group', None)
    ],
    'templates/admin/edit_group.html': [
        ('Home', "url_for('index')"),
        ('Admin', "url_for('admin.dashboard')"),
        ('Groups', "url_for('admin.manage_groups')"),
        ('Edit Group', None)
    ],
    'templates/admin/view_group.html': [
        ('Home', "url_for('index')"),
        ('Admin', "url_for('admin.dashboard')"),
        ('Groups', "url_for('admin.manage_groups')"),
        ('View Group', None)
    ],
    'templates/themes/index.html': [
        ('Home', "url_for('index')"),
        ('Theme Studio', None)
    ],
    'templates/themes/create.html': [
        ('Home', "url_for('index')"),
        ('Themes', "url_for('themes.index')"),
        ('Create Theme', None)
    ],
    'templates/themes/edit.html': [
        ('Home', "url_for('index')"),
        ('Themes', "url_for('themes.index')"),
        ('Edit Theme', None)
    ],
    'templates/themes/ai_create.html': [
        ('Home', "url_for('index')"),
        ('Themes', "url_for('themes.index')"),
        ('AI Assistant', None)
    ],
    'templates/dashboard.html': [
        ('Home', "url_for('index')"),
        ('Dashboard', None)
    ],
    'templates/blog/my_posts.html': [
        ('Home', "url_for('index')"),
        ('Dashboard', "url_for('dashboard')"),
        ('My Posts', None)
    ],
    'templates/blog/create_post.html': [
        ('Home', "url_for('index')"),
        ('Dashboard', "url_for('dashboard')"),
        ('My Posts', "url_for('blog.my_posts')"),
        ('Create Post', None)
    ],
    'templates/blog/edit_post.html': [
        ('Home', "url_for('index')"),
        ('Dashboard', "url_for('dashboard')"),
        ('My Posts', "url_for('blog.my_posts')"),
        ('Edit Post', None)
    ],
}

def generate_breadcrumb_code(crumbs):
    """Generate the breadcrumb Jinja2 code"""
    code_lines = ["{% set breadcrumbs = make_breadcrumbs("]

    for i, crumb in enumerate(crumbs):
        name, url = crumb
        if url is None:
            line = f"    ('{name}', None)"
        else:
            line = f"    ('{name}', {url})"

        if i < len(crumbs) - 1:
            line += ","
        code_lines.append(line)

    code_lines.append(") %}")
    return "\n".join(code_lines)

def add_breadcrumbs_to_template(filepath, breadcrumbs):
    """Add breadcrumbs to a template file"""
    if not os.path.exists(filepath):
        print(f"⚠️  File not found: {filepath}")
        return False

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if breadcrumbs already exist
    if 'breadcrumbs = make_breadcrumbs' in content:
        print(f"✓ Breadcrumbs already exist: {filepath}")
        return True

    # Generate breadcrumb code
    breadcrumb_code = generate_breadcrumb_code(breadcrumbs)

    # Find the position to insert breadcrumbs (after title block, before content block)
    pattern = r'({% block title %}.*?{% endblock %})\s*\n\s*\n({% block content %})'

    if re.search(pattern, content, re.DOTALL):
        # Insert breadcrumbs between title and content
        new_content = re.sub(
            pattern,
            r'\1\n\n' + breadcrumb_code + r'\n\n\2',
            content,
            flags=re.DOTALL
        )

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"✅ Added breadcrumbs: {filepath}")
        return True
    else:
        print(f"❌ Could not find insertion point: {filepath}")
        return False

def main():
    """Main function to add breadcrumbs to all templates"""
    print("="*60)
    print("Adding Breadcrumb Navigation to Templates")
    print("="*60 + "\n")

    success_count = 0
    skip_count = 0
    fail_count = 0

    for filepath, breadcrumbs in BREADCRUMB_CONFIGS.items():
        result = add_breadcrumbs_to_template(filepath, breadcrumbs)
        if result:
            success_count += 1
        elif 'already exist' in str(result):
            skip_count += 1
        else:
            fail_count += 1

    print("\n" + "="*60)
    print("Summary:")
    print(f"✅ Success: {success_count}")
    print(f"⏭️  Skipped: {skip_count}")
    print(f"❌ Failed: {fail_count}")
    print("="*60)

if __name__ == '__main__':
    main()
