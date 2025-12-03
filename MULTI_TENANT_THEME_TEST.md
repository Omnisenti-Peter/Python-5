# Multi-Tenant Theme Testing Guide

## Current Situation
- **Group:** Friends (ID: 1)
- **Theme:** Modern SaaS Vibe
- **Members:** admin (SuperAdmin), imran (User)
- **Result:** Both see the same theme ✅ CORRECT!

## Test Scenario: Create a Second Group

### Step 1: Create New Group
1. Login as **admin** (SuperAdmin)
2. Go to Admin → Manage Groups
3. Create new group: **"Work Team"**
4. Assign admin as group administrator

### Step 2: Create Different Theme
1. Go to Themes → AI Assistant
2. Describe: "Dark professional theme with deep navy blues and orange accents"
3. Generate theme (name it "Corporate Dark")
4. Save theme

### Step 3: Assign Theme to New Group
1. Go to Admin → Manage Groups
2. Edit **"Work Team"** group
3. Select theme: **"Corporate Dark"**
4. Save

### Step 4: Create User in New Group
1. Go to Admin → Manage Users
2. Create user: **"john"**
3. Email: john@example.com
4. Password: Test123!
5. **Important:** Set group_id = **Work Team**
6. Role: User
7. Save

### Step 5: Test Theme Isolation

**Test A: Admin in Friends Group**
1. Make sure admin's group_id = 1 (Friends)
2. Login as admin
3. Should see: **Modern SaaS Vibe** theme
4. Colors: Purple/Indigo

**Test B: John in Work Team Group**
1. Login as **john**
2. Should see: **Corporate Dark** theme
3. Colors: Navy blue/Orange
4. **Different from admin!**

**Test C: Imran in Friends Group**
1. Login as **imran**
2. Should see: **Modern SaaS Vibe** theme (same as admin)
3. Colors: Purple/Indigo

## Expected Results

| User  | Group      | Theme             | Colors          |
|-------|------------|-------------------|-----------------|
| admin | Friends    | Modern SaaS Vibe  | Purple/Indigo   |
| imran | Friends    | Modern SaaS Vibe  | Purple/Indigo   |
| john  | Work Team  | Corporate Dark    | Navy/Orange     |

## How to Move Admin to Different Group

If you want admin to see a DIFFERENT theme than imran:

### Option 1: Change Admin's Group
```sql
-- Move admin to Work Team
UPDATE users SET group_id = 2 WHERE username = 'admin';
```
Now:
- **admin** sees Work Team's theme
- **imran** sees Friends' theme
- They see **different themes!**

### Option 2: Create SuperAdmin Without Group
```sql
-- Remove admin from any group
UPDATE users SET group_id = NULL WHERE username = 'admin';
```
Now:
- **admin** sees default theme (no group)
- **imran** sees Friends' theme

## Verification Query

Run this to check who sees what:

```sql
SELECT
    u.username,
    u.email,
    r.name as role,
    g.name as group_name,
    t.name as theme_name,
    t.theme_type
FROM users u
LEFT JOIN roles r ON u.role_id = r.id
LEFT JOIN groups g ON u.group_id = g.id
LEFT JOIN themes t ON g.theme_id = t.id
WHERE u.is_active = TRUE
ORDER BY g.name, u.username;
```

## Database Structure

```
users table:
- id
- username
- group_id  ← Points to groups table

groups table:
- id
- name
- theme_id  ← Points to themes table

themes table:
- id
- name
- css_variables (JSON with colors)
- custom_css
```

## Theme Application Logic

```python
# When user logs in (app.py):
session['group_id'] = user.group_id

# Context processor (app.py):
@app.context_processor
def inject_active_theme():
    theme = get_active_theme(session['group_id'])
    return {'active_theme': theme}

# Get active theme function (app.py):
def get_active_theme(group_id):
    SELECT t.* FROM themes t
    JOIN groups g ON g.theme_id = t.id
    WHERE g.id = group_id
```

## Conclusion

**Your current setup is working CORRECTLY!**

- Admin and imran are BOTH in "Friends" group
- Both see the same theme
- This is proper multi-tenant behavior

To see **different themes**, users must belong to **different groups**.
