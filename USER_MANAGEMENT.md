# User Management Guide - Opinian Platform

## User Role Hierarchy

The Opinian platform has 4 user roles with different permission levels:

| Role | Level | Permissions |
|------|-------|-------------|
| **SuperAdmin** | 1 (Highest) | Full platform control, create groups/organizations, manage all users, API settings |
| **Admin** | 2 | Manage their group, create users within group, manage group content and themes |
| **SuperUser** | 3 | Create pages and blog posts, extended content permissions |
| **User** | 4 (Basic) | Create blog posts, view content |

## User Creation Methods

### 1. Creating the First SuperAdmin

**When to use:** Initial platform setup, server deployment

**Method 1: Integrated with Database Setup (Recommended)**

Run the database initialization script which includes SuperAdmin creation:

```bash
python init_db.py
```

The script will:
- Create database and tables
- Set up roles and permissions
- Check if SuperAdmin already exists
- Prompt for SuperAdmin credentials (interactive mode)
- OR use environment variables for automated deployment
- Create the SuperAdmin user
- Confirm creation

**Interactive Example:**
```
🚀 Opinian Platform - Database Initialization
============================================================
Database opinian created successfully
All tables created successfully
Initial data inserted successfully
Database indexes created successfully

✅ Database initialization completed successfully!
============================================================

🔐 SuperAdmin Creation
============================================================
No SuperAdmin credentials found in environment variables.
Please provide SuperAdmin details:

Username: admin
Email: admin@opinian.com
Password: ********
Confirm Password: ********
First Name (default: Super): John
Last Name (default: Admin): Doe

✅ SuperAdmin user created successfully!
   User ID: 1
   Username: admin
   Email: admin@opinian.com
   Name: John Doe
```

**Method 2: Using Environment Variables (For Automated Deployment)**

Add to your `.env` file:
```env
SUPERADMIN_USERNAME=admin
SUPERADMIN_EMAIL=admin@opinian.com
SUPERADMIN_PASSWORD=your_secure_password
SUPERADMIN_FIRST_NAME=John
SUPERADMIN_LAST_NAME=Doe
```

Then run:
```bash
python init_db.py
```

The script will automatically use these credentials without prompting.

---

> 🔐 **Security Note:** See [SECURITY.md](SECURITY.md) for how to safely store and manage SuperAdmin credentials.

### 2. Creating Admin Users

**Who can do this:** SuperAdmin only

**Method:** Admin panel at `/admin/users/create`

**Steps:**
1. Log in as SuperAdmin
2. Navigate to **Admin Dashboard** → **Users** → **Create User**
3. Fill in user details:
   - Username
   - Email
   - Password
   - First Name
   - Last Name
   - **Select Role:** Admin
4. Click **Create User**

**Important Notes:**
- Admin users can create groups/organizations
- Each Admin typically manages one group
- Admins can only manage users within their own group

---

### 3. Creating SuperUser and Regular Users

**Who can do this:** SuperAdmin OR Admin

**Method:** Admin panel at `/admin/users/create`

**Steps:**
1. Log in as SuperAdmin or Admin
2. Navigate to **Admin Dashboard** → **Users** → **Create User**
3. Fill in user details
4. **Select Role:** SuperUser or User
5. Click **Create User**

**Permissions:**
- **SuperAdmin:** Can create users in any group
- **Admin:** Can only create users within their own group

---

### 4. Self-Registration (Public)

**Who can do this:** Anyone visiting the site

**Method:** Public registration at `/register`

**Steps:**
1. Visit the registration page
2. Fill in:
   - Username
   - Email
   - Password
   - First Name
   - Last Name
3. Click **Register**
4. User is automatically created with **"User"** role
5. Redirect to login page

**Important Notes:**
- Self-registered users always get the basic "User" role
- They are not assigned to any group initially
- Admins can later assign them to groups and change roles

---

## User Management Workflows

### Scenario 1: New Platform Deployment

**Local Development:**
```
1. Deploy application to local machine
2. Configure .env file with database credentials
3. Run: python init_db.py
4. Provide SuperAdmin credentials when prompted
5. Run: python app.py
6. Log in as SuperAdmin
7. Create Admin users for each organization
8. Admins create their groups/organizations
9. Admins create SuperUsers and Users for their groups
```

**Server/Production Deployment:**
```
1. Deploy application to server
2. Configure .env file with database and SuperAdmin credentials
3. Run: python init_db.py (uses environment variables)
4. SuperAdmin credentials are created automatically
5. Start application with production server (gunicorn)
6. Log in as SuperAdmin
7. Create Admin users for each organization
8. Admins create their groups/organizations
9. Admins create SuperUsers and Users for their groups
```

