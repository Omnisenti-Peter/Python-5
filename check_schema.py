import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME'),
    port=os.getenv('DB_PORT')
)

cur = conn.cursor()

# Get users table columns
print("USERS TABLE COLUMNS:")
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='users' ORDER BY ordinal_position")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

print("\n" + "="*50 + "\n")

# Get actual members of Friends group
print("FRIENDS GROUP MEMBERS:")
cur.execute("""
    SELECT u.id, u.username, u.email, r.name as role_name, u.group_id, u.is_active
    FROM users u
    LEFT JOIN roles r ON u.role_id = r.id
    WHERE u.group_id = 1
    ORDER BY u.username
""")

for row in cur.fetchall():
    print(f"  ID: {row[0]}, Username: {row[1]}, Email: {row[2]}, Role: {row[3]}, Group: {row[4]}, Active: {row[5]}")

print("\n" + "="*50 + "\n")

# Check admin user
print("ADMIN USER:")
cur.execute("""
    SELECT u.id, u.username, u.email, r.name as role_name, u.group_id, u.is_active
    FROM users u
    LEFT JOIN roles r ON u.role_id = r.id
    WHERE u.username = 'admin'
""")

row = cur.fetchone()
if row:
    print(f"  ID: {row[0]}, Username: {row[1]}, Email: {row[2]}, Role: {row[3]}, Group: {row[4]}, Active: {row[5]}")
else:
    print("  Admin user not found!")

cur.close()
conn.close()
