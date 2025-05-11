const axios = require("axios");
const xml2js = require("xml2js");
const cheerio = require("cheerio");
const fs = require("fs");
const path = require("path");

const sitemapUrl = "https://qalampir.uz/sitemap.xml";
const maxArticles = 3000; // Maksimal maqolalar soni

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

    const filtered = results.filter((item, index) => {
      const pubDate = new Date(item.published_at);
      return pubDate >= oneWeekAgo && index < maxArticles; 
    });

    // Har bir URL uchun maqola kontentini olish
    const enriched = [];
    let count = 0;
    for (const item of filtered) {
      try {
        const page = await axios.get(item.url);
        const $ = cheerio.load(page.data);

        const title = $(".title h1.text").text().trim();
        const articleText = $(".content-main-titles").text().replace(/\s+/g, " ").trim();

        const category = $(".tags span")
          .map((i, el) => $(el).text().trim())
          .get();

        const imageUrls = $(".source_post img")
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
          category,
          image_url: imageUrls,
          type: "gazeta",
        });

        if (++count % 100 === 0) {
          console.log(`[+] ${count} ta maqola yuklandi...`);
        }
      } catch (e) {
        console.warn(`[-] Yuklab bo‘lmadi: ${item.url}`);
      }
    }

    // output papkasi mavjudligini tekshirish va yaratish
    const outputDir = path.join(__dirname, "../output");
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
      console.log(`[+] Papka yaratildi: ${outputDir}`);
    }

    // JSON faylga yozish
    const finalData = {
      source: "qalampir.uz",
      posts: enriched,
    };

    const filePath = path.join(outputDir, "qalampir_articles.json");

    fs.writeFileSync(filePath, JSON.stringify(finalData, null, 2), "utf8");

    console.log(`✅ Maqolalar saqlandi: ${filePath}`);
  } catch (err) {
    console.error("[-] Xatolik:", err.message);
  }
}

extractUrlsAndDates();
