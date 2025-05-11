import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import xmltodict
from pytz import timezone

sitemap_url = "https://www.gazeta.uz/sitemap/google-news-ru.xml"
results = []


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://example.com",
    # Agar kerak bo‘lsa Cookie qo‘shing
    # "Cookie": "sessionid=abc123; othercookie=value",
}

def scrape_page(url, published_at):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.title.string.strip() if soup.title else ""

        content = "\n\n".join(
            [p.get_text(strip=True) for p in soup.find_all("p")]
        )

        images = [
            img["src"]
            for img in soup.find_all("img", src=True)
            if img["src"].startswith("http")
        ]

        category = [
            *[
                a.get_text(strip=True)
                for a in soup.select("nav.breadcrumbs li a")
                if a.get_text(strip=True) and a.get_text(strip=True) != "Главная"
            ],
            *[
                span.get_text(strip=True)
                for span in soup.select('span[itemprop="about"]')
            ],
        ]

        result = {
            "url": url,
            "title": title,
            "content": content,
            "image_url": images,
            "published_at": published_at,
            "category": category,
            "type": "gazeta",
        }

        results.append(result)
    except Exception as e:
        print(f"❌ Xatolik: {e}")

def parse_gazeta_news_xml():
    try:
        response = requests.get(sitemap_url, headers=headers)
        response.raise_for_status()
        parsed = xmltodict.parse(response.content)

        urls = parsed["urlset"]["url"]
        now = datetime.now()
        one_week_ago = now - timedelta(days=7)

        if isinstance(urls, dict):  # Agar faqat bitta URL bo'lsa
            urls = [urls]

        for item in urls:
            pub_date = datetime.fromisoformat(item["news:news"]["news:publication_date"])
            if pub_date < one_week_ago:
                continue

            url = item["loc"]
            published_at = pub_date.astimezone(timezone("UTC")).strftime("%Y-%m-%d %H:%M")
            scrape_page(url, published_at)

        output_dir = os.path.join(os.path.dirname(__file__), "../output")
        os.makedirs(output_dir, exist_ok=True)
        print(f"[+] Papka yaratildi: {output_dir}")

        final_data = {
            "source": "Gazeta.uz",
            "posts": results,
        }

        file_path = os.path.join(output_dir, "gazeta_full.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Saqlandi: {file_path}")
    except Exception as e:
        print(f"[-] Xatolik: {e}")

if __name__ == "__main__":
    parse_gazeta_news_xml()

