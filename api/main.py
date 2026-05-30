from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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

from database import get_user, get_bulletins, get_stats
from weather_api import get_weather
from news import get_news

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

app = FastAPI(title="Morning Bot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def verify_telegram_auth(data: dict) -> bool:
    check_hash = data.pop("hash", None)
    if not check_hash:
        return False
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret_key = hashlib.sha256(TELEGRAM_TOKEN.encode()).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    auth_date = int(data.get("auth_date", 0))
    if time.time() - auth_date > 86400:
        return False
    return hmac.compare_digest(computed_hash, check_hash)

@app.post("/api/auth/telegram")
async def telegram_auth(request: Request):
    data = await request.json()
    if not verify_telegram_auth(dict(data)):
        raise HTTPException(status_code=401, detail="Autenticazione non valida")
    chat_id = data.get("id")
    user = get_user(chat_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utente non registrato sul bot")
    return {"ok": True, "chat_id": chat_id, "name": user[1], "city": user[2]}

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

        # Raggruppa per giorno (prendi lettura a mezzogiorno)
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
        # Prima ottieni coordinate dalla città
        geo_r = requests.get("http://api.openweathermap.org/geo/1.0/direct", params={
            "q": city, "limit": 1, "appid": WEATHER_API_KEY
        }, timeout=10)
        geo = geo_r.json()
        if not geo:
            raise HTTPException(status_code=404, detail="Città non trovata")

        lat, lon = geo[0]["lat"], geo[0]["lon"]

        # Poi ottieni qualità aria
        aq_r = requests.get("http://api.openweathermap.org/data/2.5/air_pollution", params={
            "lat": lat, "lon": lon, "appid": WEATHER_API_KEY
        }, timeout=10)
        aq = aq_r.json()
        components = aq["list"][0]["components"]
        aqi = aq["list"][0]["main"]["aqi"]

        aqi_labels = {1: "Buona", 2: "Discreta", 3: "Moderata", 4: "Scarsa", 5: "Pessima"}
        aqi_colors = {1: "#6ee7b7", 2: "#a3e635", 3: "#fbbf24", 4: "#fb923c", 5: "#f87171"}

        return {
            "aqi": aqi,
            "aqi_label": aqi_labels.get(aqi, "N/D"),
            "aqi_color": aqi_colors.get(aqi, "#6ee7b7"),
            "pm2_5": round(components.get("pm2_5", 0), 1),
            "pm10": round(components.get("pm10", 0), 1),
            "no2": round(components.get("no2", 0), 1),
            "o3": round(components.get("o3", 0), 1),
            "co": round(components.get("co", 0), 1),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/news")
async def news():
    return get_news(max_articles=5)

frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")