### Scenario 2: Adding a New Organization

```
1. SuperAdmin creates an Admin user
2. Admin user logs in
3. Admin creates their group/organization
4. Admin customizes group settings (theme, pages, etc.)
5. Admin creates SuperUsers and regular Users
6. Users can also self-register and Admin assigns them to group
```

### Scenario 3: User Wants to Join

```
Option A - Self Registration:
1. User visits /register
2. Fills in details and registers
3. Gets "User" role automatically
4. Admin can later assign them to a group and upgrade role

Option B - Admin Creation:
1. Admin creates user account directly
2. Admin assigns role and group immediately
3. Admin sends credentials to user
4. User logs in with provided credentials
```

---

## Role Upgrade/Downgrade

**Who can do this:** SuperAdmin or Admin

**Method:** Edit user at `/admin/users/edit/<user_id>`

**Steps:**
1. Navigate to **Admin Dashboard** → **Users**
2. Click **Edit** on the user you want to modify
3. Change the **Role** dropdown
4. Click **Update User**

**Restrictions:**
- Admins can only modify users in their own group
- SuperAdmins can modify any user

---

## Security Best Practices

### For SuperAdmin Creation:
1. ✅ Use strong passwords (minimum 8 characters)
2. ✅ Use a secure email address
3. ✅ Run `create_superadmin.py` only once initially
4. ✅ Keep the script for future server deployments
5. ✅ Delete or secure the script in production if not needed

### For User Management:
1. ✅ Only create Admin users for trusted organization managers
2. ✅ Regularly review user permissions via Admin Dashboard
3. ✅ Use the ban feature for problematic users
4. ✅ Monitor activity logs for suspicious behavior
5. ✅ Assign users to groups to maintain tenant isolation

---

## Troubleshooting

### Problem: Can't create SuperAdmin - Role not found
**Solution:** Run `python init_db.py` to create the roles table first

### Problem: SuperAdmin already exists
**Solution:** The script will warn you. You can:
- Use existing SuperAdmin credentials
- Create another SuperAdmin if needed
- Reset existing SuperAdmin password via database

### Problem: Admin can't create users
**Solution:** Check that:
- Admin is logged in correctly
- Admin has a group assigned
- Admin is accessing `/admin/users/create`

### Problem: Self-registered users not appearing
**Solution:**
- Check database connection
- Verify user table has data
- Self-registered users won't appear in group-filtered views until assigned

---

## Database Schema Reference

### Users Table
```sql
users (
    id,
    username,
    email,
    password_hash,
    role_id → references roles(id),
    group_id → references groups(id),
    is_active,
    is_banned
)
```

### Roles Table
```sql
roles (
    id,
    name,  -- 'SuperAdmin', 'Admin', 'SuperUser', 'User'
    description,
    permissions (JSONB)
)
```

### Default Role IDs (after init_db.py):
- SuperAdmin: ID 1
- Admin: ID 2
- SuperUser: ID 3
- User: ID 4

---

## API Endpoints Summary

| Endpoint | Method | Access | Purpose |
|----------|--------|--------|---------|
| `/register` | GET/POST | Public | Self-registration (creates User role) |
| `/login` | GET/POST | Public | User authentication |
| `/admin/users` | GET | SuperAdmin, Admin | View all users |
| `/admin/users/create` | GET/POST | SuperAdmin, Admin | Create new user with any role |
| `/admin/users/edit/<id>` | GET/POST | SuperAdmin, Admin | Edit user details and role |
| `/admin/users/ban/<id>` | POST | SuperAdmin, Admin | Ban/unban user |
| `/admin/groups` | GET | SuperAdmin | View all groups |

---

## Quick Reference Commands

```bash
# Initial setup - ONE COMMAND DOES IT ALL
python init_db.py              # Creates database, tables, roles, and SuperAdmin

# Start application
python app.py                  # Run Flask development server
gunicorn -w 4 app:app          # Run production server

# Database access (if needed)
psql -U postgres -d opinian    # Connect to database directly

# Password reset (if needed)
# See SECURITY.md for password reset procedures
```

**Environment Variables for Automated Setup:**
```bash
# Add to .env for automated SuperAdmin creation
SUPERADMIN_USERNAME=admin
SUPERADMIN_EMAIL=admin@example.com
SUPERADMIN_PASSWORD=secure_password_here
SUPERADMIN_FIRST_NAME=Super
SUPERADMIN_LAST_NAME=Admin
```

---

## Support

For issues or questions about user management:
1. Check this documentation
2. Review the REQUIREMENTS.md file
3. Check application logs
4. Verify database connection and table structure
