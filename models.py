"""
Database models for Opinian blogging platform
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication and blog authorship"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    blog_posts = db.relationship('BlogPost', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify the user's password"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class BlogPost(db.Model):
    """Blog post model"""
    __tablename__ = 'blog_posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_published = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # AI enhancement tracking
    ai_enhanced = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships
    comments = db.relationship('Comment', backref='blog_post', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='blog_post', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def like_count(self):
        """Get the number of likes for this post"""
        return self.likes.count()

    @property
    def comment_count(self):
        """Get the number of comments for this post"""
        return self.comments.count()

    def is_liked_by(self, user):
        """Check if a specific user has liked this post"""
        if not user or not user.is_authenticated:
            return False
        return self.likes.filter_by(user_id=user.id).first() is not None

    def __repr__(self):
        return f'<BlogPost {self.title}>'

class Comment(db.Model):
    """Comment model for blog posts"""
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Comment {self.id} on Post {self.post_id}>'

class Like(db.Model):
    """Like model for blog posts"""
    __tablename__ = 'likes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Ensure a user can only like a post once
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_like'),)

    def __repr__(self):
        return f'<Like user={self.user_id} post={self.post_id}>'

class AIUsage(db.Model):
    """Track AI API usage for analytics"""
    __tablename__ = 'ai_usage'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    model_used = db.Column(db.String(100), nullable=False)
    input_length = db.Column(db.Integer, nullable=False)
    output_length = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref='ai_usage_history')

    def __repr__(self):
        return f'<AIUsage {self.model_used} by user {self.user_id}>'

class APIConfiguration(db.Model):
    """Store API configuration (admin only)"""
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
