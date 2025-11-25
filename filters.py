"""
Template filters for Jinja2
"""
import re


def register_filters(app):
    """Register all template filters with the Flask app"""
    
    @app.template_filter('truncate_words')
    def truncate_words(text, length=50):
        """Truncate text to specified number of words"""
        words = text.split()
        if len(words) > length:
            return ' '.join(words[:length]) + '...'
        return text

    @app.template_filter('format_date')
    def format_date(date):
        """Format date for display"""
        return date.strftime('%B %d, %Y')

    @app.template_filter('format_datetime')
    def format_datetime(date):
        """Format datetime for display"""
        return date.strftime('%B %d, %Y at %I:%M %p')

    @app.template_filter('wordcount')
    def wordcount(text):
        """Count words in text"""
        if not text:
            return 0
        # Strip HTML tags for accurate word count
        clean_text = re.sub(r'<[^>]+>', '', text)
        words = clean_text.split()
        return len(words)

    @app.template_filter('nl2br')
    def nl2br(text):
        """Convert newlines to HTML line breaks"""
        if not text:
            return ''
        # Replace \r\n and \n with <br> tags
        return text.replace('\r\n', '<br>').replace('\n', '<br>')

