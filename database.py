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

    c.execute('''
        CREATE TABLE IF NOT EXISTS weather_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            city        TEXT,
            temp        REAL,
            temp_max    REAL,
            temp_min    REAL,
            humidity    INTEGER,
            wind_speed  REAL,
            description TEXT,
            icon        TEXT,
            uv_index    REAL,
            recorded_at TEXT DEFAULT (datetime('now'))
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
            name=excluded.name, city=excluded.city,
            latitude=excluded.latitude, longitude=excluded.longitude, active=1
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
    ''', (chat_id, content,
          json.dumps(weather) if weather else None,
          json.dumps(news) if news else None))
    conn.commit()
    conn.close()

def get_bulletins(chat_id, limit=30):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT id, content, weather, news, sent_at FROM bulletins
        WHERE chat_id=? ORDER BY sent_at DESC LIMIT ?
    ''', (chat_id, limit))
    rows = c.fetchall()
    conn.close()
    return [{
        "id": r[0], "content": r[1],
        "weather": json.loads(r[2]) if r[2] else None,
        "news": json.loads(r[3]) if r[3] else None,
        "sent_at": r[4]
    } for r in rows]

def save_weather_history(city, weather):
    if not weather:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO weather_history (city, temp, temp_max, temp_min, humidity, wind_speed, description, icon, uv_index)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        city, weather.get("temp"), weather.get("temp_max"), weather.get("temp_min"),
        weather.get("humidity"), weather.get("wind_speed"), weather.get("description"),
        weather.get("icon"), weather.get("uv_index")
    ))
    conn.commit()
    conn.close()

def get_weather_history(city, days=30):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT date(recorded_at) as day,
               round(avg(temp), 1) as avg_temp,
               round(max(temp_max), 1) as max_temp,
               round(min(temp_min), 1) as min_temp,
               round(avg(humidity), 0) as avg_humidity
        FROM weather_history
        WHERE city=? AND recorded_at >= datetime('now', ?)
        GROUP BY day ORDER BY day ASC
    ''', (city, f'-{days} days'))
    rows = c.fetchall()
    conn.close()
    return [{"date": r[0], "avg_temp": r[1], "max_temp": r[2], "min_temp": r[3], "avg_humidity": r[4]} for r in rows]

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
    return {"active_users": active_users, "total_bulletins": total_bulletins, "today_bulletins": today_bulletins}