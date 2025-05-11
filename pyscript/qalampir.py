import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import xmltodict

sitemap_url = "https://qalampir.uz/sitemap.xml"
max_articles = 3000  # Maksimal maqolalar soni

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

        now = datetime.now()
        one_week_ago = now - timedelta(days=7)

        filtered = [
            item
            for index, item in enumerate(results)
            if datetime.fromisoformat(item["published_at"]) >= one_week_ago and index < max_articles
        ]

        enriched = []
        count = 0
        for item in filtered:
            try:
                page = requests.get(item["url"])
                page.raise_for_status()
                soup = BeautifulSoup(page.text, "html.parser")

                title = soup.select_one(".title h1.text").get_text(strip=True) if soup.select_one(".title h1.text") else ""
                article_text = soup.select_one(".content-main-titles").get_text(" ", strip=True) if soup.select_one(".content-main-titles") else ""

                category = [
                    span.get_text(strip=True)
                    for span in soup.select(".tags span")
                ]

                image_urls = [
                    img["src"]
                    for img in soup.select(".source_post img")
                    if img.get("src") and not img["src"].endswith("dp.svg")
                ]

                enriched.append(
                    {
                        "url": item["url"],
                        "published_at": item["published_at"],
                        "title": title,
                        "content": article_text.replace('"', "❞"),
                        "category": category,
                        "image_url": image_urls,
                        "type": "gazeta",
                    }
                )

                count += 1
                if count % 100 == 0:
                    print(f"[+] {count} ta maqola yuklandi...")
            except Exception as e:
                print(f"[-] Yuklab bo‘lmadi: {item['url']} - {e}")

        output_dir = os.path.join(os.path.dirname(__file__), "../output")
        os.makedirs(output_dir, exist_ok=True)
        print(f"[+] Papka yaratildi: {output_dir}")

        final_data = {
            "source": "qalampir.uz",
            "posts": enriched,
        }

        file_path = os.path.join(output_dir, "qalampir_articles.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Maqolalar saqlandi: {file_path}")
    except Exception as e:
        print(f"[-] Xatolik: {e}")

if __name__ == "__main__":
    extract_urls_and_dates()