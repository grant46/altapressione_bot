# 🌅 Morning Bot – Il tuo bollettino mattutino su Telegram

Bot Telegram che ogni mattina alle 8:00 ti invia notizie + meteo con consigli personalizzati generati dall'AI.

---

## 🚀 Installazione

### 1. Installa le dipendenze

```bash
pip install -r requirements.txt
```

### 2. Configura le API key

Apri il file `.env` e inserisci le tue chiavi:

```env
TELEGRAM_TOKEN=il_tuo_token_telegram
NEWS_API_KEY=la_tua_key_newsapi
WEATHER_API_KEY=la_tua_key_openweathermap
GROQ_API_KEY=la_tua_key_groq
```

### 3. Avvia il bot

```bash
python bot.py
```

---

## 📋 Comandi disponibili

| Comando | Descrizione |
|---|---|
| `/start` | Registrati e configura il bot |
| `/anteprima` | Ricevi subito il bollettino di oggi |
| `/stop` | Disattiva il bollettino |
| `/cancel` | Annulla il setup |

---

## 🔑 Come ottenere le API key

- **Telegram Token** → [@BotFather](https://t.me/BotFather) su Telegram
- **NewsAPI** → [newsapi.org](https://newsapi.org) (free)
- **OpenWeatherMap** → [openweathermap.org/api](https://openweathermap.org/api) (free)
- **Groq** → [console.groq.com](https://console.groq.com) (free)

---

## 🏗️ Struttura progetto

```
morning-bot/
├── bot.py          # Bot principale + scheduler
├── database.py     # Gestione utenti (SQLite)
├── news.py         # Fetch notizie (NewsAPI)
├── weather.py      # Fetch meteo (OpenWeatherMap)
├── ai_bulletin.py  # Generazione AI (Groq/LLaMA)
├── requirements.txt
├── .env            # Le tue API key (NON condividere!)
└── README.md
```
