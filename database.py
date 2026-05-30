import sqlite3
import json
from datetime import datetime

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
            active      INTEGER DEFAULT 1,
            created_at  TEXT DEFAULT (datetime('now'))
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS bulletins (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id     INTEGER,
            content     TEXT,
            weather     TEXT,
            news        TEXT,
            sent_at     TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (chat_id) REFERENCES users(chat_id)
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

def get_user(chat_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE chat_id=?", (chat_id,))
    row = c.fetchone()
    conn.close()
    return row

def deactivate_user(chat_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET active=0 WHERE chat_id=?", (chat_id,))
    conn.commit()
    conn.close()

def save_bulletin(chat_id, content, weather, news):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO bulletins (chat_id, content, weather, news)
        VALUES (?, ?, ?, ?)
    ''', (
        chat_id,
        content,
        json.dumps(weather) if weather else None,
        json.dumps(news) if news else None
    ))
    conn.commit()
    conn.close()

def get_bulletins(chat_id, limit=30):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT id, content, weather, news, sent_at
        FROM bulletins
        WHERE chat_id=?
        ORDER BY sent_at DESC
        LIMIT ?
    ''', (chat_id, limit))
    rows = c.fetchall()
    conn.close()
    result = []
    for row in rows:
        result.append({
            "id": row[0],
            "content": row[1],
            "weather": json.loads(row[2]) if row[2] else None,
            "news": json.loads(row[3]) if row[3] else None,
            "sent_at": row[4]
        })
    return result

def get_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE active=1")
    active_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM bulletins")
    total_bulletins = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM bulletins WHERE date(sent_at) = date('now')")
    today_bulletins = c.fetchone()[0]
    conn.close()
    return {
        "active_users": active_users,
        "total_bulletins": total_bulletins,
        "today_bulletins": today_bulletins
    }