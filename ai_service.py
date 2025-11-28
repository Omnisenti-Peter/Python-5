"""
AI Service Module for Opinian Platform
Handles OpenAI API integration for content generation
"""

import os
import logging
from openai import OpenAI
from dotenv import load_dotenv
import httpx

load_dotenv()
logger = logging.getLogger(__name__)

class AIService:
    """Service class for AI content generation using OpenAI"""

    def __init__(self):
        """Initialize OpenAI client"""
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '2000'))
        self.client = None

        if not self.api_key or self.api_key == 'your_openai_api_key_here':
            logger.warning("OpenAI API key not configured. AI features will use fallback mode.")
        else:
            try:
                # Create httpx client with explicit configuration (no proxy)
                http_client = httpx.Client(
                    timeout=30.0,
                    follow_redirects=True,
                    trust_env=False  # Ignore environment proxy settings
                )

                # Initialize OpenAI client with custom http client
                self.client = OpenAI(
                    api_key=self.api_key,
                    http_client=http_client,
                    max_retries=2
                )

                logger.info(f"OpenAI client initialized successfully with model: {self.model}")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                logger.warning("AI features will use fallback mode.")
                import traceback
                logger.debug(traceback.format_exc())

    def generate_blog_content(self, prompt, content_type='blog_post'):
        """
        Generate blog content based on user prompt

        Args:
            prompt (str): User's content idea or topic
            content_type (str): Type of content to generate

        Returns:
            dict: Generated content with metadata
        """
        if not self.client:
            return self._generate_fallback_content(prompt, content_type)

        try:
            # Create a detailed system prompt based on content type
            system_prompts = {
                'blog_post': """You are a professional blog writer. Generate engaging, well-structured blog content.

IMPORTANT: Generate ONLY the content body, NOT a complete HTML document.
DO NOT include <!DOCTYPE>, <html>, <head>, <body>, or <title> tags.

Generate content using these HTML tags ONLY:
- <h2> for the main title
- <h3> for subheadings
- <p> for paragraphs
- <ul> and <li> for bullet lists
- <ol> and <li> for numbered lists
- <strong> and <em> for emphasis
- <blockquote> for quotes

Structure:
1. Start with an <h2> title
2. 2-3 paragraphs of introduction
3. Main content with <h3> subheadings
4. Use bullet points or numbered lists where appropriate
5. End with a conclusion paragraph

Make it engaging, informative, and SEO-friendly. Start directly with <h2> and end with the last </p> tag.""",

                'article': """You are a professional article writer. Create detailed, informative article content.

IMPORTANT: Generate ONLY content snippets, NOT a complete HTML document.
DO NOT include <!DOCTYPE>, <html>, <head>, <body>, or <title> tags.

Use only: <h2>, <h3>, <p>, <ul>, <ol>, <li>, <strong>, <em>, <blockquote>
Focus on depth, research-backed points, and comprehensive coverage.
Start directly with <h2> and end with the last closing tag.""",

                'story': """You are a creative storyteller. Write engaging narrative content.

IMPORTANT: Generate ONLY the story content, NOT a complete HTML document.
DO NOT include <!DOCTYPE>, <html>, <head>, <body>, or <title> tags.

Use only: <h2>, <h3>, <p>, <strong>, <em>, <blockquote>
Focus on storytelling elements: setting, characters, conflict, and resolution.
Start directly with <h2> and end with the last </p> tag."""
            }

            system_prompt = system_prompts.get(content_type, system_prompts['blog_post'])

            # Generate content using OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Write content about: {prompt}"}
                ],
                max_tokens=self.max_tokens,
                temperature=0.7,
            )

            generated_content = response.choices[0].message.content

            # Clean up content - remove full HTML document structure if present
            generated_content = self._clean_html_content(generated_content)

            # Calculate metrics
            word_count = len(generated_content.split())
            estimated_reading_time = max(1, word_count // 200)  # 200 words per minute

            logger.info(f"Successfully generated content for prompt: {prompt[:50]}...")

            return {
                'success': True,
                'content': generated_content,
                'word_count': word_count,
                'estimated_reading_time': estimated_reading_time,
                'model': self.model
            }

        except Exception as e:
            logger.error(f"Error generating AI content: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to generate content. Please try again.'
            }

    def generate_title_suggestions(self, topic, count=5):
        """
        Generate title suggestions for a given topic

        Args:
            topic (str): Blog topic or idea
            count (int): Number of title suggestions to generate

        Returns:
            dict: List of title suggestions
        """
        if not self.client:
            return {
                'success': False,
                'message': 'OpenAI API key not configured'
            }

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a creative title generator. Generate catchy, SEO-friendly blog titles."},
                    {"role": "user", "content": f"Generate {count} engaging blog post titles about: {topic}. Return only the titles, one per line."}
                ],
                max_tokens=300,
                temperature=0.8,
            )

            titles = response.choices[0].message.content.strip().split('\n')
            # Clean up titles (remove numbering if present)
            titles = [title.strip().lstrip('0123456789.-) ') for title in titles if title.strip()]

            return {
                'success': True,
                'titles': titles[:count]
            }

        except Exception as e:
            logger.error(f"Error generating titles: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def improve_content(self, existing_content, instructions):
        """
        Improve or rewrite existing content based on instructions

        Args:
            existing_content (str): Current content
            instructions (str): How to improve the content

        Returns:
            dict: Improved content
        """
        if not self.client:
            return {
                'success': False,
                'message': 'OpenAI API key not configured'
            }

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional content editor. Improve the given content based on user instructions while maintaining HTML formatting."},
                    {"role": "user", "content": f"Instructions: {instructions}\n\nContent to improve:\n{existing_content}"}
                ],
                max_tokens=self.max_tokens,
                temperature=0.7,
            )

            improved_content = response.choices[0].message.content

            return {
                'success': True,
                'content': improved_content,
                'word_count': len(improved_content.split())
            }

        except Exception as e:
            logger.error(f"Error improving content: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def generate_excerpt(self, full_content, max_length=200):
        """
        Generate a compelling excerpt from full content

        Args:
            full_content (str): Full blog post content
            max_length (int): Maximum length of excerpt in characters

        Returns:
            dict: Generated excerpt
        """
        if not self.client:
            # Fallback: simple truncation
            from html import unescape
            import re
            # Strip HTML tags for simple excerpt
            text = re.sub('<[^<]+?>', '', full_content)
            text = unescape(text).strip()
            excerpt = text[:max_length] + '...' if len(text) > max_length else text
            return {
                'success': True,
                'excerpt': excerpt
            }

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are a professional editor. Create a compelling excerpt (max {max_length} characters) from the given content. Make it engaging and suitable for a blog post preview. Return only the excerpt text, no HTML tags."},
                    {"role": "user", "content": full_content}
                ],
                max_tokens=150,
                temperature=0.7,
            )

            excerpt = response.choices[0].message.content.strip()

            return {
                'success': True,
                'excerpt': excerpt
            }

        except Exception as e:
            logger.error(f"Error generating excerpt: {e}")
            # Fallback to simple truncation
            from html import unescape
            import re
            text = re.sub('<[^<]+?>', '', full_content)
            text = unescape(text).strip()
            excerpt = text[:max_length] + '...' if len(text) > max_length else text
            return {
                'success': True,
                'excerpt': excerpt
            }

    def _clean_html_content(self, content):
        """
        Clean HTML content to remove full document structure

        Args:
            content (str): Generated HTML content

        Returns:
            str: Cleaned content with only body elements
        """
        import re

        # Remove markdown code blocks if present
        content = re.sub(r'^```html\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'```\s*$', '', content, flags=re.MULTILINE)

        # If content contains full HTML document structure, extract body content
        if '<!DOCTYPE' in content or '<html' in content.lower():
            # Try to extract content from <body> tag
            body_match = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL | re.IGNORECASE)
            if body_match:
                content = body_match.group(1).strip()
            else:
                # If no body tag, try to remove html, head, and doctype
                content = re.sub(r'<!DOCTYPE[^>]*>', '', content, flags=re.IGNORECASE)
                content = re.sub(r'<html[^>]*>', '', content, flags=re.IGNORECASE)
                content = re.sub(r'</html>', '', content, flags=re.IGNORECASE)
                content = re.sub(r'<head>.*?</head>', '', content, flags=re.DOTALL | re.IGNORECASE)
                content = re.sub(r'<body[^>]*>', '', content, flags=re.IGNORECASE)
                content = re.sub(r'</body>', '', content, flags=re.IGNORECASE)

        # Remove any remaining title tags
        content = re.sub(r'<title>.*?</title>', '', content, flags=re.DOTALL | re.IGNORECASE)

        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        content = content.strip()

        return content

    def _generate_fallback_content(self, prompt, content_type):
        """
        Generate fallback content when OpenAI is not available

        Args:
            prompt (str): User's content idea
            content_type (str): Type of content

        Returns:
            dict: Fallback content with warning
        """
        fallback_content = f"""
        <h2>Content Generated: {prompt}</h2>

        <p><strong>Note:</strong> This is placeholder content. To use AI-powered content generation, please configure your OpenAI API key in the .env file.</p>

        <h3>Getting Started with Your Topic</h3>
        <p>Your topic "{prompt}" is interesting and has great potential. Here are some points to consider when writing about this:</p>

        <ul>
            <li>Research your topic thoroughly to provide valuable insights</li>
            <li>Structure your content with clear headings and subheadings</li>
            <li>Include examples and real-world applications</li>
            <li>Keep your audience engaged with a conversational tone</li>
            <li>Conclude with actionable takeaways</li>
        </ul>

        <h3>Content Structure Recommendations</h3>
        <p>For best results, consider organizing your content with:</p>
        <ul>
            <li>An attention-grabbing introduction</li>
            <li>2-3 main sections covering key aspects</li>
            <li>Supporting examples or case studies</li>
            <li>A strong conclusion with key takeaways</li>
        </ul>

        <p><em>To enable AI-powered content generation, add your OpenAI API key to the .env file:</em></p>
        <p><code>OPENAI_API_KEY=your_api_key_here</code></p>
        """

        return {
            'success': True,
            'content': fallback_content,
            'word_count': len(fallback_content.split()),
            'estimated_reading_time': 2,
            'is_fallback': True,
            'message': 'OpenAI API not configured. Using fallback content.'
        }

# Create a singleton instance
ai_service = AIService()
