# Theme Usage Guide - Where Themes Are Applied

## 🎨 What is a Theme?

A **theme** is the visual design (colors, fonts, layout) for your organization's website. When you create and apply a theme, it controls how your pages and blog posts look to visitors.

---

## 📍 Where Are Themes Used?

### **1. Organization/Group Level**
- Each **organization (group)** has one active theme
- Stored in database: `groups.theme_id`
- All pages/blogs for that group use this theme

### **2. Public-Facing Pages**
When applied, the theme affects:

✅ **Blog Posts** (`/blog/*`)
- Blog list pages
- Individual blog post pages
- Blog categories

✅ **Custom Pages** (`/page/*`)
- About Us page
- Contact Us page
- Any custom pages created

✅ **User Profiles** (`/profile/*`)
- Public user profiles
- Author pages

✅ **Landing Pages**
- Group/organization home page
- Portfolio pages

---

## 🔄 How Theme Application Works

### **Current Implementation:**

```
Step 1: Create Theme
  └─> User builds theme in visual builder
  └─> Saves to database (themes table)

Step 2: Apply Theme
  └─> User clicks "Apply Theme" button
  └─> Updates groups.theme_id = theme.id
  └─> Theme is now "active"

Step 3: Theme is Used (Next Steps)
  └─> Blog/page templates load active theme
  └─> CSS and HTML from theme applied
  └─> Visitors see the custom design
```

---

## 💾 Database Structure

### **themes table:**
```sql
- id (primary key)
- name (theme name)
- gjs_data (JSONB: HTML/CSS/components)
- html_export (generated HTML)
- css_variables (JSON: colors, fonts)
- theme_type (visual/ai_generated/manual)
- group_id (which organization owns this)
```

### **groups table:**
```sql
- id (primary key)
- name (organization name)
- theme_id (FK to themes.id) ← Active theme!
```

### **Relationship:**
```
Group (Organization)
  └─> has ONE active theme_id
  └─> can have MANY themes created
  └─> only ONE is "applied" at a time
```

---

## 🎯 Implementation Status

### ✅ **What's Working Now:**

1. ✅ Theme creation (visual builder)
2. ✅ Theme saving to database
3. ✅ Apply theme (updates groups.theme_id)
4. ✅ Theme list and management
5. ✅ Preview themes

### ⏳ **What Needs Implementation:**

To actually USE the active theme on pages, you need to:

#### **Step 1: Load Active Theme in Templates**

Add this to your base template or page routes:

```python
# In routes/blog.py or routes/pages.py
@bp.route('/blog/<slug>')
def view_post(slug):
    # Get blog post
    post = get_blog_post(slug)

    # Get active theme for this group
    active_theme = get_active_theme(post['group_id'])

    # Pass to template
    return render_template('blog/view.html',
                          post=post,
                          theme=active_theme)
```

#### **Step 2: Helper Function to Get Active Theme**

```python
# In app.py or utils.py
def get_active_theme(group_id):
    """Get the active theme for a group"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT t.* FROM themes t
        JOIN groups g ON g.theme_id = t.id
        WHERE g.id = %s AND t.is_active = TRUE
    """, (group_id,))

    theme = cursor.fetchone()
    cursor.close()
    conn.close()

    return theme
```

#### **Step 3: Apply Theme in Template**

In your Jinja2 template (`blog/view.html`):

```html
{% extends "base.html" %}

{% block head %}
    <!-- Apply theme CSS -->
    {% if theme and theme.gjs_data %}
    <style>
        {{ theme.gjs_data.css | safe }}

        /* Apply theme colors */
        {% if theme.css_variables %}
        :root {
            --primary-color: {{ theme.css_variables.primary_color }};
            --secondary-color: {{ theme.css_variables.secondary_color }};
            --background-color: {{ theme.css_variables.background_color }};
            --text-color: {{ theme.css_variables.text_color }};
        }
        {% endif %}
    </style>
    {% endif %}
{% endblock %}

{% block content %}
    <!-- Your blog post content -->
    <article>
        <h1>{{ post.title }}</h1>
        <div class="content">{{ post.content | safe }}</div>
    </article>
{% endblock %}
```

---

## 📝 Example: Full Implementation

### **Create Theme Wrapper Function**

```python
# In app.py
@app.context_processor
def inject_theme():
    """Inject active theme into all templates"""
    theme = None

    if 'group_id' in session:
        group_id = session['group_id']
        theme = get_active_theme(group_id)

    return {'active_theme': theme}
```

