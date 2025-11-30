# Security Guide - Credential Management

## 🔐 SuperAdmin Credentials - How to Store Safely

### Understanding How Credentials Work

When you create a SuperAdmin, here's what happens:

```
You type: username = "admin", password = "MyPassword123"
         ↓
System hashes password: "MyPassword123" → "$2b$12$xyz..." (encrypted)
         ↓
Database stores: username="admin", password_hash="$2b$12$xyz..."
         ↓
Original password is NEVER saved anywhere!
```

**Important:** The system **CANNOT recover** your password. You must remember it or save it securely!

---

## 📋 Two Ways to Create SuperAdmin

### Method 1: Interactive Mode (Recommended for Local Development)

```bash
python init_db.py
```

**What happens:**
```
Username: admin           ← You type this
Password: ********        ← You type this (hidden)
Confirm Password: ******** ← You confirm it
```

**Where are credentials stored?**
- ❌ **NOT stored in any file**
- ✅ Password is hashed and stored in PostgreSQL database
- ⚠️ **YOU must save these credentials yourself!**

**How to save them securely:**

| ✅ SAFE Methods | ❌ UNSAFE Methods |
|----------------|-------------------|
| Password manager (1Password, Bitwarden, LastPass) | Plain text file on desktop |
| Secure notes app (encrypted) | Email to yourself |
| Physical paper in locked safe | Sticky note on monitor |
| Company secrets vault | Shared Google Doc |
| Encrypted USB drive | Commit to git repository |

**Example - Using a Password Manager:**
```
Service: Opinian Platform - SuperAdmin
Username: admin
Password: MySecurePassword123!
URL: http://localhost:5000/login
Notes: Created on 2025-11-30, production server
```

---

### Method 2: Environment Variables (Automated Deployment)

**Step 1:** Copy `.env.example` to `.env`
```bash
cp .env.example .env
```

**Step 2:** Edit `.env` file:
```env
# Uncomment and set these values:
SUPERADMIN_USERNAME=admin
SUPERADMIN_EMAIL=admin@yourcompany.com
SUPERADMIN_PASSWORD=VerySecurePassword123!@#
SUPERADMIN_FIRST_NAME=John
SUPERADMIN_LAST_NAME=Doe
```

**Step 3:** Run init_db.py (it will use these automatically)
```bash
python init_db.py
```

**Security for .env file:**

| ✅ SAFE | ❌ UNSAFE |
|---------|-----------|
| `.env` is in `.gitignore` (already configured) | Committing `.env` to git |
| Only on your local machine / secure server | Uploading to public repositories |
| Proper file permissions (chmod 600 on Linux) | Sharing via email or chat |
| Different passwords for dev/staging/production | Using same password everywhere |
| Using secrets manager in production | Hardcoding in production |

---

## 🚀 Production Deployment - Best Practices

### ❌ DO NOT: Store credentials in .env on production server

### ✅ DO: Use Environment Variables or Secrets Manager

#### Option 1: Server Environment Variables (Good)
```bash
# On your production server, set environment variables
export SUPERADMIN_USERNAME=admin
export SUPERADMIN_EMAIL=admin@company.com
export SUPERADMIN_PASSWORD=ProductionSecurePass123!

# Then run init_db.py
python init_db.py
```

#### Option 2: Cloud Secrets Manager (Best)

**AWS Secrets Manager:**
```bash
# Store secret
aws secretsmanager create-secret \
  --name opinian/superadmin \
  --secret-string '{"username":"admin","password":"SecurePass123!"}'

# Retrieve in your deployment script
SECRET=$(aws secretsmanager get-secret-value --secret-id opinian/superadmin)
export SUPERADMIN_USERNAME=$(echo $SECRET | jq -r .username)
export SUPERADMIN_PASSWORD=$(echo $SECRET | jq -r .password)
```

**Azure Key Vault:**
```bash
# Store secret
az keyvault secret set \
  --vault-name opinian-vault \
  --name superadmin-username \
  --value "admin"

az keyvault secret set \
  --vault-name opinian-vault \
  --name superadmin-password \
  --value "SecurePass123!"
```

