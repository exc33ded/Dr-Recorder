import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            password TEXT NOT NULL,
            gender TEXT NULL,
            organization TEXT NULL,
            village TEXT NULL,
            town TEXT NULL,
            district TEXT NULL,
            state TEXT NULL,
            dob TEXT NULL,
            user_id TEXT NOT NULL UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
