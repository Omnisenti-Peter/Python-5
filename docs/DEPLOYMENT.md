# Opinian Platform - Deployment Guide

## Overview
This guide provides detailed instructions for deploying the Opinian SaaS Blogging Platform in various environments.

## Deployment Options

### 1. Local Development

#### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Git

#### Steps
```bash
# Clone repository
git clone <repository-url>
cd opinian

# Run setup script
python setup.py

# Edit .env file with your configuration
nano .env

# Start the application
python run.py
```

### 2. Production Server (Linux)

#### Prerequisites
- Ubuntu 20.04+ or CentOS 8+
- Python 3.8+
- PostgreSQL 12+
- Nginx (optional)
- Supervisor (optional)

#### Steps

1. **Update system packages**
```bash
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
sudo yum update -y  # CentOS/RHEL
```

2. **Install PostgreSQL**
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib -y

# CentOS/RHEL
sudo yum install postgresql-server postgresql-contrib -y
sudo postgresql-setup --initdb
```

3. **Configure PostgreSQL**
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql
CREATE DATABASE opinian_prod;
CREATE USER opinian_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE opinian_prod TO opinian_user;
\q
```

4. **Install Python and dependencies**
```bash
sudo apt install python3-pip python3-venv python3-dev -y
sudo apt install build-essential libpq-dev -y
```

5. **Setup application**
```bash
# Create application user
sudo useradd -m -s /bin/bash opinian
sudo su - opinian

# Clone and setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with production settings
```

6. **Configure environment variables**
```bash
# Example .env for production
FLASK_ENV=production
SECRET_KEY=your_very_secure_secret_key
DB_HOST=localhost
DB_NAME=opinian_prod
DB_USER=opinian_user
DB_PASSWORD=your_secure_password
```

7. **Initialize database**
```bash
python init_db.py
```

8. **Setup Gunicorn**
```bash
pip install gunicorn

cat > gunicorn_config.py << 'EOF'
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2
preload_app = True
user = "opinian"
group = "opinian"
EOF
```

9. **Setup Supervisor (optional)**
```bash
sudo apt install supervisor -y

sudo tee /etc/supervisor/conf.d/opinian.conf > /dev/null <<EOF
[program:opinian]
directory=/home/opinian/opinian
command=/home/opinian/opinian/venv/bin/gunicorn --config gunicorn_config.py run:app
user=opinian
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/opinian/opinian/logs/gunicorn.log
environment=PATH="/home/opinian/opinian/venv/bin",VIRTUAL_ENV="/home/opinian/opinian/venv"
EOF

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start opinian
```

10. **Setup Nginx (optional)**
```bash
sudo apt install nginx -y

sudo tee /etc/nginx/sites-available/opinian > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;
    
    client_max_body_size 10M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static {
        alias /home/opinian/opinian/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /uploads {
        alias /home/opinian/opinian/uploads;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/opinian /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3. Docker Deployment

#### Dockerfile
```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads logs

# Set permissions
RUN chmod +x run.py setup.py

# Expose port
EXPOSE 5000

# Run application
CMD ["python", "run.py"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: opinian
      POSTGRES_USER: opinian_user
      POSTGRES_PASSWORD: your_secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DB_HOST=db
      - DB_NAME=opinian
      - DB_USER=opinian_user
      - DB_PASSWORD=your_secure_password
    depends_on:
      - db
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs

volumes:
  postgres_data:
```

#### Deploy with Docker Compose
```bash
# Build and start
docker-compose up -d

# Initialize database
docker-compose exec app python init_db.py

# View logs
docker-compose logs -f app
```

### 4. Cloud Deployment

#### AWS ECS
```json
{
  "family": "opinian-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "opinian",
      "image": "your-registry/opinian:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "FLASK_ENV",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:opinian/secret-key"
        }
      ]
    }
  ]
}
```

#### Google Cloud Run
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: opinian
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/cpu-throttling: "false"
    spec:
      containers:
      - image: gcr.io/PROJECT-ID/opinian:latest
        ports:
        - containerPort: 5000
        env:
        - name: FLASK_ENV
          value: production
        resources:
          limits:
            cpu: "1"
            memory: "512Mi"
```

## Security Considerations

### 1. Environment Variables
```bash
# Generate secure keys
openssl rand -hex 32  # For SECRET_KEY
openssl rand -hex 32  # For JWT_SECRET_KEY

# Set proper permissions
chmod 600 .env
chown opinian:opinian .env
```

### 2. Database Security
```sql
-- Create read-only user for backup
CREATE USER backup_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE opinian_prod TO backup_user;
GRANT USAGE ON SCHEMA public TO backup_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_user;

-- Enable SSL connections
-- Add to postgresql.conf:
ssl = on
ssl_cert_file = 'server.crt'
ssl_key_file = 'server.key'
```

