# Opinian SaaS Blogging Platform - Requirements Document

## 1. Executive Summary
Opinian is a multi-tenant SaaS blogging platform that enables organizations to create branded blogging environments with hierarchical user management, AI-powered content creation, and customizable themes.

## 2. Functional Requirements

### 2.1 User Management System
- **User Roles & Hierarchy:**
  - SuperAdmin: Platform-wide authority, can create groups/organizations
  - Admin User: Can create users and super users within their group
  - Super User: Can create pages and has extended permissions
  - User: Basic blogging and reading capabilities

- **User Permissions Dashboard:**
  - Matrix view of all users with roles and status
  - Ability to edit user permissions
  - User activity logs
  - Ban/suspend functionality
  - Individual user profile pages

### 2.2 Multi-Tenant Architecture
- **Group/Organization System:**
  - Each Admin user creates a group representing their organization
  - Groups function as tenant boundaries
  - Isolated content and user management per group

### 2.3 Content Management
- **Blog System:**
  - Users can create and publish blog articles
  - Articles are posted to existing pages
  - Content moderation tools

- **Page Creation:**
  - Super Users, Admin Users, and SuperAdmins can create pages
  - WordPress-style page creation
  - Template-based page structure

### 2.4 Theme Management
- **AI-Powered Theme Creation:**
  - Prompt-based theme definition
  - Visual editor for theme customization
  - Group-specific theme application
  - Drag-and-drop component management

- **Visual Editor Features:**
  - Code view with HTML/React export
  - Table, form, and image insertion
  - File upload capabilities
  - Responsive design preview

### 2.5 AI Writing Assistant
- **Content Generation:**
  - Blog idea input and AI rewriting
  - Export to blog, Word doc, or text file
  - Integration with main blogging system

### 2.6 Administrative Features
- **Super Admin Dashboard:**
  - API settings management for LLM
  - Platform-wide configuration
  - User management across all groups

- **Group Management:**
  - Contact Us page (template-based, editable)
  - About Us page (template-based, editable)
  - Admin Dashboard for theme creation

## 3. Non-Functional Requirements

### 3.1 Security
- Secure authentication and authorization
- Role-based access control (RBAC)
- Data isolation between tenants
- Input validation and sanitization

### 3.2 Performance
- Responsive design for desktop and mobile
- Efficient database queries
- Scalable architecture

### 3.3 User Experience
- 1920s 'flapper' style mixed with 1940s 'noir' aesthetic
- Intuitive navigation
- Consistent design language

## 4. Technical Requirements

### 4.1 Backend
- Python with Flask framework
- PostgreSQL database
- RESTful API architecture
- JWT-based authentication

### 4.2 Frontend
- HTML5 with Jinja2 templating
- JavaScript for interactivity
- CSS with 1920s/1940s aesthetic
- Responsive design

### 4.3 Database
- User management tables
- Content storage
- Theme and template storage
- Activity logging

## 5. Integration Requirements
- LLM API integration for AI features
- File upload and storage
- Export functionality (HTML, React, Word)

## 6. Success Criteria
- Multi-tenant isolation achieved
- All user roles functional with proper permissions
- Theme system operational
- AI writing assistant integrated
- Responsive design implemented
- All CRUD operations working