### **Update Base Template**

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}Opinian{% endblock %}</title>

    <!-- Default styles -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/default.css') }}">

    <!-- Apply active theme if exists -->
    {% if active_theme %}
    <style>
        /* Theme CSS from visual builder */
        {{ active_theme.gjs_data.css | safe if active_theme.gjs_data else '' }}

        /* Theme color variables */
        {% if active_theme.css_variables %}
        :root {
            --primary: {{ active_theme.css_variables.primary_color | default('#1a1a1a') }};
            --secondary: {{ active_theme.css_variables.secondary_color | default('#d4af37') }};
            --bg: {{ active_theme.css_variables.background_color | default('#f5f5dc') }};
            --text: {{ active_theme.css_variables.text_color | default('#2c2c2c') }};
        }

        body {
            background-color: var(--bg);
            color: var(--text);
        }

        .btn-primary {
            background-color: var(--primary);
            color: var(--secondary);
        }
        {% endif %}
    </style>
    {% endif %}

    {% block head %}{% endblock %}
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>
```

---

## 🎬 Real-World Flow

### **Admin Creates Theme:**
```
1. Admin logs in
2. Goes to /themes
3. Clicks "Visual Builder"
4. Drags components (header, cards, buttons)
5. Customizes colors, text, images
6. Clicks "Save Theme"
   └─> Theme saved to database
   └─> theme_type = 'visual'
   └─> group_id = admin's group
```

### **Admin Applies Theme:**
```
1. Admin sees theme in list at /themes
2. Clicks "Apply Theme" button
3. System updates: groups.theme_id = this_theme_id
4. Success message: "Theme is now active!"
```

### **Visitors See Theme:**
```
1. Visitor goes to /blog/my-awesome-post
2. System checks: what is the group_id for this post?
3. System loads: active theme for that group_id
4. Template renders with:
   ├─> Theme CSS applied
   ├─> Theme colors used
   ├─> Theme fonts loaded
   └─> Custom layout from theme
5. Visitor sees beautiful custom design!
```

---

## 🔧 Quick Implementation (20 minutes)

Want to make themes work right now? Follow these steps:

### **1. Add Helper Function** (5 min)
```python
# In app.py after get_db_connection()
def get_active_theme(group_id):
    if not group_id:
        return None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT t.* FROM themes t
            JOIN groups g ON g.theme_id = t.id
            WHERE g.id = %s
        """, (group_id,))
        theme = cursor.fetchone()
        cursor.close()
        conn.close()
        return theme
    except:
        return None
```

### **2. Add Context Processor** (5 min)
```python
# In app.py before route definitions
@app.context_processor
def inject_active_theme():
    theme = None
    if 'group_id' in session:
        theme = get_active_theme(session['group_id'])
    return {'active_theme': theme}
```

### **3. Update Base Template** (10 min)
```html
<!-- In templates/base.html <head> section -->
{% if active_theme and active_theme.gjs_data %}
<style>
    {{ active_theme.gjs_data.css | safe if active_theme.gjs_data.css else '' }}
</style>
{% endif %}
```

### **4. Test It!**
```
1. Create a theme
2. Apply it
3. Visit any page in your organization
4. See the theme in action!
```

---

## 🎨 What Users See

### **Before Applying Theme:**
- Default platform styling
- Standard colors (black, white, gray)
- Basic layout
- Generic appearance

### **After Applying Theme:**
- Custom header with organization colors
- Branded cards and buttons
- Custom fonts (Playfair Display, Source Sans Pro)
- Unique vintage aesthetic
- Professional, polished look
- Organization's identity visible

---

## 📊 Theme Scope

### **Multi-Tenant Isolation:**

```
Group A (Company ABC)
  └─> Theme: "ABC Corporate Blue"
  └─> All ABC's pages use this theme
  └─> ABC visitors see blue theme

Group B (Company XYZ)
  └─> Theme: "XYZ Vintage Gold"
  └─> All XYZ's pages use this theme
  └─> XYZ visitors see gold theme

✅ Completely isolated!
✅ Each organization has unique branding
✅ No mixing between groups
```

---

## 💡 Key Takeaways

1. **Purpose:** Themes provide custom branding for each organization

2. **Scope:** One active theme per organization/group

3. **Application:** Updates `groups.theme_id` in database

4. **Usage:** Templates load and apply the active theme CSS/HTML

5. **Isolation:** Each group's theme only affects their content

6. **Flexibility:** Can change themes anytime by applying a different one

7. **Preview:** Can preview before applying

8. **Rollback:** Can revert by applying previous theme

---

## 🚀 Next Steps

To fully implement theme usage:

1. ✅ Fix apply_theme to show proper message (DONE!)
2. ⏳ Add `get_active_theme()` helper function
3. ⏳ Add context processor to inject theme
4. ⏳ Update base.html to use theme CSS
5. ⏳ Test on blog posts and pages
6. ⏳ Add theme preview on actual pages
7. ⏳ Document for users

---

**Summary:** Themes control the visual appearance of your organization's public-facing pages. When you apply a theme, it updates the database to mark that theme as active, and templates use that theme's CSS and design when rendering pages for visitors.
