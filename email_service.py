"""
Email service for Opinian platform
Handles email sending for password reset, welcome emails, and notifications
"""

import os
import logging
from flask import render_template_string
from flask_mail import Mail, Message
from threading import Thread

logger = logging.getLogger(__name__)

# Global mail instance (will be initialized in app.py)
mail = None


def init_mail(app):
    """Initialize Flask-Mail with the Flask app"""
    global mail
    mail = Mail(app)
    logger.info("Email service initialized")


def send_async_email(app, msg):
    """Send email asynchronously"""
    with app.app_context():
        try:
            mail.send(msg)
            logger.info(f"Email sent successfully to {msg.recipients}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")


def send_email(subject, recipients, text_body, html_body, sender=None, app=None):
    """
    Send email with both text and HTML body

    Args:
        subject: Email subject
        recipients: List of recipient emails
        text_body: Plain text body
        html_body: HTML body
        sender: Sender email (optional, uses default from config)
        app: Flask app instance for async sending
    """
    if not mail:
        logger.warning("Email service not initialized, email not sent")
        return False

    try:
        msg = Message(
            subject=subject,
            recipients=recipients if isinstance(recipients, list) else [recipients],
            sender=sender or os.getenv('MAIL_DEFAULT_SENDER', 'noreply@opinian.com')
        )
        msg.body = text_body
        msg.html = html_body

        if app:
            # Send asynchronously
            Thread(target=send_async_email, args=(app, msg)).start()
        else:
            # Send synchronously
            mail.send(msg)

        return True
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False


