import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import xmltodict

sitemap_url = "https://qalampir.uz/sitemap.xml"
max_articles = 10  # Maksimal maqolalar soni


def normalize_date(date_str):
    months = {
        "Январь": "01", "Февраль": "02", "Март": "03", "Апрель": "04",
        "Май": "05", "Июнь": "06", "Июль": "07", "Август": "08",
        "Сентябрь": "09", "Октябрь": "10", "Ноябрь": "11", "Декабрь": "12"
    }
    parts = date_str.split()
    day = parts[0]
    month = months[parts[1]]
    year = parts[2] if len(parts) > 2 else str(datetime.now().year)
    return f"{year}-{month}-{day.zfill(2)}"


def fetch_sitemap():
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()
        parsed = xmltodict.parse(response.content)
        urls = parsed["urlset"]["url"]
        return [
            {"url": entry["loc"]}
            for entry in urls
            if "loc" in entry
        ]
    except Exception as e:
        print(f"[-] Xatolik sitemapni yuklashda: {e}")
        return []


def fetch_article_content(url):
    try:
        page = requests.get(url)
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

        published_at_element = soup.select_one('p.right[itemprop="datePublished"]')
        published_at = published_at_element.get_text(strip=True).split('visibility')[0]
        published_at = normalize_date(published_at)

        return {
            "title": title,
            "content": article_text.replace('"', "❞"),
            "category": category,
            "image_url": image_urls,
            "published_at": published_at,
        }
    except Exception as e:
        print(f"[-] Xatolik maqolani yuklashda: {url} - {e}")
        return {}


def process_articles(urls):
    enriched = []
    for index, item in enumerate(urls[:max_articles]):
        article_content = fetch_article_content(item["url"])
        if article_content:
            enriched.append({
                **item,
                **article_content,
                "type": "gazeta",
            })
        if (index + 1) % 100 == 0:
            print(f"[+] {index + 1} ta maqola yuklandi...")
    return enriched


def save_to_file(data, filename):
    output_dir = os.path.join(os.path.dirname(__file__), "../output")
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Maqolalar saqlandi: {file_path}")


def extract_urls_and_dates():
    urls = fetch_sitemap()
    enriched_articles = process_articles(urls)
    final_data = {
        "source": "qalampir.uz",
        "posts": enriched_articles,
    }
    save_to_file(final_data, "qalampir_articles.json")


if __name__ == "__main__":
    extract_urls_and_dates()