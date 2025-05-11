import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import xmltodict

sitemap_url = "https://novayagazeta.eu/feed/sitemap"

def extract_urls_and_dates():
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()
        parsed = xmltodict.parse(response.content)

        urls = parsed["urlset"]["url"]
        results = [
            {
                "url": entry["loc"],
                "published_at": entry.get("lastmod", ""),
            }
            for entry in urls
            if "loc" in entry
        ]

        now = datetime.now(timezone.utc)  # Offset-aware datetime
        one_week_ago = now - timedelta(days=7)

        filtered = []
        for item in results:
            try:
                pub_date = datetime.fromisoformat(item["published_at"])
                if pub_date.tzinfo is None:  # Agar offset-naive bo'lsa
                    pub_date = pub_date.replace(tzinfo=timezone.utc)
                if pub_date >= one_week_ago:
                    filtered.append(item)
            except ValueError:
                print(f"[-] Noto'g'ri sana formati: {item['published_at']}")

        enriched = []
        for item in filtered:
            try:
                page = requests.get(item["url"])
                page.raise_for_status()
                soup = BeautifulSoup(page.text, "html.parser")

                title = soup.title.string.strip() if soup.title else ""
                article_text = (
                    soup.find("article").get_text(" ", strip=True)
                    if soup.find("article")
                    else ""
                )

                image_urls = [
                    img["src"]
                    for img in soup.find_all("img", src=True)
                    if not img["src"].endswith("dp.svg")
                ]

                enriched.append(
                    {
                        "url": item["url"],
                        "published_at": item["published_at"],
                        "title": title,
                        "content": article_text.replace('"', "❞"),
                        "category": "",
                        "image_url": image_urls,
                        "type": "gazeta",
                    }
                )

                print(f"[+] Yuklandi: {item['url']}")
            except Exception as e:
                print(f"[-] Yuklab bo‘lmadi: {item['url']} - {e}")

        output_dir = os.path.join(os.path.dirname(__file__), "../output")
        os.makedirs(output_dir, exist_ok=True)
        print(f"[+] Papka yaratildi: {output_dir}")

        final_data = {
            "source": "novayagazeta.eu",
            "posts": enriched,
        }

        file_path = os.path.join(output_dir, "novaya_articles.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Maqolalar saqlandi: {file_path}")
    except Exception as e:
        print(f"[-] Xatolik: {e}")

if __name__ == "__main__":
    extract_urls_and_dates()