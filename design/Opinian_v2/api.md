# Opinian Platform - API Endpoints Documentation

## API Architecture Overview

The Opinian platform uses a RESTful API architecture with JSON data exchange. All endpoints are versioned and follow consistent naming conventions for predictability and maintainability.

**Base URL:** `https://api.opinian.com/v1`
**Authentication:** JWT Bearer tokens
**Content-Type:** `application/json`

## Authentication Endpoints

### 1. User Registration
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "securePassword123!",
  "firstName": "John",
  "lastName": "Doe",
  "displayName": "John Doe"
}

Response:
{
  "success": true,
  "message": "Registration successful. Please check your email to verify your account.",
  "data": {
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "johndoe"
  }
}
```

### 2. User Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securePassword123!"
}

Response:
{
  "success": true,
  "message": "Login successful",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "username": "johndoe",
      "displayName": "John Doe",
      "role": "author",
      "avatarUrl": null,
      "preferences": {}
    }
  }
}
```

### 3. Token Refresh
```http
POST /auth/refresh
Content-Type: application/json

{
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

Response:
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

### 4. Token Validation
```http
GET /auth/validate
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

Response:
{
  "success": true,
  "data": {
    "valid": true,
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "username": "johndoe",
      "role": "author"
    }
  }
}
```

### 5. Password Reset
```http
POST /auth/password-reset
Content-Type: application/json

{
  "email": "user@example.com"
}

Response:
{
  "success": true,
  "message": "Password reset email sent"
}
```

## Blog Management Endpoints

### 6. Create Blog Post
```http
POST /blog/posts
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "title": "The Art of Noir Storytelling",
  "content": "<p>In the shadowy corners of the digital realm...</p>",
  "contentText": "In the shadowy corners of the digital realm...",
  "excerpt": "Discover the timeless appeal of noir storytelling...",
  "categories": ["writing", "storytelling"],
  "tags": ["noir", "blogging", "style"],
  "status": "draft",
  "visibility": "public",
  "metaTitle": "Noir Storytelling in Modern Blogging",
  "metaDescription": "Learn how to incorporate noir elements...",
  "featuredImage": "https://cdn.opinian.com/images/noir-hero.jpg"
}

Response:
{
  "success": true,
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "slug": "the-art-of-noir-storytelling",
    "title": "The Art of Noir Storytelling",
    "status": "draft",
    "createdAt": "2024-01-15T10:30:00Z",
    "updatedAt": "2024-01-15T10:30:00Z"
  }
}
```

### 7. Get Blog Posts (List)
```http
GET /blog/posts?page=1&limit=10&status=published&category=writing&search=noir
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

Response:
{
  "success": true,
  "data": {
    "posts": [
      {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "title": "The Art of Noir Storytelling",
        "slug": "the-art-of-noir-storytelling",
        "excerpt": "Discover the timeless appeal...",
        "featuredImage": "https://cdn.opinian.com/images/noir-hero.jpg",
        "author": {
          "id": "550e8400-e29b-41d4-a716-446655440000",
          "displayName": "John Doe",
          "avatarUrl": null
        },
        "categories": ["writing", "storytelling"],
        "tags": ["noir", "blogging", "style"],
        "publishedAt": "2024-01-15T10:30:00Z",
        "viewCount": 1542,
        "likeCount": 89,
        "commentCount": 12
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 156,
      "pages": 16
    }
  }
}
```

### 8. Get Single Blog Post
```http
GET /blog/posts/the-art-of-noir-storytelling
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

Response:
{
  "success": true,
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "title": "The Art of Noir Storytelling",
    "slug": "the-art-of-noir-storytelling",
    "content": "<p>In the shadowy corners...</p>",
    "contentText": "In the shadowy corners...",
    "excerpt": "Discover the timeless appeal...",
    "featuredImage": "https://cdn.opinian.com/images/noir-hero.jpg",
    "author": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "displayName": "John Doe",
      "username": "johndoe",
      "avatarUrl": null,
      "bio": "Passionate writer and storyteller..."
    },
    "categories": ["writing", "storytelling"],
    "tags": ["noir", "blogging", "style"],
    "status": "published",
    "publishedAt": "2024-01-15T10:30:00Z",
    "updatedAt": "2024-01-15T10:30:00Z",
    "viewCount": 1542,
    "likeCount": 89,
    "commentCount": 12,
    "shareCount": 45,
    "readingTime": 8,
    "wordCount": 1567,
    "aiAssisted": false
  }
}
```

### 9. Update Blog Post
```http
PUT /blog/posts/660e8400-e29b-41d4-a716-446655440001
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "title": "The Art of Noir Storytelling (Updated)",
  "content": "<p>In the shadowy corners of the digital realm...</p>",
  "status": "published"
}

