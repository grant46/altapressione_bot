import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_bulletin(name: str, weather: dict, news: list) -> str:
    """Uses Groq/LLaMA to generate intro + weather, then appends news with links."""

    weather_text = (
        f"Città: {weather['city']}\n"
        f"Temperatura: {weather['temp']}°C (percepita {weather['feels_like']}°C)\n"
        f"Condizioni: {weather['description']}\n"
        f"Umidità: {weather['humidity']}%\n"
        f"Vento: {weather['wind_speed']} km/h"
    ) if weather else "Meteo non disponibile al momento."

    prompt = f"""Sei un assistente simpatico e diretto che invia ogni mattina un bollettino su Telegram.

Nome utente: {name}
Meteo attuale:
{weather_text}

Genera SOLO queste due sezioni (niente notizie, le aggiungo io dopo):
1. Saluto personalizzato con il nome e il giorno della settimana
2. Sezione meteo con emoji, dati e 2-3 consigli pratici (cosa indossare, ombrello, ecc.)
3. Una frase motivazionale breve e originale per chiudere

Scrivi in italiano, usa emoji. Usa grassetto Telegram con *testo*. Sii conciso."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600,
        temperature=0.8
    )

    intro = response.choices[0].message.content.strip()

    # Costruiamo la sezione notizie con i link direttamente nel codice
    it_news = [a for a in news if a["lang"] == "🇮🇹"]
    intl_news = [a for a in news if a["lang"] == "🌍"]

    news_section = "\n\n*📰 Notizie di oggi*\n"

    if it_news:
        news_section += "\n🇮🇹 *Italia*\n"
        for a in it_news:
            link = a.get("link", "")
            if link:
                news_section += f"• [{a['title']}]({link})\n"
            else:
                news_section += f"• {a['title']}\n"

    if intl_news:
        news_section += "\n🌍 *Mondo*\n"
        for a in intl_news:
            link = a.get("link", "")
            if link:
                news_section += f"• [{a['title']}]({link})\n"
            else:
                news_section += f"• {a['title']}\n"

    return intro + news_section