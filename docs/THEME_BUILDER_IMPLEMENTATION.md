# Advanced Theme Builder Implementation Plan
**Using GrapesJS Visual Editor Framework**

## Executive Summary
Transform the current basic theme creation system into a professional-grade visual theme builder that meets client requirements. The implementation will use GrapesJS, an open-source web builder framework, to provide drag-and-drop functionality, responsive design, and AI-powered theme generation.

---

## Current State Analysis

### Existing Implementation
- **Location**: `/themes/create`
- **Features**:
  - Simple color picker form (4 colors: primary, secondary, background, text)
  - Custom CSS text area
  - Basic live preview
  - Manual and AI creation modes (AI is mock only)

### Current Database Schema
```sql
themes table:
- id (SERIAL PRIMARY KEY)
- name (VARCHAR 100)
- description (TEXT)
- css_variables (JSONB) -- Stores color config
- custom_css (TEXT) -- Custom CSS code
- created_by (FK to users)
- group_id (FK to groups)
- is_active (BOOLEAN)
- created_at, updated_at (TIMESTAMP)
```

### Limitations
❌ No visual page builder
❌ No component library
❌ No responsive design preview
❌ No HTML/React export
❌ No drag-and-drop functionality
❌ AI integration is placeholder only
❌ No asset/file management
❌ Limited to basic color customization

---

## Requirements (From REQUIREMENTS.md)

### 2.4 Theme Management - Required Features
1. **AI-Powered Theme Creation**
   - Prompt-based theme definition
   - Visual editor for theme customization
   - Group-specific theme application
   - Drag-and-drop component management

2. **Visual Editor Features**
   - Code view with HTML/React export
   - Table, form, and image insertion
   - File upload capabilities
   - Responsive design preview

3. **User Experience**
   - 1920s 'flapper' style mixed with 1940s 'noir' aesthetic
   - Intuitive navigation
   - Consistent design language

---

## Proposed Solution: GrapesJS Integration

### Why GrapesJS?
✅ **Open-source** - MIT Licensed, free for commercial use
✅ **Drag & Drop** - Visual component builder
✅ **Responsive** - Mobile/tablet/desktop preview modes
✅ **Code Editor** - Built-in HTML/CSS/JS editing
✅ **Plugin Ecosystem** - Forms, tables, custom blocks, etc.
✅ **Asset Manager** - Image/file upload handling
✅ **Storage API** - Easy integration with backend
✅ **Customizable** - Can match vintage aesthetic
✅ **Export Ready** - HTML/CSS/React export capability

### GrapesJS Core Features We'll Use
- **Canvas**: Visual editing area
- **Blocks**: Drag-and-drop components (text, images, forms, tables)
- **Style Manager**: Visual CSS editor
- **Trait Manager**: Component properties editor
- **Layer Manager**: Component hierarchy view
- **Asset Manager**: File/image upload system
- **Device Manager**: Responsive preview (mobile/tablet/desktop)
- **Commands**: Custom actions (save, export, AI generate)

---

## Implementation Plan

### PHASE 1: Foundation & Setup

#### 1.1 Database Schema Enhancement
**Modify themes table to support GrapesJS data:**

```sql
-- Add new columns to themes table
ALTER TABLE themes ADD COLUMN IF NOT EXISTS
    gjs_data JSONB DEFAULT NULL;  -- GrapesJS components/styles/pages

ALTER TABLE themes ADD COLUMN IF NOT EXISTS
    gjs_assets JSONB DEFAULT '[]'::jsonb;  -- Uploaded images/files

ALTER TABLE themes ADD COLUMN IF NOT EXISTS
    html_export TEXT DEFAULT NULL;  -- Generated HTML

ALTER TABLE themes ADD COLUMN IF NOT EXISTS
    react_export TEXT DEFAULT NULL;  -- Generated React code

ALTER TABLE themes ADD COLUMN IF NOT EXISTS
    theme_type VARCHAR(50) DEFAULT 'visual';  -- 'visual', 'ai_generated', 'manual'

ALTER TABLE themes ADD COLUMN IF NOT EXISTS
    ai_prompt TEXT DEFAULT NULL;  -- Original AI prompt if applicable

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_themes_group_id ON themes(group_id);
CREATE INDEX IF NOT EXISTS idx_themes_theme_type ON themes(theme_type);
```

#### 1.2 Static Assets Installation
**Add GrapesJS CDN or local files:**

```html
<!-- GrapesJS Core -->
<link rel="stylesheet" href="https://unpkg.com/grapesjs/dist/css/grapes.min.css">
<script src="https://unpkg.com/grapesjs"></script>

<!-- GrapesJS Plugins -->
<script src="https://unpkg.com/grapesjs-blocks-basic"></script>
<script src="https://unpkg.com/grapesjs-preset-webpage"></script>
<script src="https://unpkg.com/grapesjs-plugin-forms"></script>
<script src="https://unpkg.com/grapesjs-blocks-flexbox"></script>
<script src="https://unpkg.com/grapesjs-plugin-export"></script>
<script src="https://unpkg.com/grapesjs-component-countdown"></script>
<script src="https://unpkg.com/grapesjs-tabs"></script>
<script src="https://unpkg.com/grapesjs-custom-code"></script>
<script src="https://unpkg.com/grapesjs-typed"></script>
<script src="https://unpkg.com/grapesjs-tooltip"></script>
```

