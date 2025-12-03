# Opinian Platform - System Workflow

## Initial Setup Flow

### 0. Platform Initialization Workflow
```
Deploy Application → Configure .env → Run init_db.py → Creates Database & Tables & Roles
                                                              ↓
                                              Prompts for SuperAdmin Credentials
                                              (or uses environment variables)
                                                              ↓
                                              Creates First SuperAdmin → Setup Complete
                                                              ↓
                                              Start app.py → SuperAdmin Login → Platform Ready
```

**Steps:**
1. `python init_db.py` - Creates database, tables, roles, permissions, AND SuperAdmin
   - Interactive mode: Prompts for credentials
   - Automated mode: Uses environment variables
2. `python app.py` - Start the application
3. SuperAdmin logs in via web interface at http://localhost:5000/login
4. Platform is ready for use

---

## User Flow Diagrams

### 1. User Registration and Authentication Flow

**Public Self-Registration (Creates "User" role):**
```
User → /register → Fill Form → Validate Input → Create User → Assign "User" Role → Success → /login
                                      ↓
                                  Error → Show Message → /register
```

**Admin-Created Users (Any role):**
```
Admin/SuperAdmin → /admin/users/create → Fill Form → Select Role → Create User → Email Credentials
                                                           ↓
                                                   User receives credentials → Login → Dashboard
```

### 2. User Hierarchy and Permission Flow
```
Initial Setup → create_superadmin.py → First SuperAdmin Created
                                              ↓
SuperAdmin → Creates Admin Users → Assigns to Groups → Admin Logs In
                ↓                                            ↓
    Platform-wide Management                   Admin Creates SuperUsers/Users in Group
                ↓                                            ↓
    API Settings, All Groups                        Group Content & Theme Management
            User Management                                  ↓
                                                    Regular Users Create Blog Posts
```

**Role Capabilities:**
- **SuperAdmin:** Full platform control, create/manage all groups and users, API settings
- **Admin:** Manage one group, create users within group, manage group content and themes
- **SuperUser:** Create pages and blog posts with extended permissions
- **User:** Create blog posts on existing pages

### 3. Content Creation Workflow
```
User → Choose Content Type → Blog Post/Page → Write Content → AI Assistant (Optional) → Review → Publish
                                      ↓
Super User → Create New Page → Add Content → Configure Theme → Publish Page
```

### 4. Theme Management Flow
```
Admin User → Access Theme Editor → Choose Creation Method:
                                      ↓
    AI Prompt → Generate Theme → Preview → Apply to Group
                                      ↓
    Manual Design → Visual Editor → Code View → Export/Save → Apply Theme
```

### 5. AI Writing Assistant Flow
```
User → Input Blog Idea → AI Processing → Generate Content → Review/Edit → Export Options:
                                                                      ↓
                                                        Publish to Blog | Download as Word | Download as Text
```

## System Architecture Flow

### 6. Multi-Tenant Data Flow
```
Request → Authentication → Tenant Identification → Data Isolation → Process Request → Return Response
                                      ↓
Group-Based Filtering → Content Filtering → User Permission Check
```

### 7. API Request Flow
```
Frontend Request → API Gateway → Authentication Middleware → Route Handling → Business Logic → Database Operations → Response → Frontend
```

## Administrative Workflow

### 8. User Management Flow
```
Admin → Access Dashboard → View User Matrix → Select User → Modify Permissions → Save Changes → Log Activity
```

**For detailed user management procedures, see [USER_MANAGEMENT.md](USER_MANAGEMENT.md)**

**User Creation Methods:**
1. **First SuperAdmin:** Automatically prompted during `init_db.py` (one-time setup)
   - Interactive: Type credentials when prompted
   - Automated: Set credentials in `.env` file
2. **Admin Users:** Created by SuperAdmin via `/admin/users/create`
3. **SuperUser/User:** Created by SuperAdmin or Admin via `/admin/users/create`
4. **Self-Registration:** Public users register at `/register` (always gets "User" role)

**Environment Variable Setup (Optional):**
- Set `SUPERADMIN_USERNAME`, `SUPERADMIN_EMAIL`, `SUPERADMIN_PASSWORD` in `.env`
- `init_db.py` will use these for automated SuperAdmin creation (useful for CI/CD)
- See [SECURITY.md](SECURITY.md) for credential management best practices

### 9. Content Moderation Flow
```
Moderator → Review Queue → Content Review → Approve/Reject → Notify User → Update Content Status
```

### 10. System Monitoring Flow
```
System → Activity Logging → Performance Monitoring → Error Tracking → Admin Notifications → Maintenance Actions
```

## Data Relationships

### 11. Database Entity Relationships
```
Users → Groups → Organizations → Content → Themes → Settings
  ↓        ↓         ↓           ↓        ↓         ↓
Roles → Permissions → Templates → Media → Logs → Configurations
```

## Error Handling Flows

### 12. Error Management
```
Error Occurs → Log Error → User Notification → Recovery Actions → Continue Operation
                    ↓
                Admin Alert → System Monitoring
```

## Integration Points

### 13. External API Integration
```
Platform → LLM API → Process Request → Return Response → Integration Layer → Business Logic
                    ↓
                Error Handling → Fallback Mechanisms
```