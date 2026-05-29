import requests
import os
from dotenv import load_dotenv
load_dotenv() 
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

def get_weather(city: str, lat: float = None, lon: float = None) -> dict:
    """Fetches weather data by city name or coordinates."""
    def get_weather(city: str, lat: float = None, lon: float = None) -> dict:
        print(f">>> Chiamata meteo - city={city}, lat={lat}, lon={lon}, key={WEATHER_API_KEY}")
    try:
        params = {
            "appid": WEATHER_API_KEY,
            "units": "metric",
            "lang": "it"
        }
        if lat and lon:
            params["lat"] = lat
            params["lon"] = lon
        else:
            params["q"] = city

        r = requests.get(BASE_URL, params=params, timeout=10)
        data = r.json()

        if r.status_code != 200:
            return None

        return {
            "city": data.get("name", city),
            "temp": round(data["main"]["temp"]),
            "feels_like": round(data["main"]["feels_like"]),
            "description": data["weather"][0]["description"].capitalize(),
            "humidity": data["main"]["humidity"],
            "wind_speed": round(data["wind"]["speed"] * 3.6),  # m/s -> km/h
            "icon": data["weather"][0]["main"]
        }
    except Exception as e:
        print(f"Errore meteo: {e}")
        import traceback
        traceback.print_exc()
        return None

def weather_emoji(icon: str) -> str:
    mapping = {
        "Clear": "☀️",
        "Clouds": "☁️",
        "Rain": "🌧️",
        "Drizzle": "🌦️",
        "Thunderstorm": "⛈️",
        "Snow": "❄️",
        "Mist": "🌫️",
        "Fog": "🌫️",
        "Haze": "🌫️",
        "Wind": "💨",
    }
    return mapping.get(icon, "🌡️")
