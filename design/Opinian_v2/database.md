# Opinian Platform - Database Schema Documentation

## Database Architecture Overview

The Opinian platform uses a comprehensive database schema designed to support blogging functionality, user management, AI integration, and analytics. The schema is organized into logical modules for maintainability and scalability.

## Core Tables Structure

### 1. Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    display_name VARCHAR(200),
    bio TEXT,
    avatar_url VARCHAR(500),
    role ENUM('admin', 'author', 'reader') DEFAULT 'reader',
    status ENUM('active', 'suspended', 'pending') DEFAULT 'pending',
    email_verified BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    preferences JSON,
    metadata JSON
);
```

**Indexes:**
- PRIMARY KEY: id
- UNIQUE: email, username
- INDEX: role, status, created_at
- FULLTEXT: first_name, last_name, display_name, bio

### 2. Blog Posts Table
```sql
CREATE TABLE blog_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    slug VARCHAR(600) UNIQUE NOT NULL,
    excerpt TEXT,
    content LONGTEXT NOT NULL,
    content_html LONGTEXT,
    featured_image VARCHAR(500),
    status ENUM('draft', 'published', 'archived') DEFAULT 'draft',
    visibility ENUM('public', 'private', 'password_protected') DEFAULT 'public',
    password VARCHAR(255),
    meta_title VARCHAR(500),
    meta_description VARCHAR(1000),
    meta_keywords VARCHAR(1000),
    canonical_url VARCHAR(500),
    reading_time INT,
    word_count INT,
    view_count BIGINT DEFAULT 0,
    like_count INT DEFAULT 0,
    comment_count INT DEFAULT 0,
    share_count INT DEFAULT 0,
    is_featured BOOLEAN DEFAULT FALSE,
    is_sticky BOOLEAN DEFAULT FALSE,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    scheduled_at TIMESTAMP,
    expires_at TIMESTAMP,
    tags JSON,
    categories JSON,
    custom_fields JSON,
    ai_assisted BOOLEAN DEFAULT FALSE,
    ai_prompts JSON,
    version INT DEFAULT 1,
    parent_id UUID REFERENCES blog_posts(id)
);
```

**Indexes:**
- PRIMARY KEY: id
- UNIQUE: slug
- INDEX: user_id, status, published_at, is_featured
- FULLTEXT: title, content, excerpt, meta_keywords
- INDEX: categories, tags (using JSON indexing)

### 3. Categories Table
```sql
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(250) UNIQUE NOT NULL,
    description TEXT,
    parent_id UUID REFERENCES categories(id),
    color VARCHAR(7),
    icon VARCHAR(100),
    post_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    metadata JSON
);
```

### 4. Tags Table
```sql
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(150) UNIQUE NOT NULL,
    description TEXT,
    color VARCHAR(7),
    post_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON
);
```

### 5. Media Files Table
```sql
CREATE TABLE media_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    filename VARCHAR(500) NOT NULL,
    original_name VARCHAR(500),
    mime_type VARCHAR(100),
    file_size BIGINT,
    file_hash VARCHAR(64),
    url VARCHAR(1000) NOT NULL,
    thumbnail_url VARCHAR(1000),
    alt_text VARCHAR(500),
    caption TEXT,
    description TEXT,
    dimensions JSON,
    metadata JSON,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX: user_id, mime_type, uploaded_at
);
```

### 6. Comments Table
```sql
CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID NOT NULL REFERENCES blog_posts(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    parent_id UUID REFERENCES comments(id) ON DELETE CASCADE,
    author_name VARCHAR(200),
    author_email VARCHAR(255),
    author_website VARCHAR(500),
    content TEXT NOT NULL,
    content_html TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    status ENUM('pending', 'approved', 'spam', 'trash') DEFAULT 'pending',
    like_count INT DEFAULT 0,
    dislike_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX: post_id, user_id, status, created_at
);
```

## AI Integration Tables

### 7. AI Prompts Table
```sql
CREATE TABLE ai_prompts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    description TEXT,
    prompt_template TEXT NOT NULL,
    variables JSON,
    model_config JSON,
    temperature DECIMAL(3,2) DEFAULT 0.7,
    max_tokens INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    version INT DEFAULT 1,
    usage_count INT DEFAULT 0,
    INDEX: category, is_active, created_at
);
```

### 8. AI Usage Logs Table
```sql
CREATE TABLE ai_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    prompt_id UUID REFERENCES ai_prompts(id),
    model_name VARCHAR(100),
    input_tokens INT,
    output_tokens INT,
    total_tokens INT,
    cost DECIMAL(10,6),
    request_data JSON,
    response_data JSON,
    status ENUM('success', 'error', 'timeout') DEFAULT 'success',
    error_message TEXT,
    processing_time INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX: user_id, prompt_id, created_at, status
);
```

### 9. LLM Configuration Table
```sql
CREATE TABLE llm_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(100) NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    endpoint_url VARCHAR(1000),
    additional_params JSON,
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    usage_limits JSON,
    cost_per_token DECIMAL(10,6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE: provider, model_name
);
```

## Analytics Tables

### 10. Analytics Events Table
```sql
CREATE TABLE analytics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_id VARCHAR(100),
    event_type VARCHAR(100) NOT NULL,
    event_category VARCHAR(100),
    event_action VARCHAR(100),
    event_label VARCHAR(500),
    page_url VARCHAR(1000),
    referrer_url VARCHAR(1000),
    user_agent TEXT,
    ip_address VARCHAR(45),
    geo_location JSON,
    device_info JSON,
    custom_data JSON,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX: user_id, event_type, timestamp, session_id
);
```

### 11. Page Views Table
```sql
CREATE TABLE page_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_id VARCHAR(100),
    page_url VARCHAR(1000) NOT NULL,
    page_title VARCHAR(500),
    post_id UUID REFERENCES blog_posts(id),
    referrer_url VARCHAR(1000),
    user_agent TEXT,
    ip_address VARCHAR(45),
    geo_location JSON,
    device_info JSON,
    time_on_page INT,
    scroll_depth INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX: user_id, post_id, timestamp, session_id
);
```

### 12. User Sessions Table
```sql
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_id VARCHAR(100) UNIQUE NOT NULL,
    user_agent TEXT,
    ip_address VARCHAR(45),
    geo_location JSON,
    device_info JSON,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX: user_id, session_id, last_activity
);
```

## System Tables

### 13. System Settings Table
```sql
CREATE TABLE system_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_name VARCHAR(200) UNIQUE NOT NULL,
    value TEXT,
    value_type ENUM('string', 'number', 'boolean', 'json') DEFAULT 'string',
    description TEXT,
    category VARCHAR(100),
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 14. Audit Logs Table
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(200) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    old_values JSON,
    new_values JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX: user_id, action, resource_type, created_at
);
```

## Relationships and Constraints

### Foreign Key Relationships
- **users → blog_posts**: One-to-Many (user can write many posts)
- **blog_posts → categories**: Many-to-Many (through JSON arrays)
- **blog_posts → tags**: Many-to-Many (through JSON arrays)
- **users → media_files**: One-to-Many (user can upload many files)
- **blog_posts → comments**: One-to-Many (post can have many comments)
- **users → comments**: One-to-Many (user can write many comments)
- **ai_prompts → ai_usage_logs**: One-to-Many (prompt can have many usage logs)

### Data Integrity Rules
1. **User Deletion**: Cascade delete user's blogs, comments, media
2. **Blog Deletion**: Cascade delete associated comments
3. **Category/Tag Updates**: Update post JSON arrays accordingly
4. **Media Cleanup**: Remove orphaned files from storage
5. **Analytics Retention**: Auto-delete old data after specified period

## Mock Data Examples

### Sample User Data
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "admin@opinian.com",
  "username": "admin",
  "display_name": "Administrator",
  "role": "admin",
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Sample Blog Post Data
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "The Art of Noir Storytelling in Modern Blogging",
  "slug": "noir-storytelling-modern-blogging",
  "content": "In the shadowy corners of the digital realm...",
  "status": "published",
  "categories": ["writing", "storytelling", "noir"],
  "tags": ["blogging", "style", "aesthetic"],
  "view_count": 15420,
  "ai_assisted": true,
  "published_at": "2024-01-15T10:30:00Z"
}
```

