import sqlite3

DB_PATH = "users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            chat_id     INTEGER PRIMARY KEY,
            name        TEXT,
            city        TEXT,
            latitude    REAL,
            longitude   REAL,
            active      INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

def save_user(chat_id, name, city, lat, lon):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO users (chat_id, name, city, latitude, longitude, active)
        VALUES (?, ?, ?, ?, ?, 1)
        ON CONFLICT(chat_id) DO UPDATE SET
            name=excluded.name,
            city=excluded.city,
            latitude=excluded.latitude,
            longitude=excluded.longitude,
            active=1
    ''', (chat_id, name, city, lat, lon))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT chat_id, name, city, latitude, longitude FROM users WHERE active=1")
    rows = c.fetchall()
    conn.close()
    return rows

def deactivate_user(chat_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET active=0 WHERE chat_id=?", (chat_id,))
    conn.commit()
    conn.close()
