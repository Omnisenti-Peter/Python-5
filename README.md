# Opinian - SaaS Blogging Platform

A sophisticated multi-tenant blogging platform with 1920s flapper and 1940s noir aesthetic, featuring AI-powered content creation and customizable themes.

## Features

### 🎨 Design & User Experience
- **Vintage Aesthetic**: 1920s flapper style mixed with 1940s noir design
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Customizable Themes**: AI-powered theme generation and visual editor
- **Rich Text Editor**: WYSIWYG editor with media support

### 👥 User Management
- **Multi-Tenant Architecture**: Organizations can create branded environments
- **4-Tier Role System**:
  - **SuperAdmin**: Full platform administration, manage all groups/organizations
  - **Admin**: Group management and user creation within their organization
  - **SuperUser**: Extended content creation capabilities (pages and posts)
  - **User**: Basic blogging and reading
- **Multiple User Creation Methods**:
  - SuperAdmin creation via script (one-time setup)
  - Admin panel user creation (any role)
  - Public self-registration (creates User role)
- **User Permissions Dashboard**: Matrix view of all users with editable permissions
- **Activity Logging**: Comprehensive audit trail of user actions

> 📖 **Detailed guide**: See [USER_MANAGEMENT.md](USER_MANAGEMENT.md) for complete user creation workflows

### ✍️ Content Management
- **Blog Posts**: Create, edit, and publish articles with rich media
- **Static Pages**: Create custom pages (About, Contact, etc.)
- **AI Writing Assistant**: Generate and enhance content using AI
- **Media Management**: Upload and organize images and files
- **Content Moderation**: Built-in moderation tools and approval workflows

### 🛠️ Administration
- **User Management**: Create, edit, ban, and manage user permissions
- **Group/Organization Management**: Multi-tenant isolation and branding
- **Theme Management**: Create and apply custom themes per organization
- **API Settings**: Configure external API integrations
- **System Monitoring**: Activity logs and performance metrics

### 🔧 Technical Features
- **RESTful API**: Full API access for frontend integration
- **JWT Authentication**: Secure token-based authentication
- **Database**: PostgreSQL with optimized queries
- **File Uploads**: Secure file handling with type validation
- **Error Handling**: Comprehensive error logging and user feedback

## Technology Stack

### Backend
- **Python 3.8+** with Flask framework
- **PostgreSQL** database
- **JWT** for authentication
- **SQLAlchemy** for database operations
- **Bcrypt** for password hashing

### Frontend
- **HTML5** with Jinja2 templating
- **Tailwind CSS** for styling
- **JavaScript** for interactivity
- **Font Awesome** for icons
- **Google Fonts** (Playfair Display, Source Sans Pro)

### External Services
- **LLM API** for AI content generation (configurable)
- **Email Services** for notifications (optional)

## Installation

### Prerequisites
- Python 3.8 or higher
- PostgreSQL 12 or higher
- Node.js (for development tools)

### Setup Steps

1. **Clone the repository**
```bash
git clone <repository-url>
cd opinian
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Setup database and create SuperAdmin**
```bash
python init_db.py
```
This will:
- Create database and tables
- Set up roles and permissions
- Prompt you to create the first SuperAdmin user
- You can provide credentials interactively or via environment variables

6. **Run the application**
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=opinian
DB_USER=postgres
DB_PASSWORD=your_password

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your_secret_key

# JWT Configuration
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ACCESS_TOKEN_EXPIRES=3600

# File Upload Configuration
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=10485760
ALLOWED_EXTENSIONS=png,jpg,jpeg,gif,webp

# API Configuration
LLM_API_KEY=your_llm_api_key
LLM_API_URL=https://api.example.com/v1

# Email Configuration (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_email_password

# SuperAdmin Creation (optional - for automated deployment)
# If not set, init_db.py will prompt interactively
SUPERADMIN_USERNAME=admin
SUPERADMIN_EMAIL=admin@example.com
SUPERADMIN_PASSWORD=your_secure_password
SUPERADMIN_FIRST_NAME=Super
SUPERADMIN_LAST_NAME=Admin
```

> **Note:** For security, SuperAdmin credentials via environment variables should only be used in automated deployment scenarios. For local development, use interactive mode.

## Usage

### First Time Setup

1. **Initialize database** - This creates tables, roles, and SuperAdmin
   ```bash
   python init_db.py
   ```
   - The script will prompt you to create the first SuperAdmin
   - Provide username, email, and secure password when prompted
   - Alternatively, set SuperAdmin credentials in `.env` for automated setup

2. **Log in as SuperAdmin** at `http://localhost:5000/login`

3. **Create Admin users** via `/admin/users/create`
   - Each Admin typically manages one organization/group

4. **Admins create their organizations** and configure:
   - Group name and description
   - Custom themes
   - About and Contact pages

5. **Admins create users** within their groups:
   - SuperUsers (can create pages and posts)
   - Regular Users (can create posts)

6. **Enable public registration** (optional)
   - Users can self-register at `/register`
   - Self-registered users get "User" role
   - Admins can later assign them to groups

> 📖 **For detailed workflows**, see [USER_MANAGEMENT.md](USER_MANAGEMENT.md) and [WORKFLOW.md](WORKFLOW.md)

### Creating Content

1. **Write Blog Posts**: Use the rich text editor or AI assistant
2. **Create Pages**: Build static pages for your organization
3. **Design Themes**: Use AI or visual editor for custom themes
4. **Manage Media**: Upload images and files for your content

### Administration

1. **User Management**: View and edit user permissions
2. **Content Moderation**: Review and approve posts
3. **Theme Management**: Create and apply themes
4. **System Monitoring**: View activity logs and statistics

## API Documentation

### Authentication

Login endpoint:
```http
POST /api/auth/login
Content-Type: application/json

{
    "username": "user@example.com",
    "password": "password"
}
```

Response:
```json
{
    "message": "Login successful",
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "user",
        "email": "user@example.com",
        "role": "User"
    }
}
```

### Blog Posts API

Get all posts:
```http
GET /api/blog/posts
Authorization: Bearer <token>
```

Create a post:
```http
POST /api/blog/posts
Authorization: Bearer <token>
Content-Type: application/json

{
    "title": "My Blog Post",
    "content": "Post content here...",
    "is_published": true
}
```

## Deployment

### Production Deployment

1. **Set environment to production**
```bash
export FLASK_ENV=production
export SECRET_KEY=your_production_secret_key
```

2. **Use a production WSGI server**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

3. **Configure reverse proxy** (Nginx example)
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /static {
        alias /path/to/opinian/static;
        expires 30d;
    }
}
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "run.py"]
```

## Security Considerations

- Change default secret keys in production
- Use HTTPS in production
- Configure proper database permissions
- Regular security updates
- Monitor user activity logs
- Implement rate limiting for API endpoints
- **Never commit `.env` file to git** (already in `.gitignore`)
- Use strong passwords for SuperAdmin (minimum 12 characters)
- Store production credentials in secrets manager (AWS Secrets, Azure Key Vault)

> 🔐 **Detailed security guide**: See [SECURITY.md](SECURITY.md) for credential management best practices

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the API documentation

## Roadmap

### Upcoming Features
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Advanced SEO tools
- [ ] Social media integration
- [ ] Mobile app
- [ ] Advanced AI features
- [ ] Plugin system
- [ ] Advanced caching

### Performance Improvements
- [ ] Redis caching
- [ ] CDN integration
- [ ] Image optimization
- [ ] Database query optimization

---

Built with ❤️ using Flask and PostgreSQL