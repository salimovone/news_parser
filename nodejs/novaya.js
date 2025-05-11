const axios = require("axios");
const xml2js = require("xml2js");
const cheerio = require("cheerio");
const fs = require("fs");
const path = require("path");

const sitemapUrl = "https://novayagazeta.eu/feed/sitemap";

async function extractUrlsAndDates() {
  try {
    const res = await axios.get(sitemapUrl);
    const parsed = await xml2js.parseStringPromise(res.data);

    const results = parsed.urlset.url
      .filter((entry) => entry.loc[0])
      .map((entry) => ({
        url: entry.loc[0],
        published_at: entry.lastmod ? entry.lastmod[0] : "",
      }));

    const now = new Date();
    const oneWeekAgo = new Date(now);
    oneWeekAgo.setDate(now.getDate() - 7);

    const filtered = results.filter((item) => {
      const pubDate = new Date(item.published_at);
      return pubDate >= oneWeekAgo;
    });

    const enriched = [];
    for (const item of filtered) {
      try {
        const page = await axios.get(item.url);
        const $ = cheerio.load(page.data);

        const title = $("title").text().trim();
        const articleText = $("article").text().replace(/\s+/g, " ").trim();

        const imageUrls = $("article img")
          .map((i, el) => {
            const src = $(el).attr("src");

            if (!src || src.endsWith("dp.svg")) return null;
            return new URL(src, item.url).href;
          })
          .get()
          .filter(Boolean);

        enriched.push({
          url: item.url,
          published_at: item.published_at,
          title,
          content: `${articleText.replaceAll('"', "❞")}`,
          category: "",
          image_url: imageUrls,
          type: "gazeta",
        });

        console.log(`[+] Yuklandi: ${item.url}`);
      } catch (e) {
        console.warn(`[-] Yuklab bo‘lmadi: ${item.url}`);
      }
    }

    const outputDir = path.join(__dirname, "../output");
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
      console.log(`[+] Papka yaratildi: ${outputDir}`);
    }

    const finalData = {
      source: "novayagazeta.eu",
      posts: enriched,
    };

    const filePath = path.join(outputDir, "novaya_articles.json");

    fs.writeFileSync(filePath, JSON.stringify(finalData, null, 2), "utf8");

    console.log(`✅ Maqolalar saqlandi: ${filePath}`);
  } catch (err) {
    console.error("[-] Xatolik:", err.message);
  }
}

extractUrlsAndDates();