### 3. Application Security
```python
# config.py additions for production
class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    
    # Security headers
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = "redis://localhost:6379"
```

### 4. SSL/TLS with Let's Encrypt
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Monitoring and Logging

### 1. Application Logging
```python
# Add to app.py
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/opinian.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
```

### 2. Health Checks
```python
# Add health check endpoint
@app.route('/health')
def health_check():
    try:
        # Check database connection
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            cursor.close()
            conn.close()
            return jsonify({'status': 'healthy'}), 200
        else:
            return jsonify({'status': 'unhealthy', 'reason': 'database'}), 503
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'reason': str(e)}), 503
```

### 3. Monitoring with Prometheus
```python
# Install prometheus-client
pip install prometheus-client

# Add metrics endpoint
from prometheus_client import Counter, Histogram, generate_latest

request_count = Counter('opinian_requests_total', 'Total requests')
request_duration = Histogram('opinian_request_duration_seconds', 'Request duration')

@app.route('/metrics')
def metrics():
    return generate_latest()
```

## Backup and Recovery

### 1. Database Backup
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/var/backups/opinian"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="opinian_prod"
DB_USER="opinian_user"

mkdir -p $BACKUP_DIR

# Database backup
pg_dump -U $DB_USER -d $DB_NAME -f $BACKUP_DIR/db_backup_$DATE.sql

# Uploads backup
tar -czf $BACKUP_DIR/uploads_backup_$DATE.tar.gz /home/opinian/opinian/uploads/

# Cleanup old backups (keep last 7 days)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

### 2. Automated Backups
```bash
# Add to crontab
0 2 * * * /home/opinian/backup.sh
```

## Performance Optimization

### 1. Database Optimization
```sql
-- Add indexes for common queries
CREATE INDEX idx_blog_posts_published ON blog_posts(is_published);
CREATE INDEX idx_blog_posts_group_id ON blog_posts(group_id);
CREATE INDEX idx_blog_posts_created_at ON blog_posts(created_at);
CREATE INDEX idx_users_group_id ON users(group_id);
```

### 2. Caching with Redis
```python
# Install redis-py
pip install redis

# Add caching
import redis
from functools import wraps

cache = redis.Redis(host='localhost', port=6379, decode_responses=True)

def cached(timeout=300):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = f"cache:{f.__name__}:{hash(str(args) + str(kwargs))}"
            result = cache.get(cache_key)
            if result is not None:
                return json.loads(result)
            result = f(*args, **kwargs)
            cache.setex(cache_key, timeout, json.dumps(result))
            return result
        return decorated_function
    return decorator
```

### 3. Static File Optimization
```nginx
# Nginx configuration for static files
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    add_header X-Content-Type-Options "nosniff";
}
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL is running: `sudo systemctl status postgresql`
   - Verify credentials in .env file
   - Check firewall settings

2. **Permission Denied Errors**
   - Ensure correct file permissions: `chown -R opinian:opinian /home/opinian/opinian`
   - Check SELinux settings if on CentOS

3. **Gunicorn Workers Crashing**
   - Check logs: `tail -f logs/gunicorn.log`
   - Increase worker timeout in gunicorn_config.py
   - Verify database connection

4. **Static Files Not Loading**
   - Check Nginx configuration
   - Verify static file permissions
   - Ensure DEBUG=False in production

### Log Locations
- Application logs: `logs/opinian.log`
- Gunicorn logs: `logs/gunicorn.log`
- Nginx access logs: `/var/log/nginx/access.log`
- Nginx error logs: `/var/log/nginx/error.log`
- PostgreSQL logs: `/var/log/postgresql/`

## Scaling Considerations

### 1. Horizontal Scaling
- Use load balancer (AWS ALB, NGINX)
- Session storage in Redis
- Shared file storage (AWS S3, NFS)
- Database read replicas

### 2. Vertical Scaling
- Increase server resources
- Optimize database queries
- Add caching layers
- Use CDN for static assets

### 3. Auto-scaling
```yaml
# AWS Auto Scaling Group
Resources:
  AutoScalingGroup:
    Type: AWS::AutoScaling::AutoScalingGroup
    Properties:
      MinSize: 2
      MaxSize: 10
      DesiredCapacity: 2
      HealthCheckType: ELB
      HealthCheckGracePeriod: 300
      TargetGroupARNs:
        - !Ref TargetGroup
```

## Support

For deployment support:
- Check application logs
- Review system requirements
- Test database connectivity
- Verify environment configuration
- Consult troubleshooting section

For additional help, contact support@opinian.com