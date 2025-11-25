"""
Database initialization and setup
"""
from extensions import db
from models import User, BlogPost
from datetime import datetime
import re


def slugify(text):
    """Convert text to URL-friendly slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def init_db(app):
    """Initialize database tables and demo data"""
    with app.app_context():
        db.create_all()

        # Create demo users if they don't exist
        if User.query.count() == 0:
            admin = User(
                username='admin',
                email='admin@opinian.com',
                first_name='Admin',
                last_name='User',
                display_name='Administrator',
                role='admin',
                status='active',
                email_verified=True,
                is_admin=True  # Backward compatibility
            )
            admin.set_password('admin123')

            user = User(
                username='user',
                email='user@opinian.com',
                first_name='Regular',
                last_name='User',
                display_name='Regular User',
                role='author',
                status='active',
                email_verified=True,
                is_admin=False  # Backward compatibility
            )
            user.set_password('user123')

            db.session.add(admin)
            db.session.add(user)
            db.session.commit()

            # Create demo blog posts
            post1 = BlogPost(
                title="The Jazz Age Chronicles: A Night at the Speakeasy",
                slug=slugify("The Jazz Age Chronicles: A Night at the Speakeasy"),
                excerpt="The year was 1925, and the air was thick with cigarette smoke and the sweet sounds of jazz.",
                content="The year was 1925, and the air was thick with cigarette smoke and the sweet sounds of jazz. Sarah adjusted her feathered headband and stepped into the dimly lit speakeasy, her beaded dress catching the golden light from the chandeliers above. The password had been 'butterscotch' - a detail she wouldn't soon forget.",
                user_id=admin.id,
                status='published',
                visibility='public',
                published_at=datetime.utcnow(),
                word_count=len("The year was 1925, and the air was thick with cigarette smoke and the sweet sounds of jazz. Sarah adjusted her feathered headband and stepped into the dimly lit speakeasy, her beaded dress catching the golden light from the chandeliers above. The password had been 'butterscotch' - a detail she wouldn't soon forget.".split()),
                reading_time=1,
                ai_assisted=False
            )

            post2 = BlogPost(
                title="Midnight in Chicago: A Detective's Tale",
                slug=slugify("Midnight in Chicago: A Detective's Tale"),
                excerpt="The rain fell in sheets as Detective Murphy lit his fifth cigarette of the night.",
                content="The rain fell in sheets as Detective Murphy lit his fifth cigarette of the night. The dame in the red dress had promised him answers, but all he'd gotten so far was a headache and an empty wallet. This city had a way of chewing people up and spitting them out, and tonight, he was feeling particularly chewed.",
                user_id=user.id,
                status='published',
                visibility='public',
                published_at=datetime.utcnow(),
                word_count=len("The rain fell in sheets as Detective Murphy lit his fifth cigarette of the night. The dame in the red dress had promised him answers, but all he'd gotten so far was a headache and an empty wallet. This city had a way of chewing people up and spitting them out, and tonight, he was feeling particularly chewed.".split()),
                reading_time=1,
                ai_assisted=False
            )

            db.session.add(post1)
            db.session.add(post2)
            db.session.commit()

            app.logger.info('Database initialized with demo data')
