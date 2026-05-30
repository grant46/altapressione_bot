from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import hashlib
import hmac
import os
import time
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_user, get_bulletins, get_stats
from weather_api import get_weather
from news import get_news

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

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

@app.get("/api/news")
async def news():
    return get_news(max_articles=5)

frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")