**Or install via npm (preferred for production):**
```bash
npm install grapesjs grapesjs-preset-webpage grapesjs-plugin-forms \
    grapesjs-blocks-flexbox grapesjs-plugin-export grapesjs-tabs \
    grapesjs-custom-code grapesjs-tooltip
```

#### 1.3 File Upload System
**Create media upload endpoint:**

```python
# routes/media.py (new file)
@bp.route('/upload', methods=['POST'])
@login_required
def upload_media():
    """Handle file uploads for theme builder"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Validate file type
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'}
    if not file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
        return jsonify({'error': 'Invalid file type'}), 400

    # Generate unique filename
    filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
    upload_path = os.path.join('static/uploads/themes', filename)

    # Save file
    file.save(upload_path)

    # Store in database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO media_files
        (filename, original_filename, file_path, file_size, mime_type, uploaded_by, group_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (filename, file.filename, upload_path,
          os.path.getsize(upload_path), file.content_type,
          session['user_id'], session.get('group_id')))

    media_id = cursor.fetchone()[0]
    conn.commit()

    return jsonify({
        'success': True,
        'url': f'/static/uploads/themes/{filename}',
        'id': media_id
    })
```

---

### PHASE 2: Visual Theme Builder Interface

#### 2.1 Create New Template: `templates/themes/visual_builder.html`

**Full GrapesJS Editor Implementation:**