def send_password_reset_email(user_email, reset_token, user_name, app=None):
    """Send password reset email"""
    reset_url = f"{os.getenv('APP_URL', 'http://localhost:5000')}/reset-password/{reset_token}"

    subject = "Reset Your Password - Opinian"

    text_body = f"""
Hello {user_name},

You requested to reset your password for your Opinian account.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you did not request this, please ignore this email.

Best regards,
The Opinian Team
"""

    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #1a1a1a; color: #d4af37; padding: 20px; text-align: center; }}
        .content {{ background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; }}
        .button {{ display: inline-block; padding: 12px 30px; background-color: #d4af37; color: #1a1a1a; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖋️ Opinian</h1>
        </div>
        <div class="content">
            <h2>Password Reset Request</h2>
            <p>Hello <strong>{user_name}</strong>,</p>
            <p>You requested to reset your password for your Opinian account.</p>
            <p>Click the button below to reset your password:</p>
            <p style="text-align: center;">
                <a href="{reset_url}" class="button">Reset Password</a>
            </p>
            <p style="color: #666; font-size: 14px;">
                Or copy and paste this link into your browser:<br>
                <a href="{reset_url}">{reset_url}</a>
            </p>
            <p style="color: #d9534f; font-weight: bold;">This link will expire in 1 hour.</p>
            <p>If you did not request this, please ignore this email and your password will remain unchanged.</p>
        </div>
        <div class="footer">
            <p>© 2025 Opinian. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

    return send_email(subject, user_email, text_body, html_body, app=app)


def send_welcome_email(user_email, user_name, username, app=None):
    """Send welcome email to new users"""
    login_url = f"{os.getenv('APP_URL', 'http://localhost:5000')}/login"

    subject = "Welcome to Opinian!"

    text_body = f"""
Hello {user_name},

Welcome to Opinian! Your account has been successfully created.

Username: {username}

You can now log in and start creating amazing content:
{login_url}

Features you can explore:
- Create and publish blog posts
- Use AI-powered writing assistant
- Customize your profile
- Join a community of writers

If you have any questions, feel free to reach out to us.

Best regards,
The Opinian Team
"""

    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #1a1a1a; color: #d4af37; padding: 30px; text-align: center; }}
        .content {{ background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; }}
        .button {{ display: inline-block; padding: 12px 30px; background-color: #d4af37; color: #1a1a1a; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 20px 0; }}
        .features {{ background-color: #fff; padding: 20px; margin: 20px 0; border-left: 4px solid #d4af37; }}
        .features ul {{ list-style-type: none; padding: 0; }}
        .features li {{ padding: 8px 0; }}
        .features li:before {{ content: "✓ "; color: #d4af37; font-weight: bold; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖋️ Welcome to Opinian!</h1>
        </div>
        <div class="content">
            <h2>Your Account is Ready!</h2>
            <p>Hello <strong>{user_name}</strong>,</p>
            <p>Welcome aboard! Your Opinian account has been successfully created.</p>
            <p><strong>Username:</strong> {username}</p>
            <p style="text-align: center;">
                <a href="{login_url}" class="button">Start Writing</a>
            </p>

            <div class="features">
                <h3 style="margin-top: 0;">What You Can Do:</h3>
                <ul>
                    <li>Create and publish engaging blog posts</li>
                    <li>Use AI-powered writing assistant</li>
                    <li>Customize your profile and bio</li>
                    <li>Export content to Word documents</li>
                    <li>Join a community of passionate writers</li>
                </ul>
            </div>

            <p>Ready to share your voice with the world? Log in now and start creating!</p>
        </div>
        <div class="footer">
            <p>© 2025 Opinian. All rights reserved.</p>
            <p>You're receiving this email because you created an account on Opinian.</p>
        </div>
    </div>
</body>
</html>
"""

    return send_email(subject, user_email, text_body, html_body, app=app)


def send_contact_form_email(name, email, message, app=None):
    """Send contact form submission to admin"""
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@opinian.com')

    subject = f"New Contact Form Submission from {name}"

    text_body = f"""
New contact form submission:

Name: {name}
Email: {email}

Message:
{message}
"""

    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #1a1a1a; color: #d4af37; padding: 20px; text-align: center; }}
        .content {{ background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; }}
        .field {{ margin-bottom: 15px; }}
        .label {{ font-weight: bold; color: #666; }}
        .message {{ background-color: #fff; padding: 15px; border-left: 4px solid #d4af37; margin-top: 15px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>New Contact Form Submission</h2>
        </div>
        <div class="content">
            <div class="field">
                <span class="label">From:</span> {name}
            </div>
            <div class="field">
                <span class="label">Email:</span> <a href="mailto:{email}">{email}</a>
            </div>
            <div class="message">
                <span class="label">Message:</span><br><br>
                {message.replace(chr(10), '<br>')}
            </div>
        </div>
    </div>
</body>
</html>
"""

    return send_email(subject, admin_email, text_body, html_body, app=app)


def send_admin_notification_new_user(admin_email, user_name, username, user_email, app=None):
    """Send notification to admin when new user registers"""
    subject = f"New User Registration: {user_name}"

    text_body = f"""
New user has registered on Opinian:

Name: {user_name}
Username: {username}
Email: {user_email}

You can manage users from the admin dashboard.
"""

    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #1a1a1a; color: #d4af37; padding: 20px; text-align: center; }}
        .content {{ background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; }}
        .user-info {{ background-color: #fff; padding: 15px; margin: 15px 0; border-left: 4px solid #d4af37; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🎉 New User Registration</h2>
        </div>
        <div class="content">
            <p>A new user has registered on Opinian:</p>
            <div class="user-info">
                <p><strong>Name:</strong> {user_name}</p>
                <p><strong>Username:</strong> {username}</p>
                <p><strong>Email:</strong> {user_email}</p>
            </div>
            <p>You can manage users from the admin dashboard.</p>
        </div>
    </div>
</body>
</html>
"""

    return send_email(subject, admin_email, text_body, html_body, app=app)


def send_moderation_decision_email(user_email, user_name, content_type, decision, review_notes, app=None):
    """
    Send moderation decision notification to content author

    Args:
        user_email: Author's email
        user_name: Author's name
        content_type: Type of content ('blog_post' or 'page')
        decision: 'approved' or 'rejected'
        review_notes: Moderator's notes/reason
        app: Flask app instance for async sending
    """
    content_label = content_type.replace('_', ' ').title()

    if decision == 'approved':
        subject = f"✓ Your {content_label} Has Been Approved - Opinian"
        status_color = "#5cb85c"
        status_icon = "✓"
        status_text = "Approved"
        message = f"Great news! Your {content_label.lower()} has been approved and is now published."
    else:  # rejected
        subject = f"Your {content_label} Requires Revision - Opinian"
        status_color = "#d9534f"
        status_icon = "✗"
        status_text = "Requires Revision"
        message = f"Your {content_label.lower()} submission requires some changes before it can be published."

    text_body = f"""
Hello {user_name},

{message}

Content Type: {content_label}
Status: {status_text}

{'Moderator Notes:' if review_notes else 'No additional notes provided.'}
{review_notes if review_notes else ''}

{'You can now view your published content on the platform!' if decision == 'approved' else 'Please review the moderator notes and resubmit your content with the necessary changes.'}

Best regards,
The Opinian Moderation Team
"""

    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #1a1a1a; color: #d4af37; padding: 20px; text-align: center; }}
        .content {{ background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; }}
        .status-box {{ background-color: {status_color}; color: white; padding: 20px; text-align: center; border-radius: 5px; margin: 20px 0; }}
        .status-icon {{ font-size: 48px; margin-bottom: 10px; }}
        .info-box {{ background-color: #fff; padding: 15px; margin: 15px 0; border-left: 4px solid {status_color}; }}
        .notes {{ background-color: #fff3cd; padding: 15px; margin: 15px 0; border-left: 4px solid #ffc107; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖋️ Opinian</h1>
        </div>
        <div class="content">
            <div class="status-box">
                <div class="status-icon">{status_icon}</div>
                <h2 style="margin: 0;">{status_text}</h2>
            </div>

            <p>Hello <strong>{user_name}</strong>,</p>
            <p>{message}</p>

            <div class="info-box">
                <p style="margin: 5px 0;"><strong>Content Type:</strong> {content_label}</p>
                <p style="margin: 5px 0;"><strong>Status:</strong> {status_text}</p>
            </div>

            {f'''
            <div class="notes">
                <h3 style="margin-top: 0; color: #856404;">
                    <i class="fas fa-comment-dots"></i> Moderator Notes:
                </h3>
                <p>{review_notes.replace(chr(10), '<br>')}</p>
            </div>
            ''' if review_notes else ''}

            {'<p style="color: #5cb85c; font-weight: bold;">🎉 Your content is now live and visible to all users!</p>' if decision == 'approved' else '<p style="color: #856404;">Please review the moderator notes and make the necessary changes to your content. You can edit and resubmit for review.</p>'}
        </div>
        <div class="footer">
            <p>© 2025 Opinian. All rights reserved.</p>
            <p>This is an automated moderation notification.</p>
        </div>
    </div>
</body>
</html>
"""

    return send_email(subject, user_email, text_body, html_body, app=app)