Response:
{
  "success": true,
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "title": "The Art of Noir Storytelling (Updated)",
    "slug": "the-art-of-noir-storytelling",
    "status": "published",
    "updatedAt": "2024-01-15T11:45:00Z"
  }
}
```

### 10. Delete Blog Post
```http
DELETE /blog/posts/660e8400-e29b-41d4-a716-446655440001
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

Response:
{
  "success": true,
  "message": "Blog post deleted successfully"
}
```

## AI Generation Endpoints

### 11. Get AI Prompts
```http
GET /ai/prompts?category=content-creation
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

Response:
{
  "success": true,
  "data": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "name": "Blog Idea Generator",
      "category": "content-creation",
      "description": "Generate unique blog post ideas",
      "promptTemplate": "Generate 5 unique blog post ideas about {topic} for a {style} blog...",
      "variables": ["topic", "style"],
      "isActive": true,
      "usageCount": 1247
    }
  ]
}
```

### 12. Generate AI Content
```http
POST /ai/generate
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "promptId": "770e8400-e29b-41d4-a716-446655440002",
  "inputs": {
    "topic": "modern storytelling techniques",
    "style": "noir",
    "tone": "creative",
    "length": "medium",
    "audience": "general"
  }
}

Response:
{
  "success": true,
  "data": {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "title": "Shadows and Pixels: Modern Storytelling",
    "content": "<h2>Shadows and Pixels: Modern Storytelling</h2><p>In the digital age...</p>",
    "wordCount": 1156,
    "readingTime": 6,
    "suggestions": [
      "Consider adding more personal anecdotes",
      "Include relevant statistics about digital storytelling"
    ],
    "generatedAt": "2024-01-15T12:00:00Z"
  }
}
```

### 13. Enhance Existing Content
```http
POST /ai/enhance
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "content": "<p>This is my blog post about storytelling...</p>",
  "promptId": "770e8400-e29b-41d4-a716-446655440002",
  "enhancementType": "improve-writing"
}

Response:
{
  "success": true,
  "data": {
    "originalContent": "<p>This is my blog post about storytelling...</p>",
    "enhancedContent": "<p>In the shadowy realm of digital narratives...</p>",
    "changes": [
      "Improved vocabulary and sentence structure",
      "Added more engaging opening"
    ],
    "confidence": 0.85,
    "enhancedAt": "2024-01-15T12:30:00Z"
  }
}
```

## Media Management Endpoints

### 14. Upload Media File
```http
POST /media/upload
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: multipart/form-data

Form Data:
- file: [binary file data]
- filename: "noir-hero.jpg"
- mimeType: "image/jpeg"

Response:
{
  "success": true,
  "data": {
    "id": "990e8400-e29b-41d4-a716-446655440004",
    "filename": "noir-hero.jpg",
    "originalName": "noir-hero.jpg",
    "mimeType": "image/jpeg",
    "fileSize": 245678,
    "url": "https://cdn.opinian.com/media/990e8400-e29b-41d4-a716-446655440004.jpg",
    "thumbnailUrl": "https://cdn.opinian.com/media/thumb_990e8400-e29b-41d4-a716-446655440004.jpg",
    "dimensions": {
      "width": 1920,
      "height": 1080
    },
    "uploadedAt": "2024-01-15T13:00:00Z"
  }
}
```

### 15. Get User Media Files
```http
GET /media/files?page=1&limit=20
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

Response:
{
  "success": true,
  "data": {
    "files": [
      {
        "id": "990e8400-e29b-41d4-a716-446655440004",
        "filename": "noir-hero.jpg",
        "originalName": "noir-hero.jpg",
        "mimeType": "image/jpeg",
        "fileSize": 245678,
        "url": "https://cdn.opinian.com/media/990e8400-e29b-41d4-a716-446655440004.jpg",
        "thumbnailUrl": "https://cdn.opinian.com/media/thumb_990e8400-e29b-41d4-a716-446655440004.jpg",
        "uploadedAt": "2024-01-15T13:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 45,
      "pages": 3
    }
  }
}
```

### 16. Delete Media File
```http
DELETE /media/files/990e8400-e29b-41d4-a716-446655440004
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

Response:
{
  "success": true,
  "message": "Media file deleted successfully"
}
```

## Admin Dashboard Endpoints

### 17. Get Analytics Summary
```http
GET /admin/analytics/summary?period=7d
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

Response:
{
  "success": true,
  "data": {
    "period": "7d",
    "metrics": {
      "totalUsers": 1247,
      "activeUsers": 892,
      "newUsers": 156,
      "totalPosts": 2340,
      "publishedPosts": 2156,
      "totalViews": 45678,
      "totalLikes": 3456,
      "totalComments": 890,
      "bounceRate": 0.34,
      "avgSessionDuration": 245
    },
    "trends": {
      "users": 12.5,
      "posts": 8.3,
      "views": 15.7,
      "engagement": 22.1
    }
  }
}
```

### 18. Get User Management Data
```http
GET /admin/users?page=1&limit=20&role=author&status=active
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

Response:
{
  "success": true,
  "data": {
    "users": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "user@example.com",
        "username": "johndoe",
        "displayName": "John Doe",
        "role": "author",
        "status": "active",
        "lastLogin": "2024-01-15T10:30:00Z",
        "createdAt": "2024-01-01T00:00:00Z",
        "postCount": 15,
        "totalViews": 3456
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 892,
      "pages": 45
    }
  }
}
```

### 19. Update User Status
```http
PUT /admin/users/550e8400-e29b-41d4-a716-446655440000/status
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "status": "suspended",
  "reason": "Violation of community guidelines"
}