### Sample AI Prompt Data
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "name": "Blog Idea Generator",
  "category": "content-creation",
  "prompt_template": "Generate 5 unique blog post ideas about {topic} for a {style} blog. Include engaging titles and brief descriptions.",
  "variables": ["topic", "style"],
  "temperature": 0.8,
  "is_active": true
}
```

## Performance Optimization

### Indexing Strategy
1. **Primary Keys**: All tables use UUID primary keys for distributed compatibility
2. **Foreign Keys**: Indexed for join performance
3. **Search Fields**: Full-text indexes on title, content, and meta fields
4. **JSON Indexes**: Specialized indexes for JSON array fields (categories, tags)
5. **Timestamp Indexes**: For time-based queries and analytics
6. **Composite Indexes**: For complex queries involving multiple fields

### Partitioning Strategy
1. **Analytics Tables**: Partitioned by month for efficient data retention
2. **Audit Logs**: Partitioned by quarter for historical data management
3. **Media Files**: Partitioned by upload date for storage optimization

### Data Retention Policies
1. **Analytics Data**: Retain for 24 months, then archive
2. **Audit Logs**: Retain for 12 months, then archive
3. **User Sessions**: Retain for 30 days
4. **Deleted Content**: Soft delete with 90-day retention

This comprehensive database schema provides the foundation for the Opinian platform's complex functionality while maintaining performance, scalability, and data integrity.