import os
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import init_db, save_user, get_all_users, deactivate_user, save_bulletin, save_weather_history
from news import get_news
from weather_api import get_weather, weather_emoji
from ai_bulletin import generate_bulletin

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Stati conversazione
ASK_NAME, ASK_LOCATION = range(2)

# ──────────────────────────────────────────────
# HANDLERS CONVERSAZIONE SETUP
# ──────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Ciao! Sono il tuo *Morning Bot* 🌅\n\n"
        "Ogni mattina alle *8:00* ti invierò:\n"
        "📰 Le notizie più importanti del giorno\n"
        "🌤️ Il meteo della tua città con consigli\n\n"
        "Per prima cosa... come ti chiami?",
        parse_mode="Markdown"
    )
    return ASK_NAME

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("Inserisci un nome valido 😊")
        return ASK_NAME

    context.user_data["name"] = name

    location_button = KeyboardButton("📍 Invia la mia posizione", request_location=True)
    keyboard = ReplyKeyboardMarkup([[location_button]], resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        f"Piacere {name}! 🎉\n\n"
        "Ora dimmi dove sei: invia la tua *posizione GPS* oppure scrivi il nome della tua *città*.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    return ASK_LOCATION

async def ask_location_gps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.location
    name = context.user_data.get("name", "Amico")
    chat_id = update.effective_chat.id

    # Geocoding inverso con OpenWeatherMap
    weather = get_weather("", lat=location.latitude, lon=location.longitude)
    city = weather["city"] if weather else "la tua città"

    save_user(chat_id, name, city, location.latitude, location.longitude)

    await update.message.reply_text(
        f"✅ Perfetto! Ti ho registrato a *{city}*.\n\n"
        f"Da domani alle *8:00* riceverai il tuo bollettino personalizzato!\n\n"
        f"Usa /anteprima per vedere subito come sarà 👀",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def ask_location_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city_input = update.message.text.strip()
    name = context.user_data.get("name", "Amico")
    chat_id = update.effective_chat.id

    weather = get_weather(city_input)
    if not weather:
        await update.message.reply_text(
            "❌ Non riesco a trovare questa città. Riprova con un nome diverso."
        )
        return ASK_LOCATION

    save_user(chat_id, name, weather["city"], None, None)

    await update.message.reply_text(
        f"✅ Perfetto! Ti ho registrato a *{weather['city']}*.\n\n"
        f"Da domani alle *8:00* riceverai il tuo bollettino personalizzato!\n\n"
        f"Usa /anteprima per vedere subito come sarà 👀",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Setup annullato. Usa /start per ricominciare.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# ──────────────────────────────────────────────
# ANTEPRIMA BOLLETTINO
# ──────────────────────────────────────────────

async def preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    users = get_all_users()
    user = next((u for u in users if u[0] == chat_id), None)

    if not user:
        await update.message.reply_text(
            "Non sei ancora registrato! Usa /start per iniziare."
        )
        return

    _, name, city, lat, lon = user
    await update.message.reply_text("⏳ Sto preparando il tuo bollettino...")

    try:
        weather = get_weather(city, lat, lon)
        news = get_news(max_articles=3)
        bulletin = generate_bulletin(name, weather, news)

        if weather:
            emoji = weather_emoji(weather["icon"])
            header = f"{emoji} *Meteo a {weather['city']}:* {weather['temp']}°C - {weather['description']}\n\n"
        else:
            header = ""

        await update.message.reply_text(
            bulletin,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Errore anteprima: {e}")
        await update.message.reply_text(
            "⚠️ Errore nella generazione del bollettino. Riprova tra poco."
        )

# ──────────────────────────────────────────────
# STOP
# ──────────────────────────────────────────────

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    deactivate_user(chat_id)
    await update.message.reply_text(
        "😢 Mi dispiace vederti andare!\n"
        "Ho disattivato il tuo bollettino.\n"
        "Usa /start per riattivarmi quando vuoi!"
    )

# ──────────────────────────────────────────────
# SCHEDULER – invia bollettino alle 8:00
# ──────────────────────────────────────────────

async def send_daily_bulletin(app: Application):
    users = get_all_users()
    logger.info(f"Invio bollettino a {len(users)} utenti...")

    news = get_news(max_articles=3)

    for chat_id, name, city, lat, lon in users:
        try:
            weather = get_weather(city, lat, lon)
            bulletin = generate_bulletin(name, weather, news)

            save_bulletin(chat_id, bulletin, weather, news)
            save_weather_history(city, weather)

            await app.bot.send_message(
                chat_id=chat_id,
                text=bulletin,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            logger.info(f"Bollettino inviato a {name} ({chat_id})")
        except Exception as e:
            logger.error(f"Errore invio a {chat_id}: {e}")

# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def main():
    init_db()

    token = os.getenv("TELEGRAM_TOKEN")
    app = Application.builder().token(token).build()

    # ConversationHandler per il setup
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_LOCATION: [
                MessageHandler(filters.LOCATION, ask_location_gps),
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_location_text),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("anteprima", preview))
    app.add_handler(CommandHandler("stop", stop))

    # Scheduler per le 8:00
    scheduler = AsyncIOScheduler(timezone="Europe/Rome")
    scheduler.add_job(
        send_daily_bulletin,
        trigger="cron",
        hour=8,
        minute=0,
        args=[app]
    )
    scheduler.start()

    logger.info("🤖 Bot avviato! In attesa di messaggi...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()