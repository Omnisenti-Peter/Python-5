"""
AI Service for story enhancement using OpenAI and Anthropic APIs
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class AIService:
    """Service class for AI-powered story enhancement"""

    def __init__(self,
                 openai_key: Optional[str] = None,
                 anthropic_key: Optional[str] = None,
                 huggingface_key: Optional[str] = None,
                 preferred_model: str = 'gpt-3.5-turbo',
                 temperature: float = 0.7):
        """
        Initialize AI Service with API keys

        Args:
            openai_key: OpenAI API key
            anthropic_key: Anthropic API key
            huggingface_key: Hugging Face API key
            preferred_model: Preferred AI model to use
            temperature: Temperature for AI generation (0-1)
        """
        self.openai_key = openai_key
        self.anthropic_key = anthropic_key
        self.huggingface_key = huggingface_key
        self.preferred_model = preferred_model
        self.temperature = temperature

        # Initialize clients
        self.openai_client = None
        self.anthropic_client = None

        # Setup clients based on available keys
        self._setup_clients()

    def _setup_clients(self):
        """Setup AI client libraries"""
        # Setup OpenAI
        if self.openai_key and self.openai_key.strip():
            try:
                from openai import OpenAI
                # Initialize with minimal parameters to avoid conflicts
                self.openai_client = OpenAI(
                    api_key=self.openai_key.strip(),
                    timeout=60.0,  # 60 second timeout
                )
                logger.info('OpenAI client initialized successfully')
            except ImportError:
                logger.warning('OpenAI library not installed. Install with: pip install openai')
                self.openai_client = None
            except Exception as e:
                logger.error(f'Error initializing OpenAI client: {str(e)}')
                self.openai_client = None

        # Setup Anthropic
        if self.anthropic_key and self.anthropic_key.strip():
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(
                    api_key=self.anthropic_key.strip(),
                    timeout=60.0,
                )
                logger.info('Anthropic client initialized successfully')
            except ImportError:
                logger.warning('Anthropic library not installed. Install with: pip install anthropic')
                self.anthropic_client = None
            except Exception as e:
                logger.error(f'Error initializing Anthropic client: {str(e)}')
                self.anthropic_client = None

    def enhance_story(self, text: str) -> str:
        """
        Enhance story text using AI

        Args:
            text: Original story text to enhance

        Returns:
            Enhanced story text
        """
        if not text:
            raise ValueError('No text provided for enhancement')

        # Determine which AI service to use based on preferred model
        if 'gpt' in self.preferred_model.lower() and self.openai_client:
            return self._enhance_with_openai(text)
        elif 'claude' in self.preferred_model.lower() and self.anthropic_client:
            return self._enhance_with_anthropic(text)
        else:
            # Fallback to whichever client is available
            if self.openai_client:
                return self._enhance_with_openai(text)
            elif self.anthropic_client:
                return self._enhance_with_anthropic(text)
            else:
                raise RuntimeError('No AI service configured. Please add API keys in the admin panel.')

    def _enhance_with_openai(self, text: str) -> str:
        """Enhance text using OpenAI API"""
        try:
            system_prompt = """You are a creative writing assistant specializing in 1920s and 1940s noir storytelling.
Your task is to enhance the given text with:
- Rich, evocative language reminiscent of the Jazz Age and Film Noir era
- Vivid descriptions that paint atmospheric scenes
- Engaging narrative flow
- Period-appropriate vocabulary and style
- Emotional depth and compelling characters

Maintain the original story's core message and intent while elevating the prose quality."""

            response = self.openai_client.chat.completions.create(
                model=self.preferred_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Please enhance this story:\n\n{text}"}
                ],
                temperature=self.temperature,
                max_tokens=2000
            )

            enhanced_text = response.choices[0].message.content.strip()
            logger.info(f'Successfully enhanced text with OpenAI ({self.preferred_model})')
            return enhanced_text

        except Exception as e:
            logger.error(f'OpenAI enhancement error: {str(e)}')
            raise RuntimeError(f'AI enhancement failed: {str(e)}')

    def _enhance_with_anthropic(self, text: str) -> str:
        """Enhance text using Anthropic Claude API"""
        try:
            system_prompt = """You are a creative writing assistant specializing in 1920s and 1940s noir storytelling.
Your task is to enhance the given text with:
- Rich, evocative language reminiscent of the Jazz Age and Film Noir era
- Vivid descriptions that paint atmospheric scenes
- Engaging narrative flow
- Period-appropriate vocabulary and style
- Emotional depth and compelling characters

Maintain the original story's core message and intent while elevating the prose quality."""

            message = self.anthropic_client.messages.create(
                model=self.preferred_model,
                max_tokens=2000,
                temperature=self.temperature,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": f"Please enhance this story:\n\n{text}"
                    }
                ]
            )

            enhanced_text = message.content[0].text.strip()
            logger.info(f'Successfully enhanced text with Anthropic ({self.preferred_model})')
            return enhanced_text

        except Exception as e:
            logger.error(f'Anthropic enhancement error: {str(e)}')
            raise RuntimeError(f'AI enhancement failed: {str(e)}')

    def get_available_models(self) -> list:
        """Get list of available AI models based on configured API keys"""
        models = []

        if self.openai_key:
            models.extend([
                {'id': 'gpt-4', 'name': 'GPT-4 (OpenAI)', 'provider': 'openai'},
                {'id': 'gpt-3.5-turbo', 'name': 'GPT-3.5 Turbo (OpenAI)', 'provider': 'openai'}
            ])

        if self.anthropic_key:
            models.extend([
                {'id': 'claude-3-opus-20240229', 'name': 'Claude 3 Opus (Anthropic)', 'provider': 'anthropic'},
                {'id': 'claude-3-sonnet-20240229', 'name': 'Claude 3 Sonnet (Anthropic)', 'provider': 'anthropic'},
                {'id': 'claude-3-haiku-20240307', 'name': 'Claude 3 Haiku (Anthropic)', 'provider': 'anthropic'}
            ])

        return models

    def is_configured(self) -> bool:
        """Check if at least one AI service is configured"""
        return self.openai_client is not None or self.anthropic_client is not None