```html
{% extends "base.html" %}

{% block head %}
<!-- GrapesJS Core -->
<link rel="stylesheet" href="https://unpkg.com/grapesjs/dist/css/grapes.min.css">

<!-- Custom Vintage Styling for GrapesJS -->
<style>
    /* Full-screen editor */
    #gjs-editor {
        height: calc(100vh - 100px);
        width: 100%;
    }

    /* Vintage aesthetic overlay for panels */
    .gjs-pn-panel {
        background: linear-gradient(135deg, #1a1a1a 0%, #2c2c2c 100%) !important;
        border: 2px solid #d4af37 !important;
        box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3) !important;
    }

    .gjs-pn-btn {
        color: #d4af37 !important;
        transition: all 0.3s ease;
    }

    .gjs-pn-btn:hover {
        background: rgba(212, 175, 55, 0.2) !important;
        transform: scale(1.1);
    }

    /* Canvas styling */
    .gjs-cv-canvas {
        background: #f5f5dc;
        border: 3px solid #d4af37;
    }

    /* Custom block categories styling */
    .gjs-block-category .gjs-title {
        background: #2c2c2c;
        color: #d4af37;
        font-family: 'Playfair Display', serif;
        border-bottom: 2px solid #d4af37;
    }

    .gjs-block {
        border: 2px solid #8b4513;
        background: #f5f5dc;
        transition: all 0.3s ease;
    }

    .gjs-block:hover {
        border-color: #d4af37;
        box-shadow: 0 4px 8px rgba(212, 175, 55, 0.4);
        transform: translateY(-2px);
    }
</style>
{% endblock %}

{% block content %}
<div class="theme-builder-header" style="background: linear-gradient(135deg, #1a1a1a 0%, #2c2c2c 100%); padding: 1rem; border-bottom: 3px solid #d4af37;">
    <div class="container mx-auto flex justify-between items-center">
        <div class="flex items-center space-x-4">
            <h1 class="text-2xl font-bold" style="color: #d4af37; font-family: 'Playfair Display', serif;">
                <i class="fas fa-palette"></i> Visual Theme Builder
            </h1>
            <input type="text" id="theme-name" placeholder="Theme Name"
                   class="vintage-input" value="{{ theme.name if theme else '' }}">
        </div>

        <div class="flex space-x-2">
            <button id="save-theme" class="vintage-button bg-green-600 hover:bg-green-700">
                <i class="fas fa-save"></i> Save Theme
            </button>
            <button id="export-html" class="vintage-button bg-blue-600 hover:bg-blue-700">
                <i class="fas fa-code"></i> Export HTML
            </button>
            <button id="export-react" class="vintage-button bg-purple-600 hover:bg-purple-700">
                <i class="fab fa-react"></i> Export React
            </button>
            <button id="preview-theme" class="vintage-button bg-yellow-600 hover:bg-yellow-700">
                <i class="fas fa-eye"></i> Preview
            </button>
            <a href="{{ url_for('themes.index') }}" class="vintage-button bg-gray-600 hover:bg-gray-700">
                <i class="fas fa-times"></i> Close
            </a>
        </div>
    </div>
</div>

<!-- GrapesJS Editor Container -->
<div id="gjs-editor"></div>

<!-- Scripts -->
<script src="https://unpkg.com/grapesjs"></script>
<script src="https://unpkg.com/grapesjs-blocks-basic"></script>
<script src="https://unpkg.com/grapesjs-preset-webpage"></script>
<script src="https://unpkg.com/grapesjs-plugin-forms"></script>
<script src="https://unpkg.com/grapesjs-blocks-flexbox"></script>
<script src="https://unpkg.com/grapesjs-plugin-export"></script>
<script src="https://unpkg.com/grapesjs-tabs"></script>
<script src="https://unpkg.com/grapesjs-custom-code"></script>

<script>
// Initialize GrapesJS
const editor = grapesjs.init({
    container: '#gjs-editor',
    fromElement: false,
    height: '100%',
    width: 'auto',
    storageManager: false, // We'll handle storage via backend

    // Load existing theme data
    components: {{ (theme.gjs_data.components | tojson) if theme and theme.gjs_data else '[]' }},
    style: {{ (theme.gjs_data.styles | tojson) if theme and theme.gjs_data else '[]' }},

    // Canvas settings
    canvas: {
        styles: [
            // Include your base CSS
            '/static/css/vintage-theme.css'
        ],
        scripts: []
    },

    // Device Manager - Responsive preview
    deviceManager: {
        devices: [
            {
                name: 'Desktop',
                width: '',
            },
            {
                name: 'Tablet',
                width: '768px',
                widthMedia: '992px',
            },
            {
                name: 'Mobile',
                width: '320px',
                widthMedia: '480px',
            }
        ]
    },

    // Plugins configuration
    plugins: [
        'gjs-blocks-basic',
        'gjs-preset-webpage',
        'gjs-plugin-forms',
        'gjs-blocks-flexbox',
        'gjs-plugin-export',
        'gjs-tabs',
        'gjs-custom-code'
    ],

    pluginsOpts: {
        'gjs-preset-webpage': {
            blocks: ['column1', 'column2', 'column3', 'text', 'link', 'image', 'video'],
            modalImportTitle: 'Import Template',
            modalImportLabel: '<div style="margin-bottom: 10px; font-size: 13px;">Paste your HTML/CSS here</div>',
            modalImportContent: function(editor) {
                return editor.getHtml() + '<style>' + editor.getCss() + '</style>';
            },
        },
        'gjs-plugin-forms': {
            blocks: ['form', 'input', 'textarea', 'select', 'button', 'label', 'checkbox', 'radio']
        },
        'gjs-blocks-flexbox': {},
        'gjs-plugin-export': {}
    },

    // Block Manager - Custom blocks
    blockManager: {
        appendTo: '#blocks',
        blocks: []
    },

    // Asset Manager - File uploads
    assetManager: {
        upload: '/media/upload',
        uploadName: 'file',
        multiUpload: true,
        assets: {{ (theme.gjs_assets | tojson) if theme and theme.gjs_assets else '[]' }},
        uploadFile: function(e) {
            const files = e.dataTransfer ? e.dataTransfer.files : e.target.files;
            const formData = new FormData();

            for(let i = 0; i < files.length; i++) {
                formData.append('file', files[i]);
            }

            fetch('/media/upload', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    editor.AssetManager.add({
                        src: data.url,
                        name: files[0].name
                    });
                }
            });
        }
    },

    // Panels configuration
    panels: {
        defaults: [
            {
                id: 'panel-devices',
                el: '.panel__devices',
                buttons: [
                    {
                        id: 'device-desktop',
                        label: '<i class="fas fa-desktop"></i>',
                        command: 'set-device-desktop',
                        active: true,
                        togglable: false,
                    },
                    {
                        id: 'device-tablet',
                        label: '<i class="fas fa-tablet-alt"></i>',
                        command: 'set-device-tablet',
                        togglable: false,
                    },
                    {
                        id: 'device-mobile',
                        label: '<i class="fas fa-mobile-alt"></i>',
                        command: 'set-device-mobile',
                        togglable: false,
                    }
                ]
            },
            {
                id: 'panel-switcher',
                el: '.panel__switcher',
                buttons: [
                    {
                        id: 'show-blocks',
                        active: true,
                        label: '<i class="fas fa-cubes"></i>',
                        command: 'show-blocks',
                        togglable: false,
                    },
                    {
                        id: 'show-layers',
                        label: '<i class="fas fa-layer-group"></i>',
                        command: 'show-layers',
                        togglable: false,
                    },
                    {
                        id: 'show-styles',
                        label: '<i class="fas fa-paint-brush"></i>',
                        command: 'show-styles',
                        togglable: false,
                    }
                ]
            }
        ]
    }
});

// Add custom vintage-themed blocks
editor.BlockManager.add('vintage-header', {
    label: 'Vintage Header',
    category: 'Vintage Components',
    content: `
        <header style="background: linear-gradient(135deg, #1a1a1a 0%, #2c2c2c 100%);
                       padding: 2rem; border-bottom: 3px solid #d4af37;">
            <h1 style="color: #d4af37; font-family: 'Playfair Display', serif; font-size: 3rem; text-align: center;">
                Your Vintage Title
            </h1>
        </header>
    `,
    attributes: { class: 'fa fa-header' }
});

editor.BlockManager.add('art-deco-card', {
    label: 'Art Deco Card',
    category: 'Vintage Components',
    content: `
        <div style="background: #f5f5dc; border: 2px solid #d4af37; padding: 2rem;
                    box-shadow: 0 8px 16px rgba(0,0,0,0.3); margin: 1rem;">
            <h3 style="color: #1a1a1a; font-family: 'Playfair Display', serif; margin-bottom: 1rem;">
                Card Title
            </h3>
            <p style="color: #2c2c2c; font-family: 'Source Sans Pro', sans-serif;">
                Your content here...
            </p>
        </div>
    `,
    attributes: { class: 'fa fa-id-card' }
});

editor.BlockManager.add('noir-button', {
    label: 'Noir Button',
    category: 'Vintage Components',
    content: `
        <button style="background: linear-gradient(135deg, #1a1a1a 0%, #2c2c2c 100%);
                       color: #d4af37; padding: 1rem 2rem; border: 2px solid #d4af37;
                       font-family: 'Playfair Display', serif; font-size: 1.2rem; cursor: pointer;
                       box-shadow: 0 4px 8px rgba(212, 175, 55, 0.3); transition: all 0.3s;">
            Click Me
        </button>
    `,
    attributes: { class: 'fa fa-hand-pointer' }
});

editor.BlockManager.add('vintage-table', {
    label: 'Vintage Table',
    category: 'Vintage Components',
    content: `
        <table style="width: 100%; border-collapse: collapse; font-family: 'Source Sans Pro', sans-serif;">
            <thead>
                <tr style="background: #1a1a1a; color: #d4af37; border-bottom: 3px solid #d4af37;">
                    <th style="padding: 1rem; text-align: left;">Column 1</th>
                    <th style="padding: 1rem; text-align: left;">Column 2</th>
                    <th style="padding: 1rem; text-align: left;">Column 3</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom: 1px solid #8b4513;">
                    <td style="padding: 0.75rem;">Data 1</td>
                    <td style="padding: 0.75rem;">Data 2</td>
                    <td style="padding: 0.75rem;">Data 3</td>
                </tr>
            </tbody>
        </table>
    `,
    attributes: { class: 'fa fa-table' }
});

// Commands
editor.Commands.add('set-device-desktop', {
    run: editor => editor.setDevice('Desktop')
});
editor.Commands.add('set-device-tablet', {
    run: editor => editor.setDevice('Tablet')
});
editor.Commands.add('set-device-mobile', {
    run: editor => editor.setDevice('Mobile')
});

// Save theme function
document.getElementById('save-theme').addEventListener('click', async function() {
    const themeName = document.getElementById('theme-name').value;
    if (!themeName) {
        alert('Please enter a theme name');
        return;
    }

    const themeData = {
        name: themeName,
        description: 'Visual theme created with GrapesJS',
        gjs_data: {
            components: editor.getComponents(),
            styles: editor.getStyle(),
            html: editor.getHtml(),
            css: editor.getCss()
        },
        gjs_assets: editor.AssetManager.getAll(),
        html_export: editor.getHtml(),
        theme_type: 'visual'
    };

    const url = {{ ('"/themes/update/" + theme.id|string') if theme else '"/themes/visual-save"' }};

    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(themeData)
    });

    const result = await response.json();
    if (result.success) {
        alert('Theme saved successfully!');
        window.location.href = '/themes';
    } else {
        alert('Error saving theme: ' + result.message);
    }
});

// Export HTML
document.getElementById('export-html').addEventListener('click', function() {
    const html = '<!DOCTYPE html>\n<html>\n<head>\n<style>\n' +
                 editor.getCss() +
                 '\n</style>\n</head>\n<body>\n' +
                 editor.getHtml() +
                 '\n</body>\n</html>';

    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'theme-export.html';
    a.click();
});

// Export React (simplified conversion)
document.getElementById('export-react').addEventListener('click', function() {
    const html = editor.getHtml();
    const css = editor.getCss();

    // Basic HTML to JSX conversion
    const jsx = html
        .replace(/class=/g, 'className=')
        .replace(/for=/g, 'htmlFor=')
        .replace(/style="([^"]*)"/g, (match, styles) => {
            const styleObj = styles.split(';')
                .filter(s => s.trim())
                .map(s => {
                    const [key, value] = s.split(':').map(x => x.trim());
                    const camelKey = key.replace(/-([a-z])/g, g => g[1].toUpperCase());
                    return `${camelKey}: '${value}'`;
                })
                .join(', ');
            return `style={{${styleObj}}}`;
        });

    const reactComponent = `
