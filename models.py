"""
Database models for Opinian blogging platform
Based on database.md schema, adapted for SQLite
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
import json


class User(UserMixin, db.Model):
    """User model for authentication and blog authorship"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    display_name = db.Column(db.String(200))
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(500))
    role = db.Column(db.String(20), default='reader', nullable=False)  # admin, author, reader
    status = db.Column(db.String(20), default='pending', nullable=False)  # active, suspended, pending
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    preferences = db.Column(db.Text)  # JSON stored as text
    metadata_json = db.Column(db.Text)  # JSON stored as text (renamed from metadata)

    # Backward compatibility
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships
    blog_posts = db.relationship('BlogPost', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    media_files = db.relationship('MediaFile', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify the user's password"""
        return check_password_hash(self.password_hash, password)

    def get_preferences(self):
        """Get user preferences as dict"""
        if self.preferences:
            return json.loads(self.preferences)
        return {}

    def set_preferences(self, prefs_dict):
        """Set user preferences from dict"""
        self.preferences = json.dumps(prefs_dict)

    def __repr__(self):
        return f'<User {self.username}>'


class BlogPost(db.Model):
    """Blog post model"""
    __tablename__ = 'blog_posts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(500), nullable=False)
    slug = db.Column(db.String(600), unique=True, nullable=False, index=True)
    excerpt = db.Column(db.Text)
    content = db.Column(db.Text, nullable=False)  # LONGTEXT equivalent
    content_html = db.Column(db.Text)
    featured_image = db.Column(db.String(500))
    status = db.Column(db.String(20), default='draft', nullable=False, index=True)  # draft, published, archived
    visibility = db.Column(db.String(30), default='public', nullable=False)  # public, private, password_protected
    password = db.Column(db.String(255))
    meta_title = db.Column(db.String(500))
    meta_description = db.Column(db.String(1000))
    meta_keywords = db.Column(db.String(1000))
    canonical_url = db.Column(db.String(500))
    reading_time = db.Column(db.Integer)
    word_count = db.Column(db.Integer)
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    share_count = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False, nullable=False, index=True)
    is_sticky = db.Column(db.Boolean, default=False, nullable=False)
    published_at = db.Column(db.DateTime, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    scheduled_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    tags = db.Column(db.Text)  # JSON stored as text
    categories = db.Column(db.Text)  # JSON stored as text
    custom_fields = db.Column(db.Text)  # JSON stored as text
    ai_assisted = db.Column(db.Boolean, default=False, nullable=False)
    ai_prompts = db.Column(db.Text)  # JSON stored as text
    version = db.Column(db.Integer, default=1, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'))

    # Relationships
    comments = db.relationship('Comment', backref='blog_post', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='blog_post', lazy='dynamic', cascade='all, delete-orphan')
    page_views = db.relationship('PageView', backref='post', lazy='dynamic')

    def get_tags(self):
        """Get tags as list"""
        if self.tags:
            return json.loads(self.tags)
        return []

    def set_tags(self, tags_list):
        """Set tags from list"""
        self.tags = json.dumps(tags_list)

    def get_categories(self):
        """Get categories as list"""
        if self.categories:
            return json.loads(self.categories)
        return []

    def set_categories(self, categories_list):
        """Set categories from list"""
        self.categories = json.dumps(categories_list)

    # Backward compatibility properties
    @property
    def author_id(self):
        """Backward compatibility: return user_id as author_id"""
        return self.user_id

    @author_id.setter
    def author_id(self, value):
        """Backward compatibility: set user_id when author_id is set"""
        self.user_id = value

    @property
    def is_published(self):
        """Backward compatibility: check if status is published"""
        return self.status == 'published'

    @is_published.setter
    def is_published(self, value):
        """Backward compatibility: set status based on is_published"""
        if value:
            self.status = 'published'
            if not self.published_at:
                self.published_at = datetime.utcnow()
        else:
            self.status = 'draft'

    @property
    def ai_enhanced(self):
        """Backward compatibility: alias for ai_assisted"""
        return self.ai_assisted

    @ai_enhanced.setter
    def ai_enhanced(self, value):
        """Backward compatibility: set ai_assisted when ai_enhanced is set"""
        self.ai_assisted = value

    def __repr__(self):
        return f'<BlogPost {self.title}>'


class Category(db.Model):
    """Category model"""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(250), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    color = db.Column(db.String(7))
    icon = db.Column(db.String(100))
    post_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    metadata_json = db.Column(db.Text)  # JSON stored as text (renamed from metadata)

    def __repr__(self):
        return f'<Category {self.name}>'


class Tag(db.Model):
    """Tag model"""
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(150), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    color = db.Column(db.String(7))
    post_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    metadata_json = db.Column(db.Text)  # JSON stored as text (renamed from metadata)

    def __repr__(self):
        return f'<Tag {self.name}>'


class MediaFile(db.Model):
    """Media files model"""
    __tablename__ = 'media_files'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    filename = db.Column(db.String(500), nullable=False)
    original_name = db.Column(db.String(500))
    mime_type = db.Column(db.String(100), index=True)
    file_size = db.Column(db.Integer)
    file_hash = db.Column(db.String(64))
    url = db.Column(db.String(1000), nullable=False)
    thumbnail_url = db.Column(db.String(1000))
    alt_text = db.Column(db.String(500))
    caption = db.Column(db.Text)
    description = db.Column(db.Text)
    dimensions = db.Column(db.Text)  # JSON stored as text
    metadata_json = db.Column(db.Text)  # JSON stored as text (renamed from metadata)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<MediaFile {self.filename}>'


class Comment(db.Model):
    """Comment model for blog posts"""
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Nullable for guest comments
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'))
    author_name = db.Column(db.String(200))
    author_email = db.Column(db.String(255))
    author_website = db.Column(db.String(500))
    content = db.Column(db.Text, nullable=False)
    content_html = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending', nullable=False, index=True)  # pending, approved, spam, trash
    like_count = db.Column(db.Integer, default=0, nullable=False)
    dislike_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Backward compatibility property
    @property
    def author_id(self):
        """Backward compatibility: return user_id as author_id"""
        return self.user_id

    @author_id.setter
    def author_id(self, value):
        """Backward compatibility: set user_id when author_id is set"""
        self.user_id = value

    def __repr__(self):
        return f'<Comment {self.id} on Post {self.post_id}>'


class Like(db.Model):
    """Like model for blog posts"""
    __tablename__ = 'likes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Ensure a user can only like a post once
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_like'),)

    def __repr__(self):
        return f'<Like user={self.user_id} post={self.post_id}>'


class AIPrompt(db.Model):
    """AI Prompts model"""
    __tablename__ = 'ai_prompts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), index=True)
    description = db.Column(db.Text)
    prompt_template = db.Column(db.Text, nullable=False)
    variables = db.Column(db.Text)  # JSON stored as text
    model_config = db.Column(db.Text)  # JSON stored as text
    temperature = db.Column(db.Numeric(3, 2), default=0.7, nullable=False)
    max_tokens = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    version = db.Column(db.Integer, default=1, nullable=False)
    usage_count = db.Column(db.Integer, default=0, nullable=False)

    def __repr__(self):
        return f'<AIPrompt {self.name}>'


class AIUsageLog(db.Model):
    """AI Usage Logs model"""
    __tablename__ = 'ai_usage_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    prompt_id = db.Column(db.Integer, db.ForeignKey('ai_prompts.id'), index=True)
    model_name = db.Column(db.String(100))
    input_tokens = db.Column(db.Integer)
    output_tokens = db.Column(db.Integer)
    total_tokens = db.Column(db.Integer)
    cost = db.Column(db.Numeric(10, 6))
    request_data = db.Column(db.Text)  # JSON stored as text
    response_data = db.Column(db.Text)  # JSON stored as text
    status = db.Column(db.String(20), default='success', nullable=False, index=True)  # success, error, timeout
    error_message = db.Column(db.Text)
    processing_time = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Backward compatibility - simplified version
    model_used = db.Column(db.String(100))
    input_length = db.Column(db.Integer)
    output_length = db.Column(db.Integer)

    def __repr__(self):
        return f'<AIUsageLog {self.model_name} by user {self.user_id}>'


# Backward compatibility alias
AIUsage = AIUsageLog


class LLMConfig(db.Model):
    """LLM Configuration model"""
    __tablename__ = 'llm_config'

    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(100), nullable=False)
    api_key_encrypted = db.Column(db.Text, nullable=False)
    model_name = db.Column(db.String(100), nullable=False)
    endpoint_url = db.Column(db.String(1000))
    additional_params = db.Column(db.Text)  # JSON stored as text
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    usage_limits = db.Column(db.Text)  # JSON stored as text
    cost_per_token = db.Column(db.Numeric(10, 6))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (db.UniqueConstraint('provider', 'model_name', name='unique_provider_model'),)

    def __repr__(self):
        return f'<LLMConfig {self.provider}/{self.model_name}>'


class AnalyticsEvent(db.Model):
    """Analytics Events model"""
    __tablename__ = 'analytics_events'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    session_id = db.Column(db.String(100), index=True)
    event_type = db.Column(db.String(100), nullable=False, index=True)
    event_category = db.Column(db.String(100))
    event_action = db.Column(db.String(100))
    event_label = db.Column(db.String(500))
    page_url = db.Column(db.String(1000))
    referrer_url = db.Column(db.String(1000))
    user_agent = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    geo_location = db.Column(db.Text)  # JSON stored as text
    device_info = db.Column(db.Text)  # JSON stored as text
    custom_data = db.Column(db.Text)  # JSON stored as text
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f'<AnalyticsEvent {self.event_type}>'


class PageView(db.Model):
    """Page Views model"""
    __tablename__ = 'page_views'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    session_id = db.Column(db.String(100), index=True)
    page_url = db.Column(db.String(1000), nullable=False)
    page_title = db.Column(db.String(500))
    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'), index=True)
    referrer_url = db.Column(db.String(1000))
    user_agent = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    geo_location = db.Column(db.Text)  # JSON stored as text
    device_info = db.Column(db.Text)  # JSON stored as text
    time_on_page = db.Column(db.Integer)
    scroll_depth = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f'<PageView {self.page_url}>'


class UserSession(db.Model):
    """User Sessions model"""
    __tablename__ = 'user_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    user_agent = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    geo_location = db.Column(db.Text)  # JSON stored as text
    device_info = db.Column(db.Text)  # JSON stored as text
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    ended_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f'<UserSession {self.session_id}>'


class SystemSetting(db.Model):
    """System Settings model"""
    __tablename__ = 'system_settings'

    id = db.Column(db.Integer, primary_key=True)
    key_name = db.Column(db.String(200), unique=True, nullable=False, index=True)
    value = db.Column(db.Text)
    value_type = db.Column(db.String(20), default='string', nullable=False)  # string, number, boolean, json
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    is_system = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<SystemSetting {self.key_name}>'


class AuditLog(db.Model):
    """Audit Logs model"""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    action = db.Column(db.String(200), nullable=False, index=True)
    resource_type = db.Column(db.String(100), index=True)
    resource_id = db.Column(db.Integer)
    old_values = db.Column(db.Text)  # JSON stored as text
    new_values = db.Column(db.Text)  # JSON stored as text
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f'<AuditLog {self.action}>'


class APIConfiguration(db.Model):
    """Store API configuration (admin only) - Backward compatibility"""
    __tablename__ = 'api_configurations'

    id = db.Column(db.Integer, primary_key=True)
    openai_key = db.Column(db.String(255))
    anthropic_key = db.Column(db.String(255))
    huggingface_key = db.Column(db.String(255))
    preferred_model = db.Column(db.String(100), default='gpt-3.5-turbo')
    temperature = db.Column(db.Float, default=0.7)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<APIConfiguration {self.id}>'
