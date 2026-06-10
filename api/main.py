from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import hashlib
import hmac
import os
import sys
import time
import requests
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_user, get_bulletins, get_stats, get_weather_history
from weather_api import get_weather
from news import get_news

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

app = FastAPI(title="Alta Pressione API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/stats")
async def stats():
    return get_stats()

@app.get("/api/user/{chat_id}")
async def user_info(chat_id: int):
    user = get_user(chat_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    return {"chat_id": user[0], "name": user[1], "city": user[2], "active": bool(user[5])}

@app.get("/api/bulletins/{chat_id}")
async def bulletins(chat_id: int, limit: int = 30):
    return get_bulletins(chat_id, limit)

@app.get("/api/weather/{city}")
async def weather(city: str):
    data = get_weather(city)
    if not data:
        raise HTTPException(status_code=404, detail="Città non trovata")
    return data

@app.get("/api/weather/forecast/{city}")
async def weather_forecast(city: str):
    try:
        r = requests.get("https://api.openweathermap.org/data/2.5/forecast", params={
            "q": city, "appid": WEATHER_API_KEY,
            "units": "metric", "lang": "it", "cnt": 40
        }, timeout=10)
        data = r.json()
        if r.status_code != 200:
            raise HTTPException(status_code=404, detail="Città non trovata")
        days = {}
        for item in data["list"]:
            date = item["dt_txt"].split(" ")[0]
            hour = item["dt_txt"].split(" ")[1]
            if date not in days or hour == "12:00:00":
                days[date] = {
                    "date": date,
                    "temp_max": item["main"]["temp_max"],
                    "temp_min": item["main"]["temp_min"],
                    "description": item["weather"][0]["description"].capitalize(),
                    "icon": item["weather"][0]["main"],
                    "humidity": item["main"]["humidity"],
                    "wind_speed": round(item["wind"]["speed"] * 3.6)
                }
        return list(days.values())[:7]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/airquality/{city}")
async def air_quality(city: str):
    try:
        geo_r = requests.get("http://api.openweathermap.org/geo/1.0/direct", params={
            "q": city, "limit": 1, "appid": WEATHER_API_KEY
        }, timeout=10)
        geo = geo_r.json()
        if not geo:
            raise HTTPException(status_code=404, detail="Città non trovata")
        lat, lon = geo[0]["lat"], geo[0]["lon"]
        aq_r = requests.get("http://api.openweathermap.org/data/2.5/air_pollution", params={
            "lat": lat, "lon": lon, "appid": WEATHER_API_KEY
        }, timeout=10)
        aq = aq_r.json()
        components = aq["list"][0]["components"]
        aqi = aq["list"][0]["main"]["aqi"]
        aqi_labels = {1: "Buona", 2: "Discreta", 3: "Moderata", 4: "Scarsa", 5: "Pessima"}
        aqi_colors = {1: "#6ee7b7", 2: "#a3e635", 3: "#fbbf24", 4: "#fb923c", 5: "#f87171"}
        return {
            "aqi": aqi, "aqi_label": aqi_labels.get(aqi, "N/D"),
            "aqi_color": aqi_colors.get(aqi, "#6ee7b7"),
            "pm2_5": round(components.get("pm2_5", 0), 1),
            "pm10": round(components.get("pm10", 0), 1),
            "no2": round(components.get("no2", 0), 1),
            "o3": round(components.get("o3", 0), 1),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/weather/history/{city}")
async def weather_history(city: str, days: int = 30):
    return get_weather_history(city, days)

@app.get("/api/news")
async def news():
    return get_news(max_articles=5)

# ── WIDGET PUBBLICO ──
@app.get("/meteo/{city}", response_class=HTMLResponse)
async def weather_widget(city: str):
    w = get_weather(city)
    if not w:
        return HTMLResponse("<h1>Città non trovata</h1>", status_code=404)

    emojis = {"Clear":"☀️","Clouds":"☁️","Rain":"🌧️","Drizzle":"🌦️","Thunderstorm":"⛈️","Snow":"❄️","Mist":"🌫️","Fog":"🌫️","Haze":"🌫️"}
    emoji = emojis.get(w["icon"], "🌡️")

    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <meta property="og:title" content="Meteo {w['city']} — Alta Pressione"/>
  <meta property="og:description" content="{emoji} {w['temp']}°C · {w['description']}"/>
  <title>Meteo {w['city']} — Alta Pressione</title>
  <link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet">
  <style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{font-family:'DM Sans',sans-serif;background:#0a1a0f;color:#ecfdf5;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}
    .widget{{background:rgba(12,28,16,0.95);border:1px solid rgba(110,231,183,0.2);border-radius:24px;padding:36px;max-width:420px;width:100%;text-align:center;backdrop-filter:blur(20px)}}
    .brand{{font-size:0.72rem;text-transform:uppercase;letter-spacing:0.15em;color:#6b9e82;margin-bottom:20px}}
    .city{{font-family:'Syne',sans-serif;font-size:1.8rem;font-weight:800;color:#6ee7b7;margin-bottom:4px}}
    .emoji{{font-size:4rem;margin:16px 0}}
    .temp{{font-family:'Syne',sans-serif;font-size:4rem;font-weight:800;letter-spacing:-0.04em;color:#ecfdf5}}
    .desc{{color:#6b9e82;font-size:1rem;margin-top:4px;margin-bottom:24px}}
    .grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:24px}}
    .item{{background:rgba(110,231,183,0.07);border-radius:12px;padding:12px;border:1px solid rgba(110,231,183,0.1)}}
    .item-label{{font-size:0.68rem;text-transform:uppercase;letter-spacing:0.08em;color:#6b9e82;margin-bottom:4px}}
    .item-value{{font-family:'Syne',sans-serif;font-weight:700;font-size:1.1rem}}
    .footer{{font-size:0.72rem;color:#6b9e82}}
    .footer a{{color:#6ee7b7;text-decoration:none}}
    .sun{{display:flex;justify-content:center;gap:24px;margin-bottom:20px;font-size:0.88rem;color:#6b9e82}}
  </style>
</head>
<body>
<div class="widget">
  <div class="brand">🌿 Alta Pressione</div>
  <div class="city">📍 {w['city']}</div>
  <div class="emoji">{emoji}</div>
  <div class="temp">{w['temp']}°C</div>
  <div class="desc">{w['description']} · Percepita {w['feels_like']}°C</div>
  <div class="sun">
    <span>🌅 Alba {w.get('sunrise','--')}</span>
    <span>🌇 Tramonto {w.get('sunset','--')}</span>
  </div>
  <div class="grid">
    <div class="item"><div class="item-label">💧 Umidità</div><div class="item-value">{w['humidity']}%</div></div>
    <div class="item"><div class="item-label">💨 Vento</div><div class="item-value">{w['wind_speed']} km/h</div></div>
    <div class="item"><div class="item-label">🔵 Pressione</div><div class="item-value">{w.get('pressure',1013)} hPa</div></div>
    <div class="item"><div class="item-label">👁️ Visibilità</div><div class="item-value">{w.get('visibility_km',10)} km</div></div>
  </div>
  <div class="footer">Aggiornato ora · <a href="http://localhost:8000">Alta Pressione Dashboard</a></div>
</div>
</body>
</html>""")

frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")