Response:
{
  "success": true,
  "message": "User status updated successfully"
}
```

### 20. Get Content Moderation Queue
```http
GET /admin/moderation/queue?type=posts&status=pending&page=1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

Response:
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "type": "post",
        "title": "Controversial Blog Post",
        "author": {
          "id": "550e8400-e29b-41d4-a716-446655440000",
          "displayName": "John Doe"
        },
        "status": "pending",
        "flaggedReason": "potentially_sensitive_content",
        "createdAt": "2024-01-15T14:00:00Z",
        "contentPreview": "This post discusses controversial topics..."
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 8,
      "pages": 1
    }
  }
}
```

## LLM Configuration Endpoints

### 21. Get LLM Providers
```http
GET /admin/llm/providers
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

Response:
{
  "success": true,
  "data": [
    {
      "id": "aa0e8400-e29b-41d4-a716-446655440005",
      "provider": "OpenAI",
      "modelName": "gpt-4",
      "endpointUrl": "https://api.openai.com/v1/chat/completions",
      "isActive": true,
      "isDefault": true,
      "costPerToken": 0.00006,
      "createdAt": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 22. Add LLM Provider
```http
POST /admin/llm/providers
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "provider": "Anthropic",
  "apiKey": "sk-ant-...",
  "modelName": "claude-3-sonnet",
  "endpointUrl": "https://api.anthropic.com/v1/messages",
  "additionalParams": {
    "maxTokens": 4000
  },
  "costPerToken": 0.00003
}

Response:
{
  "success": true,
  "data": {
    "id": "bb0e8400-e29b-41d4-a716-446655440006",
    "provider": "Anthropic",
    "modelName": "claude-3-sonnet",
    "isActive": true,
    "createdAt": "2024-01-15T15:00:00Z"
  }
}
```

### 23. Update AI Prompts
```http
PUT /admin/ai/prompts/770e8400-e29b-41d4-a716-446655440002
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "promptTemplate": "Generate 5 unique blog post ideas about {topic}...",
  "temperature": 0.8,
  "maxTokens": 2000
}

Response:
{
  "success": true,
  "message": "Prompt updated successfully"
}
```

## Error Responses

All endpoints return consistent error responses:

```http
HTTP/1.1 400 Bad Request
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "email": "Email is required"
    }
  }
}
```

```http
HTTP/1.1 401 Unauthorized
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or expired token"
  }
}
```

```http
HTTP/1.1 403 Forbidden
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "Insufficient permissions"
  }
}
```

```http
HTTP/1.1 404 Not Found
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource not found"
  }
}
```

```http
HTTP/1.1 429 Too Many Requests
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later.",
    "retryAfter": 60
  }
}
```

```http
HTTP/1.1 500 Internal Server Error
{
  "success": false,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred"
  }
}
```

## Rate Limiting

- **Authentication endpoints**: 10 requests per minute per IP
- **Blog operations**: 30 requests per minute per user
- **AI generation**: 5 requests per minute per user
- **Media uploads**: 10 files per minute per user
- **Admin operations**: 60 requests per minute per user

## WebSocket Endpoints

For real-time features, the platform supports WebSocket connections:

### Real-time Notifications
```javascript
// Connection URL
wss://api.opinian.com/v1/notifications

// Authentication
{
  "type": "auth",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

// Incoming notifications
{
  "type": "notification",
  "data": {
    "id": "cc0e8400-e29b-41d4-a716-446655440007",
    "type": "new_comment",
    "title": "New comment on your post",
    "message": "Jane Doe commented on 'The Art of Noir Storytelling'",
    "timestamp": "2024-01-15T16:00:00Z"
  }
}
```

### Real-time Analytics
```javascript
// Connection URL
wss://api.opinian.com/v1/analytics

// Real-time stats updates
{
  "type": "analytics_update",
  "data": {
    "pageViews": 156,
    "activeUsers": 23,
    "newPosts": 2,
    "topPost": {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "title": "The Art of Noir Storytelling",
      "views": 89
    }
  }
}
```

This comprehensive API documentation provides the foundation for seamless frontend-backend communication in the Opinian platform, ensuring robust functionality for all user interactions, content management, AI integration, and administrative operations.