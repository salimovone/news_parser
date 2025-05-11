const axios = require("axios");
const xml2js = require("xml2js");
const cheerio = require("cheerio");
const fs = require("fs");
const path = require("path");
const { DateTime } = require("luxon");

const sitemapUrl = "https://www.gazeta.uz/sitemap/google-news-ru.xml";
let results = [];

async function scrapePage(url, published_at) {
  try {
    const response = await axios.get(url);
    const $ = cheerio.load(response.data);

    const title = $("title").text().trim();

    const content = $("p")
      .map((i, el) => $(el).text().trim())
      .get()
      .join("\n\n");

    const images = $("img")
      .map((i, el) => $(el).attr("src"))
      .get()
      .filter((src) => src && src.startsWith("http"));

    const category = [
      ...$("nav.breadcrumbs li a")
        .map((i, el) => $(el).text().trim())
        .get()
        .filter((text) => text && text !== "Главная"),
      ...$('span[itemprop="about"]')
        .map((i, el) => $(el).text().trim())
        .get(),
    ].filter(Boolean);

    const result = {
      url,
      title,
      content,
      image_url: images,
      published_at,
      category,
      type: "gazeta",
    };

    results.push({ ...result });
  } catch (error) {
    console.error("❌ Xatolik:", error.message);
  }
}

async function parseGazetaNewsXml() {
  try {
    const res = await axios.get(sitemapUrl);
    const parsed = await xml2js.parseStringPromise(res.data, {
      explicitArray: false,
      mergeAttrs: true,
    });

    const urls = parsed.urlset.url;
    const now = new Date();
    const oneWeekAgo = new Date(now);
    oneWeekAgo.setDate(now.getDate() - 7);

    for (const item of urls) {
      const pubDate = new Date(item["news:news"]["news:publication_date"]);
      if (pubDate < oneWeekAgo) continue;

      const url = item.loc;
      const published_at = DateTime.fromJSDate(pubDate).toFormat("yyyy-MM-dd HH:mm");
      await scrapePage(url, published_at);
    }

    const outputDir = path.join(__dirname, "../output");
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
      console.log(`[+] Papka yaratildi: ${outputDir}`);
    }

    const finalData = {
      source: "Gazeta.uz",
      posts: results,
    };

    const filePath = path.join(outputDir, "gazeta_full.json");

    fs.writeFileSync(filePath, JSON.stringify(finalData, null, 2), "utf8");

    console.log(`✅ Saqlandi: ${filePath}`);
  } catch (err) {
    console.error("[-] Xatolik:", err.message);
  }
}

parseGazetaNewsXml();
