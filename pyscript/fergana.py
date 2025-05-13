import os
import json
import requests
from bs4 import BeautifulSoup



def fetch_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status() 
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None
    
def parse_news_list(page_content, base_url):
    try:
        articles = []
        soup = BeautifulSoup(page_content, "html.parser")
        for item in soup.select("li.news_list__item"):
            link = item.select_one("a")["href"]
            published_at = item.select_one("div.news_list__time").get_text(strip=True)

            articles.append({
                "url": base_url+link,
                "published_at": published_at
            })
        return articles
    except Exception as e:
        print(f"Error parsing news list: {e}")
        return []

def parse_news_page(page_link):
    page_content = fetch_data(page_link)
    try:
        soup = BeautifulSoup(page_content, "html.parser")
        title = soup.select_one("div.article-top h1").get_text(strip=True)
        content = "\n\n".join([p.get_text(strip=True) for p in soup.select("div.article-content p")])
        images = [img["src"] for img in soup.select("div.article-content img") if img["src"].startswith("http")]

        return {
            "title": title,
            "content": content,
            "image_url": images,
            "category": [],
            "type": "news"
        }
    except Exception as e:
        print(f"Error parsing news page: {e}")
        return {}
    
def get_objects(base_url):
    url = base_url + "/news/?n=1" 
    page_content = fetch_data(url)
    news_list = parse_news_list(page_content, base_url)

    all_news = []
    
    if page_content:
        for news in news_list:
            news_page = parse_news_page(news["url"])
            res = news_page | news
            if news_page["title"]:
                all_news.append(res)
        return all_news
    else:
        print("Failed to fetch the page content.")


# Example usage
if __name__ == "__main__":
    base_url = "https://en.fergana.news"
    output_dir = os.path.join(os.path.dirname(__file__), "../output")
    os.makedirs(output_dir, exist_ok=True)


    try:
        parsed_articles = get_objects(base_url)
        final_data = {
        "source": "Gazeta.uz",
        "posts": parsed_articles,
    }
        file_path = os.path.join(output_dir, "fergana_news.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Saqlandi: {file_path}")
    except Exception as e:
        print(f"[-] Xatolik: {e}")