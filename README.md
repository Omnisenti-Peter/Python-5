# Opinian - AI-Powered Blogging Platform

A vintage-styled blogging platform with 1920s/1940s noir aesthetic and AI-powered story enhancement capabilities.

## Features

- **User Authentication**: Secure registration and login system with password hashing
- **Blog Management**: Full CRUD operations for blog posts (Create, Read, Update, Delete)
- **AI Story Enhancement**: Real AI integration with OpenAI and Anthropic APIs to enhance your stories
- **Comments System**: Users can comment on blog posts
- **Like/Unlike**: Social engagement features for blog posts
- **Search & Filter**: Find posts by title, content, or author
- **Admin Panel**: Configure AI services and view platform statistics
- **Responsive Design**: Beautiful art deco/noir theme that works on all devices
- **Auto-Save Drafts**: Automatic local storage of unsaved work

## Tech Stack

- **Backend**: Flask (Python 3.8+)
- **Database**: SQLAlchemy with SQLite (can be configured for PostgreSQL/MySQL)
- **Authentication**: Flask-Login with Werkzeug password hashing
- **AI Integration**: OpenAI API, Anthropic Claude API
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Design**: 1920s Art Deco / 1940s Film Noir aesthetic

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- (Optional) Virtual environment tool

### Step 1: Clone or Download

Place all files in your project directory.

### Step 2: Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Copy the `.env.example` file to `.env`:

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

Edit the `.env` file and add your configuration:

```env
# Required
SECRET_KEY=your-secret-key-here-change-in-production

# Optional AI API Keys (can also be configured in admin panel)
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
```

To generate a secure secret key:

```python
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 5: Initialize Database

The database will be automatically created on first run. To create it manually:

```bash
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

### Step 6: Run the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Default Demo Accounts

The application comes with two pre-configured demo accounts:

- **Admin Account**:
  - Username: `admin`
  - Password: `admin123`
  - Has access to admin panel

- **Regular User**:
  - Username: `user`
  - Password: `user123`
  - Standard user account

**Important**: Change these passwords in production!

## AI Configuration

### Option 1: Environment Variables

Set your API keys in the `.env` file:

```env
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Option 2: Admin Panel

1. Log in with an admin account
2. Navigate to the Admin Panel
3. Enter your API keys in the AI Service Configuration section
4. Choose your preferred model
5. Adjust the creativity level (temperature)
6. Click "Save Configuration"

### Supported AI Models

**OpenAI:**
- GPT-4 (Most capable, higher cost)
- GPT-3.5 Turbo (Fast and cost-effective)

**Anthropic:**
- Claude 3 Opus (Most capable)
- Claude 3 Sonnet (Balanced)
- Claude 3 Haiku (Fast and efficient)

## Project Structure

```
html_flask/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── config.py              # Configuration settings
├── ai_service.py          # AI integration service
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── README.md             # This file
├── instance/             # Database and instance-specific files
│   └── opinian.db        # SQLite database (auto-created)
├── static/               # Static files
│   ├── css/
│   │   └── style.css     # Application styles
│   ├── js/
│   │   └── main.js       # Client-side JavaScript
│   └── uploads/          # User uploads (future feature)
└── templates/            # HTML templates
    ├── base.html         # Base template
    ├── index.html        # Homepage
    ├── post.html         # Single post view
    ├── write.html        # Blog writing page
    ├── edit.html         # Blog editing page
    ├── ai.html           # AI enhancement page
    └── admin.html        # Admin panel
```

## Usage Guide

### Writing a Blog Post

1. Log in to your account
2. Click "Write Blog" in the navigation
3. Enter your title and content
4. Click "Publish Story" to make it public or "Save Draft" to save privately

### Enhancing with AI

1. Go to "AI Assistant" page
2. Enter your rough draft or story ideas
3. Click "Enhance My Story"
4. Wait for AI to process (usually 5-10 seconds)
5. Review and edit the enhanced version
6. Click "Export to Blog" to create a new blog post with the enhanced content

### Managing Comments

- View comments on any published post
- Add comments when logged in
- Comments appear below the blog post content

### Using Search & Filter

- Enter keywords in the search box to find posts by title or content
- Use the author filter dropdown to see posts by specific authors
- Combine search and filter for precise results

## API Keys

### Getting OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Go to API Keys section
4. Create a new API key
5. Copy and add to your `.env` file or admin panel

### Getting Anthropic API Key

1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Go to API Keys section
4. Create a new API key
5. Copy and add to your `.env` file or admin panel

## Database Migration

### Using SQLite (Default)

No additional setup required. Database file is created automatically in `instance/opinian.db`.

### Using PostgreSQL

1. Install PostgreSQL
2. Create a database:
   ```sql
   CREATE DATABASE opinian;
   ```
3. Update `.env`:
   ```env
   DATABASE_URL=postgresql://username:password@localhost/opinian
   ```
4. Run the application (tables will be created automatically)

### Using MySQL

1. Install MySQL
2. Create a database:
   ```sql
   CREATE DATABASE opinian CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
3. Update `.env`:
   ```env
   DATABASE_URL=mysql://username:password@localhost/opinian
   ```
4. Run the application

## Production Deployment

### Security Checklist

- [ ] Change default admin password
- [ ] Generate a strong SECRET_KEY
- [ ] Use a production database (PostgreSQL recommended)
- [ ] Enable HTTPS
- [ ] Set `FLASK_ENV=production`
- [ ] Configure proper CORS settings
- [ ] Implement rate limiting
- [ ] Set up regular database backups
- [ ] Use environment variables for all sensitive data

### Recommended Production Setup

```bash
# Install production server
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using with Nginx

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /path/to/html_flask/static;
    }
}
```

## Troubleshooting

### Database Errors

**Error**: "Table doesn't exist"
**Solution**: Delete `instance/opinian.db` and restart the application

### AI Enhancement Not Working

**Error**: "AI services not configured"
**Solution**:
1. Check that you've added valid API keys in admin panel or `.env`
2. Verify your API keys are active and have credits
3. Check the console/logs for specific error messages

### Login Issues

**Error**: "Invalid username or password"
**Solution**:
1. Ensure you're using the correct credentials
2. Try the demo accounts (admin/admin123 or user/user123)
3. If you created a new account, verify you completed registration

### Port Already in Use

**Error**: "Address already in use"
**Solution**:
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :5000
kill -9 <PID>

# Or use a different port
python app.py --port 5001
```

## Contributing

This is a demo/educational project. Feel free to:
- Fork and modify for your needs
- Report bugs or issues
- Suggest new features
- Improve documentation

## License

This project is open source and available for educational and commercial use.

## Credits

- **Design Inspiration**: 1920s Art Deco and 1940s Film Noir aesthetics
- **Fonts**: Playfair Display, Source Sans Pro (Google Fonts)
- **Icons**: Font Awesome
- **AI**: OpenAI GPT, Anthropic Claude

## Support

For questions or issues:
1. Check this README
2. Review the troubleshooting section
3. Check the Flask and SQLAlchemy documentation
4. Review the AI provider documentation (OpenAI, Anthropic)

---

**Opinian** - *Where Words Find Their Voice*

"In the golden age of words, we find our voice"
