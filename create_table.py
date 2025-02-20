import sqlite3

# Connect to the database (or create it if it doesn't exist)
conn = sqlite3.connect('database/main.db')
cursor = conn.cursor()

# SQL statement to create the 'user' table
create_table_sql = """
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

# Execute the SQL statement
cursor.execute(create_table_sql)

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Table 'user' created successfully!")