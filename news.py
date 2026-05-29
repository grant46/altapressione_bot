import requests
import xml.etree.ElementTree as ET

RSS_FEEDS = [
    ("🇮🇹", "https://www.ansa.it/sito/ansait_rss.xml"),
    ("🇮🇹", "https://www.repubblica.it/rss/homepage/rss2.0.xml"),
    ("🌍", "https://feeds.bbci.co.uk/news/rss.xml"),
    ("🌍", "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"),
]

def get_news(max_articles=3):
    articles = []
    for emoji, url in RSS_FEEDS:
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            root = ET.fromstring(r.content)
            items = root.findall(".//item")[:max_articles]
            for item in items:
                title = item.findtext("title", "").strip()
                link = item.findtext("link", "").strip()
                if title and link:
                    articles.append({
                        "title": title,
                        "link": link,
                        "source": url.split("/")[2],
                        "lang": emoji
                    })
        except Exception as e:
            print(f"Errore RSS {url}: {e}")
    return articles