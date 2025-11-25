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

    def enhance_story(self, text: str, content_type: str = 'story',
                     writing_style: str = 'noir', content_length: str = 'medium',
                     target_audience: str = 'general') -> str:
        """
        Enhance story text using AI

        Args:
            text: Original story text to enhance
            content_type: Type of content (story, blog, article, etc.)
            writing_style: Writing style (professional, casual, noir, etc.)
            content_length: Desired length (short, medium, long)
            target_audience: Target audience level

        Returns:
            Enhanced story text
        """
        if not text:
            raise ValueError('No text provided for enhancement')

        # Determine which AI service to use based on preferred model
        if 'gpt' in self.preferred_model.lower() and self.openai_client:
            return self._enhance_with_openai(text, content_type, writing_style, content_length, target_audience)
        elif 'claude' in self.preferred_model.lower() and self.anthropic_client:
            return self._enhance_with_anthropic(text, content_type, writing_style, content_length, target_audience)
        else:
            # Fallback to whichever client is available
            if self.openai_client:
                return self._enhance_with_openai(text, content_type, writing_style, content_length, target_audience)
            elif self.anthropic_client:
                return self._enhance_with_anthropic(text, content_type, writing_style, content_length, target_audience)
            else:
                raise RuntimeError('No AI service configured. Please add API keys in the admin panel.')

    def _enhance_with_openai(self, text: str, content_type: str, writing_style: str,
                            content_length: str, target_audience: str) -> str:
        """Enhance text using OpenAI API"""
        try:
            # Build dynamic system prompt based on parameters
            style_descriptions = {
                'professional': 'professional, polished business writing with clear structure',
                'casual': 'conversational, friendly tone with accessible language',
                'academic': 'scholarly, well-researched with formal academic tone',
                'creative': 'imaginative, artistic expression with vivid imagery',
                'noir': 'rich, evocative language reminiscent of 1920s-1940s Film Noir era with atmospheric scenes',
                'journalistic': 'objective, fact-based reporting style with clear information',
                'conversational': 'natural, dialogue-like tone as if speaking to a friend'
            }

            length_targets = {
                'short': '300-500 words',
                'medium': '800-1200 words',
                'long': '1500-2500 words'
            }

            audience_descriptions = {
                'general': 'general audience with clear, accessible language',
                'beginners': 'beginners with simple explanations and foundational concepts',
                'intermediate': 'intermediate readers with moderate complexity',
                'advanced': 'advanced readers with sophisticated concepts and terminology',
                'professionals': 'industry professionals with technical depth and expertise'
            }

            content_type_instructions = {
                'story': 'a narrative story with plot, characters, and engaging storytelling',
                'blog': 'a blog post with engaging hooks, clear sections, and conversational flow',
                'article': 'an informative article with structured sections and well-researched content',
                'creative': 'creative writing with artistic expression and imaginative elements',
                'noir': 'a noir mystery with atmospheric tension, compelling characters, and shadowy intrigue',
                'character': 'character development with psychological depth, motivations, and backstory',
                'outline': 'a structured story outline with plot points, character arcs, and scene breakdowns'
            }

            style_desc = style_descriptions.get(writing_style, style_descriptions['noir'])
            length_target = length_targets.get(content_length, '800-1200 words')
            audience_desc = audience_descriptions.get(target_audience, 'general audience')
            content_instruction = content_type_instructions.get(content_type, 'engaging content')

            system_prompt = f"""You are a professional writing assistant. Transform the provided text into {content_instruction}.

Writing Requirements:
- Style: {style_desc}
- Target Length: {length_target}
- Target Audience: {audience_desc}
- Maintain the original message and intent
- Create engaging, well-structured content
- Use appropriate vocabulary and tone for the audience level"""

            max_tokens_map = {'short': 800, 'medium': 2000, 'long': 3500}
            max_tokens = max_tokens_map.get(content_length, 2000)

            response = self.openai_client.chat.completions.create(
                model=self.preferred_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Transform this into {content_instruction}:\n\n{text}"}
                ],
                temperature=self.temperature,
                max_tokens=max_tokens
            )

            enhanced_text = response.choices[0].message.content.strip()
            logger.info(f'Successfully enhanced text with OpenAI ({self.preferred_model})')
            return enhanced_text

        except Exception as e:
            logger.error(f'OpenAI enhancement error: {str(e)}')
            raise RuntimeError(f'AI enhancement failed: {str(e)}')

    def _enhance_with_anthropic(self, text: str, content_type: str, writing_style: str,
                                content_length: str, target_audience: str) -> str:
        """Enhance text using Anthropic Claude API"""
        try:
            # Build dynamic system prompt (same logic as OpenAI)
            style_descriptions = {
                'professional': 'professional, polished business writing with clear structure',
                'casual': 'conversational, friendly tone with accessible language',
                'academic': 'scholarly, well-researched with formal academic tone',
                'creative': 'imaginative, artistic expression with vivid imagery',
                'noir': 'rich, evocative language reminiscent of 1920s-1940s Film Noir era with atmospheric scenes',
                'journalistic': 'objective, fact-based reporting style with clear information',
                'conversational': 'natural, dialogue-like tone as if speaking to a friend'
            }

            length_targets = {
                'short': '300-500 words',
                'medium': '800-1200 words',
                'long': '1500-2500 words'
            }

            audience_descriptions = {
                'general': 'general audience with clear, accessible language',
                'beginners': 'beginners with simple explanations and foundational concepts',
                'intermediate': 'intermediate readers with moderate complexity',
                'advanced': 'advanced readers with sophisticated concepts and terminology',
                'professionals': 'industry professionals with technical depth and expertise'
            }

            content_type_instructions = {
                'story': 'a narrative story with plot, characters, and engaging storytelling',
                'blog': 'a blog post with engaging hooks, clear sections, and conversational flow',
                'article': 'an informative article with structured sections and well-researched content',
                'creative': 'creative writing with artistic expression and imaginative elements',
                'noir': 'a noir mystery with atmospheric tension, compelling characters, and shadowy intrigue',
                'character': 'character development with psychological depth, motivations, and backstory',
                'outline': 'a structured story outline with plot points, character arcs, and scene breakdowns'
            }

            style_desc = style_descriptions.get(writing_style, style_descriptions['noir'])
            length_target = length_targets.get(content_length, '800-1200 words')
            audience_desc = audience_descriptions.get(target_audience, 'general audience')
            content_instruction = content_type_instructions.get(content_type, 'engaging content')

            system_prompt = f"""You are a professional writing assistant. Transform the provided text into {content_instruction}.

Writing Requirements:
- Style: {style_desc}
- Target Length: {length_target}
- Target Audience: {audience_desc}
- Maintain the original message and intent
- Create engaging, well-structured content
- Use appropriate vocabulary and tone for the audience level"""

            max_tokens_map = {'short': 800, 'medium': 2000, 'long': 3500}
            max_tokens = max_tokens_map.get(content_length, 2000)

            message = self.anthropic_client.messages.create(
                model=self.preferred_model,
                max_tokens=max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": f"Transform this into {content_instruction}:\n\n{text}"
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
