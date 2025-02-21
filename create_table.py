import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

# Connect to the database (this will create a new file if it doesn't exist)
conn = sqlite3.connect('database/main.db')
cursor = conn.cursor()

# SQL statement to create the 'user' table with password_hash, reset_token, and token_expiration columns
create_table_sql = """
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    reset_token TEXT,            -- New column for password reset token
    token_expiration DATETIME,   -- New column for token expiration
    role TEXT DEFAULT 'user',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

# Execute the SQL statement to create the table
cursor.execute(create_table_sql)

# Add an admin user (replace these with your own username, email, and password)
admin_username = 'admin'
admin_email = 'admin@example.com'
admin_password = 'admin_password'  # Plain password (this will be hashed)

# Hash the password
hashed_password = generate_password_hash(admin_password)

# Insert the admin user into the 'user' table
insert_admin_sql = """
INSERT INTO user (username, email, password_hash, role)
VALUES (?, ?, ?, ?);
"""

# Execute the insert statement with the hashed password
cursor.execute(insert_admin_sql, (admin_username, admin_email, hashed_password, 'admin'))

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Database and admin created successfully!")