**Docker Secrets:**
```bash
# Create secrets
echo "admin" | docker secret create superadmin_username -
echo "SecurePass123!" | docker secret create superadmin_password -

# Use in docker-compose.yml
services:
  app:
    secrets:
      - superadmin_username
      - superadmin_password
    environment:
      SUPERADMIN_USERNAME_FILE: /run/secrets/superadmin_username
      SUPERADMIN_PASSWORD_FILE: /run/secrets/superadmin_password
```

---

## 🛡️ Security Checklist

### Before Deployment:

- [ ] `.env` is in `.gitignore`
- [ ] Never committed `.env` to git repository
- [ ] Used strong passwords (minimum 12 characters, mixed case, numbers, symbols)
- [ ] Different passwords for development, staging, and production
- [ ] SuperAdmin email is monitored and secure
- [ ] Tested login with SuperAdmin credentials
- [ ] Documented where production credentials are stored
- [ ] Shared credentials securely with team (via password manager)

### Password Requirements:

✅ **Good Password Examples:**
```
MyC0mpany$ecureP@ss2024!
Bl0gging-Pl@tform-Adm1n
0p1n1an!Sup3rUs3r#2024
```

❌ **Bad Password Examples:**
```
admin123          (too simple)
password          (common word)
12345678          (only numbers)
adminadmin        (repeated words)
```

### File Permissions (Linux/Mac):

```bash
# Make .env readable only by owner
chmod 600 .env

# Verify permissions
ls -la .env
# Should show: -rw------- (600)
```

---

## 🔍 How to Check Your Setup

### 1. Verify .env is NOT in git:
```bash
git status
# .env should NOT appear in the list

# Check .gitignore
cat .gitignore | grep .env
# Should show: .env
```

### 2. Verify SuperAdmin was created:
```bash
# Connect to database
psql -U postgres -d opinian

# Check SuperAdmin exists
SELECT u.id, u.username, u.email, r.name as role
FROM users u
JOIN roles r ON u.role_id = r.id
WHERE r.name = 'SuperAdmin';

# Should show your SuperAdmin user
```

### 3. Test login:
```bash
# Start application
python app.py

# Visit: http://localhost:5000/login
# Login with your SuperAdmin credentials
# Should successfully access dashboard
```

---

## 🚨 What If You Forget the Password?

If you forget your SuperAdmin password, you have two options:

### Option 1: Reset via Database (Direct SQL)

```bash
# 1. Connect to database
psql -U postgres -d opinian

# 2. Generate new password hash (use Python)
python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('NewPassword123!'))"
# Copy the hash output

# 3. Update database
UPDATE users
SET password_hash = '$2b$12$xyz...' -- paste hash here
WHERE username = 'admin';

# 4. Log in with new password: NewPassword123!
```

### Option 2: Reset via Python Script

Create a file `reset_superadmin_password.py`:
```python
import psycopg2
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
import os
import getpass

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)

username = input("SuperAdmin Username: ")
new_password = getpass.getpass("New Password: ")
password_hash = generate_password_hash(new_password)

cursor = conn.cursor()
cursor.execute(
    "UPDATE users SET password_hash = %s WHERE username = %s",
    (password_hash, username)
)
conn.commit()
print(f"Password reset for {username}")
cursor.close()
conn.close()
```

Run it:
```bash
python reset_superadmin_password.py
```

---

## 📖 Summary

### For Local Development:
1. Run `python init_db.py`
2. Type SuperAdmin credentials when prompted
3. **Save credentials in password manager**
4. Never commit credentials to git

### For Production:
1. Use environment variables or secrets manager
2. Set strong, unique passwords
3. Use HTTPS always
4. Rotate passwords regularly
5. Monitor access logs

### Remember:
- ✅ Passwords are **hashed** (encrypted) in database
- ✅ Original passwords are **NEVER stored**
- ✅ You **MUST save credentials** yourself
- ✅ Use **password manager** for safety
- ❌ Never commit `.env` to git
- ❌ Never share passwords via insecure channels

---

## 🔗 Additional Resources

- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [Best Password Managers 2024](https://www.nist.gov/password-guidelines)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/latest/security/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/auth-methods.html)

---

**Questions or Security Concerns?**
Please review this guide carefully before deploying to production.
