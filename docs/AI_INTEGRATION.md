# AI Integration Guide - Opinian Platform

## Overview
The Opinian platform now includes OpenAI integration for AI-powered content generation features. This guide explains how to configure and use the AI capabilities.

## Configuration

### 1. Install Required Package
```bash
pip install openai==1.12.0
```

Or install from requirements.txt:
```bash
pip install -r requirements.txt
```

### 2. Configure OpenAI API Key

Edit your `.env` file and add your OpenAI API key:

```env
# API Configuration (OpenAI)
OPENAI_API_KEY=sk-proj-your-actual-api-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=2000
```

**Configuration Options:**
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `OPENAI_MODEL`: The model to use (default: `gpt-4o-mini`)
  - Options: `gpt-4o-mini`, `gpt-4o`, `gpt-3.5-turbo`, etc.
- `OPENAI_MAX_TOKENS`: Maximum tokens for generation (default: 2000)

### 3. Get Your OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in to your account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key and add it to your `.env` file

## Features

### 1. Blog Content Generation

**Endpoint:** `POST /blog/generate-content`

Generate complete blog posts based on a topic or idea.

**Request:**
```json
{
  "prompt": "The future of artificial intelligence in healthcare",
  "content_type": "blog_post"
}
```

**Content Types:**
- `blog_post`: Standard blog post format
- `article`: Long-form article format
- `story`: Narrative storytelling format

**Response:**
```json
{
  "success": true,
  "content": "<h2>Title</h2><p>Content...</p>",
  "word_count": 450,
  "estimated_reading_time": 2,
  "model": "gpt-4o-mini"
}
```

### 2. Title Suggestions

**Endpoint:** `POST /blog/generate-titles`

Generate multiple title options for your blog post.

**Request:**
```json
{
  "topic": "sustainable living tips",
  "count": 5
}
```

**Response:**
```json
{
  "success": true,
  "titles": [
    "10 Simple Ways to Live More Sustainably",
    "The Ultimate Guide to Eco-Friendly Living",
    "Sustainable Living: Small Changes, Big Impact",
    "How to Reduce Your Carbon Footprint Today",
    "Green Living Made Easy: Practical Tips"
  ]
}
```

### 3. Content Improvement

**Endpoint:** `POST /blog/improve-content`

Enhance existing content with AI suggestions.

**Request:**
```json
{
  "content": "Your existing blog content here...",
  "instructions": "Make it more engaging and add examples"
}
```

**Response:**
```json
{
  "success": true,
  "content": "<improved content>",
  "word_count": 520
}
```

### 4. Excerpt Generation

**Endpoint:** `POST /blog/generate-excerpt`

Automatically generate compelling excerpts from full content.

**Request:**
```json
{
  "content": "Your full blog post content...",
  "max_length": 200
}
```

**Response:**
```json
{
  "success": true,
  "excerpt": "A compelling summary of your blog post..."
}
```

## API Endpoints (REST API)

For external integrations, use the REST API endpoint:

**Endpoint:** `POST /api/ai/generate`

**Headers:**
```
Authorization: Bearer <your-jwt-token>
Content-Type: application/json
```

**Request:**
```json
{
  "prompt": "Your content topic",
  "content_type": "blog_post"
}
```

## Fallback Mode

If OpenAI API key is not configured, the system will automatically fall back to placeholder content with instructions on how to enable AI features. This ensures the platform remains functional even without AI capabilities.

## Cost Considerations

### Token Usage
- Average blog post: ~500-1000 tokens
- Title generation: ~100-200 tokens
- Content improvement: ~1000-2000 tokens (depending on content length)

### Pricing (as of 2024)
- **GPT-4o-mini**: $0.150 / 1M input tokens, $0.600 / 1M output tokens
- **GPT-4o**: $2.50 / 1M input tokens, $10.00 / 1M output tokens

**Recommendation:** Use `gpt-4o-mini` for cost-effective content generation with good quality.

## Best Practices

### 1. Clear Prompts
Provide specific, detailed prompts for better results:
- ✅ "Write a comprehensive guide about organic gardening for beginners, including soil preparation and common vegetables"
- ❌ "Write about gardening"

### 2. Content Review
Always review AI-generated content before publishing:
- Check for accuracy
- Verify tone and style alignment
- Add personal insights
- Update with current information

### 3. Rate Limiting
Implement rate limiting for AI requests to manage costs:
- Set user quotas
- Monitor usage patterns
- Cache frequent requests

### 4. Error Handling
The AI service includes comprehensive error handling:
- API key validation
- Fallback content
- Detailed error messages
- Activity logging

## Troubleshooting

### Common Issues

**1. "OpenAI API key not configured"**
- Check your `.env` file
- Ensure the key starts with `sk-`
- Restart the Flask application

**2. "Rate limit exceeded"**
- Wait a few minutes and retry
- Upgrade your OpenAI plan if needed
- Implement request throttling

**3. "Invalid API key"**
- Verify the key is correct
- Check if the key is active in OpenAI dashboard
- Regenerate the key if necessary

**4. "Connection timeout"**
- Check your internet connection
- Verify OpenAI API status
- Increase timeout settings if needed

## Security Notes

- Never commit your `.env` file to version control
- Add `.env` to `.gitignore`
- Use environment variables in production
- Rotate API keys regularly
- Monitor API usage for anomalies

## Support

For issues or questions:
1. Check the [OpenAI Documentation](https://platform.openai.com/docs)
2. Review application logs
3. Contact platform administrators

## Future Enhancements

Planned features:
- Multiple AI provider support (Anthropic, Cohere, etc.)
- Image generation integration
- Content tone customization
- Multi-language support
- SEO optimization suggestions
- Plagiarism checking
