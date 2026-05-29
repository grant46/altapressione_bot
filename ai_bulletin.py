import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_bulletin(name: str, weather: dict, news: list) -> str:
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

    news_titles = "\n".join([f"{i+1}. {a['title']}" for i, a in enumerate(news)])
    comment_prompt = f"""Hai questi titoli di notizie:
{news_titles}
Per ognuna scrivi UN'UNICA riga di commento brevissimo (max 15 parole), diretto e in italiano.
Rispondi SOLO con i commenti numerati, esempio:
1. Commento sulla notizia uno.
2. Commento sulla notizia due.
Niente altro, niente introduzioni."""

    comment_response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": comment_prompt}],
        max_tokens=400,
        temperature=0.7
    )

    raw_comments = comment_response.choices[0].message.content.strip().split("\n")
    comments = {}
    for line in raw_comments:
        line = line.strip()
        if line and line[0].isdigit() and "." in line:
            idx, _, text = line.partition(".")
            try:
                comments[int(idx.strip())] = text.strip()
            except ValueError:
                pass

    it_news = [a for a in news if a["lang"] == "🇮🇹"]
    intl_news = [a for a in news if a["lang"] == "🌍"]

    news_section = "\n\n*📰 Notizie di oggi*\n"

    if it_news:
        news_section += "\n🇮🇹 *Italia*\n"
        for a in it_news:
            link = a.get("link", "")
            comment = comments.get(news.index(a) + 1, "")
            if link:
                news_section += f"\n• [{a['title']}]({link})\n"
            else:
                news_section += f"\n• *{a['title']}*\n"
            if comment:
                news_section += f"  _{comment}_\n"

    if intl_news:
        news_section += "\n🌍 *Mondo*\n"
        for a in intl_news:
            link = a.get("link", "")
            comment = comments.get(news.index(a) + 1, "")
            if link:
                news_section += f"\n• [{a['title']}]({link})\n"
            else:
                news_section += f"\n• *{a['title']}*\n"
            if comment:
                news_section += f"  _{comment}_\n"

    return intro + news_section