import React from 'react';

// Styles
const styles = \`${css}\`;

function ThemeComponent() {
    return (
        <>
            <style>{\styles}</style>
            ${jsx}
        </>
    );
}

export default ThemeComponent;
`;

    const blob = new Blob([reactComponent], { type: 'text/javascript' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ThemeComponent.jsx';
    a.click();
});

// Preview
document.getElementById('preview-theme').addEventListener('click', function() {
    const previewHtml = '<!DOCTYPE html>\n<html>\n<head>\n<style>\n' +
                        editor.getCss() +
                        '\n</style>\n</head>\n<body>\n' +
                        editor.getHtml() +
                        '\n</body>\n</html>';

    const previewWindow = window.open('', '_blank');
    previewWindow.document.write(previewHtml);
    previewWindow.document.close();
});
</script>
{% endblock %}
```

#### 2.2 Update Routes: `routes/themes.py`

**Add new routes:**

```python
@bp.route('/visual-builder', methods=['GET'])
@bp.route('/visual-builder/<int:theme_id>', methods=['GET'])
@login_required
@role_required(['SuperAdmin', 'Admin'])
def visual_builder(theme_id=None):
    """Visual theme builder with GrapesJS"""
    theme = None

    if theme_id:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM themes WHERE id = %s", (theme_id,))
        theme = cursor.fetchone()
        cursor.close()
        conn.close()

        if not theme:
            flash('Theme not found', 'danger')
            return redirect(url_for('themes.index'))

        # Permission check
        if session['user_role'] == 'Admin' and theme['group_id'] != session.get('group_id'):
            flash('Permission denied', 'danger')
            return redirect(url_for('themes.index'))

    return render_template('themes/visual_builder.html', theme=theme)


@bp.route('/visual-save', methods=['POST'])
@login_required
@role_required(['SuperAdmin', 'Admin'])
def visual_save():
    """Save theme from visual builder"""
    try:
        data = request.get_json()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO themes
            (name, description, gjs_data, gjs_assets, html_export,
             theme_type, created_by, group_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data['name'],
            data.get('description', ''),
            json.dumps(data['gjs_data']),
            json.dumps(data.get('gjs_assets', [])),
            data.get('html_export', ''),
            data.get('theme_type', 'visual'),
            session['user_id'],
            session.get('group_id')
        ))

        theme_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()

        log_user_activity(session['user_id'], 'create_visual_theme', 'theme', theme_id)

        return jsonify({'success': True, 'theme_id': theme_id})

    except Exception as e:
        logger.error(f"Error saving visual theme: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/update/<int:theme_id>', methods=['POST'])
@login_required
@role_required(['SuperAdmin', 'Admin'])
def update_theme(theme_id):
    """Update existing theme from visual builder"""
    try:
        data = request.get_json()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE themes
            SET name = %s, description = %s, gjs_data = %s,
                gjs_assets = %s, html_export = %s, updated_at = %s
            WHERE id = %s
        """, (
            data['name'],
            data.get('description', ''),
            json.dumps(data['gjs_data']),
            json.dumps(data.get('gjs_assets', [])),
            data.get('html_export', ''),
            datetime.utcnow(),
            theme_id
        ))

        conn.commit()
        cursor.close()
        conn.close()

        log_user_activity(session['user_id'], 'update_visual_theme', 'theme', theme_id)

        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Error updating theme: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
```

---

### PHASE 3: AI-Powered Theme Generation

#### 3.1 AI Integration Setup

**Update routes/themes.py - Enhanced AI creation:**

```python
from openai import OpenAI  # or your preferred AI service

@bp.route('/ai-generate', methods=['POST'])
@login_required
@role_required(['SuperAdmin', 'Admin'])
def ai_generate_theme():
    """Generate theme using AI from natural language prompt"""
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        theme_name = data.get('name')

        # Get AI API key from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT setting_value FROM api_settings
            WHERE setting_key = 'openai_api_key'
        """)
        api_key_row = cursor.fetchone()

        if not api_key_row:
            return jsonify({'success': False, 'message': 'AI API not configured'}), 400

        # Initialize AI client
        client = OpenAI(api_key=api_key_row[0])

        # Create AI prompt for theme generation
        system_prompt = """You are a professional web designer specializing in vintage 1920s-1940s aesthetics.
Generate GrapesJS-compatible HTML components and CSS based on the user's description.
Return a JSON object with:
{
    "components": [...],  // GrapesJS component tree
    "styles": [...],      // CSS rules
    "description": "...", // Theme description
    "css_variables": {    // Color palette
        "primary_color": "#...",
        "secondary_color": "#...",
        ...
    }
}
Use Art Deco patterns, vintage colors (gold #d4af37, noir black #1a1a1a, beige #f5f5dc),
and period-appropriate typography (Playfair Display, Source Sans Pro)."""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create a theme: {prompt}"}
            ],
            response_format={ "type": "json_object" }
        )

        ai_result = json.loads(response.choices[0].message.content)

        # Save AI-generated theme
        cursor.execute("""
            INSERT INTO themes
            (name, description, gjs_data, css_variables, ai_prompt,
             theme_type, created_by, group_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            theme_name,
            ai_result.get('description', ''),
            json.dumps({
                'components': ai_result.get('components', []),
                'styles': ai_result.get('styles', [])
            }),
            json.dumps(ai_result.get('css_variables', {})),
            prompt,
            'ai_generated',
            session['user_id'],
            session.get('group_id')
        ))

        theme_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()

        log_user_activity(session['user_id'], 'ai_generate_theme', 'theme', theme_id)

        return jsonify({
            'success': True,
            'theme_id': theme_id,
            'data': ai_result
        })

    except Exception as e:
        logger.error(f"AI theme generation error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
```

#### 3.2 Create AI Theme Generator UI: `templates/themes/ai_builder.html`

```html
{% extends "base.html" %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    <div class="max-w-4xl mx-auto">
        <h1 class="text-4xl font-bold mb-6" style="color: #1a1a1a; font-family: 'Playfair Display', serif;">
            <i class="fas fa-magic mr-3 text-purple-600"></i>AI Theme Generator
        </h1>

        <div class="vintage-card p-8">
            <form id="ai-theme-form">
                <div class="mb-6">
                    <label class="block text-sm font-semibold text-gray-700 mb-2">
                        Theme Name
                    </label>
                    <input type="text" id="theme-name" class="vintage-input w-full"
                           placeholder="e.g., Gatsby Gala Theme" required>
                </div>

                <div class="mb-6">
                    <label class="block text-sm font-semibold text-gray-700 mb-2">
                        Describe Your Vision
                    </label>
                    <textarea id="ai-prompt" rows="6" class="vintage-input w-full"
                              placeholder="Describe the theme you want to create. Be specific about colors, style, mood, and purpose.

Example: 'Create an elegant 1920s speakeasy theme with dark backgrounds, gold accents, and art deco patterns. Include a hero section with vintage typography, a services grid with ornate borders, and a contact form with noir styling.'"
                              required></textarea>
                    <p class="text-xs text-gray-500 mt-2">
                        The more detailed your description, the better the AI-generated theme will match your vision.
                    </p>
                </div>

                <div class="mb-6 p-4 bg-yellow-50 border-2 border-yellow-400 rounded">
                    <h4 class="font-bold mb-2 text-yellow-800">
                        <i class="fas fa-lightbulb mr-2"></i>Tips for Best Results:
                    </h4>
                    <ul class="text-sm text-yellow-900 space-y-1 list-disc list-inside">
                        <li>Specify the era: 1920s flapper, 1940s noir, Art Deco, etc.</li>
                        <li>Mention key colors: gold, black, beige, burgundy, etc.</li>
                        <li>Describe sections: header, hero, features, gallery, footer</li>
                        <li>Include functionality: forms, buttons, cards, tables</li>
                        <li>Define mood: elegant, mysterious, vibrant, sophisticated</li>
                    </ul>
                </div>

                <div id="loading-indicator" class="hidden mb-6 p-4 bg-blue-50 border-2 border-blue-400 rounded text-center">
                    <i class="fas fa-spinner fa-spin text-3xl text-blue-600 mb-2"></i>
                    <p class="text-blue-800 font-semibold">AI is crafting your theme...</p>
                    <p class="text-sm text-blue-600">This may take 15-30 seconds</p>
                </div>

                <div class="flex justify-between items-center">
                    <a href="{{ url_for('themes.index') }}" class="text-gray-600 hover:text-gray-800">
                        <i class="fas fa-arrow-left mr-1"></i>Back
                    </a>
                    <button type="submit" class="vintage-button bg-purple-600 hover:bg-purple-700">
                        <i class="fas fa-wand-magic mr-2"></i>Generate Theme
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

<script>
document.getElementById('ai-theme-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const themeName = document.getElementById('theme-name').value;
    const prompt = document.getElementById('ai-prompt').value;
    const loadingIndicator = document.getElementById('loading-indicator');
    const submitButton = e.target.querySelector('button[type="submit"]');

    // Show loading
    loadingIndicator.classList.remove('hidden');
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Generating...';

    try {
        const response = await fetch('/themes/ai-generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: themeName,
                prompt: prompt
            })
        });

        const result = await response.json();

        if (result.success) {
            // Redirect to visual builder with AI-generated theme
            window.location.href = `/themes/visual-builder/${result.theme_id}`;
        } else {
            alert('Error: ' + result.message);
            loadingIndicator.classList.add('hidden');
            submitButton.disabled = false;
            submitButton.innerHTML = '<i class="fas fa-wand-magic mr-2"></i>Generate Theme';
        }
    } catch (error) {
        alert('Error generating theme: ' + error.message);
        loadingIndicator.classList.add('hidden');
        submitButton.disabled = false;
        submitButton.innerHTML = '<i class="fas fa-wand-magic mr-2"></i>Generate Theme';
    }
});
</script>
{% endblock %}
```

---

### PHASE 4: Enhanced Features

#### 4.1 Responsive Design Preview
- Already included in GrapesJS device manager
- Desktop/Tablet/Mobile preview modes
- Real-time responsive testing

#### 4.2 Component Library
**Custom vintage blocks included:**
- Vintage Header
- Art Deco Card
- Noir Button
- Vintage Table
- Flapper Form
- Gallery Grid
- Testimonial Section

#### 4.3 Export Functionality
**Supported formats:**
1. **HTML Export** - Complete HTML + CSS file
2. **React Export** - JSX component with styles
3. **WordPress Export** (future) - Theme files
4. **JSON Export** - GrapesJS format for backup

#### 4.4 Theme Preview & Testing
**Add preview route:**

```python
@bp.route('/live-preview/<int:theme_id>')
def live_preview(theme_id):
    """Render theme in full-page preview"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM themes WHERE id = %s", (theme_id,))
    theme = cursor.fetchone()
    cursor.close()
    conn.close()

    if not theme or not theme.get('gjs_data'):
        return "Theme not found", 404

    gjs_data = theme['gjs_data']
    html = gjs_data.get('html', '')
    css = gjs_data.get('css', '')

    preview_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{theme['name']} - Preview</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            {css}
        </style>
    </head>
    <body>
        {html}
    </body>
    </html>
    """

    return preview_html
```

---

### PHASE 5: Navigation & UX Updates

#### 5.1 Update Theme Index Page

**Modify `templates/themes/index.html` to include new builder options:**

```html
<!-- Add to theme index -->
<div class="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
    <a href="{{ url_for('themes.visual_builder') }}"
       class="vintage-card p-6 text-center hover:shadow-2xl transition-all border-2 border-transparent hover:border-purple-600">
        <i class="fas fa-magic text-5xl text-purple-600 mb-3"></i>
        <h3 class="text-xl font-bold mb-2">Visual Builder</h3>
        <p class="text-sm text-gray-600">Drag & drop theme creation with GrapesJS</p>
    </a>

    <a href="{{ url_for('themes.ai_create_theme') }}"
       class="vintage-card p-6 text-center hover:shadow-2xl transition-all border-2 border-transparent hover:border-blue-600">
        <i class="fas fa-robot text-5xl text-blue-600 mb-3"></i>
        <h3 class="text-xl font-bold mb-2">AI Generator</h3>
        <p class="text-sm text-gray-600">Describe your vision, let AI build it</p>
    </a>

    <a href="{{ url_for('themes.create_theme') }}"
       class="vintage-card p-6 text-center hover:shadow-2xl transition-all border-2 border-transparent hover:border-green-600">
        <i class="fas fa-code text-5xl text-green-600 mb-3"></i>
        <h3 class="text-xl font-bold mb-2">Manual Creation</h3>
        <p class="text-sm text-gray-600">Traditional CSS-based theme builder</p>
    </a>
</div>
```

#### 5.2 Add Theme Actions

**Update theme cards with new actions:**

```html
<!-- For each theme in the list -->
<div class="theme-actions flex space-x-2">
    <a href="{{ url_for('themes.visual_builder', theme_id=theme.id) }}"
       class="vintage-button-sm bg-purple-600">
        <i class="fas fa-edit"></i> Edit Visually
    </a>
    <a href="{{ url_for('themes.live_preview', theme_id=theme.id) }}"
       target="_blank" class="vintage-button-sm bg-blue-600">
        <i class="fas fa-eye"></i> Preview
    </a>
    <button onclick="exportTheme({{ theme.id }})"
            class="vintage-button-sm bg-green-600">
        <i class="fas fa-download"></i> Export
    </button>
</div>
```

---

## Implementation Timeline & Effort Estimates

### Phase 1: Foundation (2-3 days)
- [ ] Database schema updates
- [ ] GrapesJS assets installation
- [ ] File upload system setup
- [ ] Media routes creation

### Phase 2: Visual Builder (3-4 days)
- [ ] Create visual_builder.html template
- [ ] Configure GrapesJS with all plugins
- [ ] Add custom vintage components
- [ ] Implement save/update routes
- [ ] Test responsive preview

### Phase 3: AI Integration (2-3 days)
- [ ] Set up AI service integration
- [ ] Create AI prompt engineering
- [ ] Build AI generator UI
- [ ] Test AI theme generation
- [ ] Refine AI output formatting

### Phase 4: Enhanced Features (2-3 days)
- [ ] Export functionality (HTML/React)
- [ ] Live preview system
- [ ] Component library expansion
- [ ] Asset management testing

### Phase 5: UX & Polish (1-2 days)
- [ ] Update navigation
- [ ] Theme index redesign
- [ ] Documentation
- [ ] User testing

**Total Estimated Time: 10-15 days**

---

## Testing Checklist

### Functional Testing
- [ ] Create theme via visual builder
- [ ] Edit existing theme
- [ ] Save and load GrapesJS data correctly
- [ ] Upload images/files via asset manager
- [ ] Generate theme with AI prompt
- [ ] Export HTML with correct structure
- [ ] Export React component
- [ ] Preview theme in different devices
- [ ] Apply theme to group
- [ ] Delete theme with cleanup

### Permission Testing
- [ ] SuperAdmin can access all themes
- [ ] Admin can only access group themes
- [ ] SuperUser can view but not edit
- [ ] User cannot access theme builder

### Performance Testing
- [ ] Large theme saves (500+ components)
- [ ] Multiple image uploads
- [ ] Real-time preview performance
- [ ] AI generation timeout handling

### Browser Compatibility
- [ ] Chrome
- [ ] Firefox
- [ ] Safari
- [ ] Edge

---

## Security Considerations

### Input Validation
- Validate file uploads (type, size, malware)
- Sanitize AI-generated HTML/CSS
- Prevent XSS in custom CSS
- Rate limit AI requests

### Access Control
- Enforce group-based isolation
- Verify theme ownership on edit/delete
- Protect media files by group
- Audit all theme operations

### Data Protection
- Encrypt AI API keys in database
- Sanitize export downloads
- Limit export file sizes
- Prevent code injection

---

## Migration Strategy

### For Existing Themes
```sql
-- Add new columns with defaults
ALTER TABLE themes ADD COLUMN IF NOT EXISTS
    gjs_data JSONB DEFAULT NULL;

-- Migrate old themes to new format
UPDATE themes
SET gjs_data = jsonb_build_object(
    'components', '[]',
    'styles', '[]',
    'html', '<div>Legacy theme</div>',
    'css', custom_css
)
WHERE gjs_data IS NULL AND theme_type IS NULL;

-- Set theme type for existing themes
UPDATE themes
SET theme_type = 'manual'
WHERE theme_type IS NULL;
```

### Backwards Compatibility
- Keep existing manual theme creation
- Support old `css_variables` format
- Gradual migration of legacy themes

---

## Future Enhancements

### Version 2.0 Features
- [ ] Multi-page theme support (header/footer templates)
- [ ] Theme marketplace/sharing
- [ ] Version control for themes
- [ ] A/B testing for themes
- [ ] Analytics integration
- [ ] Dark mode toggle
- [ ] Accessibility checker
- [ ] SEO optimization tools

### Advanced AI Features
- [ ] AI theme variations generator
- [ ] Natural language editing ("make the header bigger")
- [ ] Automatic responsive optimization
- [ ] Brand color extraction from logo
- [ ] Competitor theme analysis

### Collaboration Features
- [ ] Multi-user editing (real-time)
- [ ] Comment system on components
- [ ] Theme approval workflow
- [ ] Revision history

---

## Documentation Requirements

### User Documentation
1. **User Guide**: "Creating Themes with Visual Builder"
2. **Video Tutorial**: 5-minute walkthrough
3. **AI Prompt Examples**: Best practices for AI generation
4. **Component Library**: Documentation of all blocks
5. **Export Guide**: How to use exported code

### Developer Documentation
1. **GrapesJS Customization Guide**
2. **API Endpoints Reference**
3. **Database Schema Documentation**
4. **Plugin Development Guide**
5. **Troubleshooting Guide**

---

## Success Metrics

### Key Performance Indicators
- Theme creation time: < 10 minutes (vs 30+ minutes manual)
- User satisfaction: > 90% positive feedback
- AI accuracy: > 80% usable without major edits
- Export success rate: > 95%
- Performance: Page load < 2 seconds with 100+ components

### Adoption Metrics
- Number of themes created via visual builder
- AI vs manual theme creation ratio
- Average components per theme
- Export format usage distribution
- Mobile vs desktop editing split

---

## Conclusion

This implementation plan transforms the basic theme creation system into a professional-grade visual theme builder that:

✅ Meets all client requirements from REQUIREMENTS.md
✅ Uses industry-standard GrapesJS framework
✅ Provides AI-powered theme generation
✅ Supports responsive design preview
✅ Enables HTML/React export
✅ Maintains vintage aesthetic
✅ Ensures security and multi-tenancy
✅ Scales for future enhancements

**Next Steps:**
1. Review and approve this implementation plan
2. Set up development environment with GrapesJS
3. Begin Phase 1: Foundation work
4. Schedule regular progress reviews
5. Plan user acceptance testing

---

**Document Version:** 1.0
**Last Updated:** 2025-12-02
**Status:** Ready for Implementation
