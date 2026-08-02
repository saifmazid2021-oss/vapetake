# vapospy-clone

A reusable crawler + price-comparison stack modeled on vapospy.com's data
(vaporizers/accessories, multi-retailer price comparison with affiliate
links). Not a copy of Vapospy's design — see `output/layout_notes.md` for
structural notes to design your own look.

vapospy.com's `robots.txt` allows crawling everything and links its own
sitemap, so this project crawls it directly rather than screen-scraping
blind. It's WordPress-based (not Shopify) with fully static, server-rendered
HTML — no Playwright/JS rendering is needed anywhere in this stack.

## Structure

```
crawler/    Scrapy project — one spider (`vapospy`), rerunnable daily
database/   Postgres schema + docker-compose
api/        FastAPI read API over Postgres
frontend/   Next.js app (product listing + detail/price-compare page)
output/     Crawl outputs: sitemap.csv, all_urls.txt, products.csv,
            categories.csv, brands.csv, offers.csv, crawl.log, layout_notes.md
```

## 1. Crawler

```bash
cd crawler
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# CSV-only dry run (no DB needed), capped for a quick smoke test:
VAPOSPY_PG_ENABLED=0 scrapy crawl vapospy -a max_pages=50

# Full crawl, writing to Postgres too (bring up the DB first, see step 2):
scrapy crawl vapospy
```

What it does every run:
- Reads `sitemap.xml` → expands `products.xml` + `collections.xml` (default
  locale only; the site also publishes 15+ locale variants like
  `products-de_de.xml` if you want those too — see `DEFAULT_LOCALE_SITEMAP_RE`
  in `spiders/vapospy_spider.py`).
- Also link-crawls from the homepage to catch any page not in the sitemaps.
- For every product page: name, brand, description, GTIN, image list,
  category breadcrumb, and **every retailer offer** shown (price, old price,
  coupon, affiliate link, position, last-updated timestamp, seller
  about-text/country).
- For every collection page: name + the product URLs listed on it.
- Streams everything to `output/*.csv` as it goes (crash-safe) and, if
  Postgres is reachable, upserts products/brands/categories/stores/offers
  and appends a `price_history` row per offer — so rerunning this daily
  builds a real price history over time.

Politeness: `robots.txt` obeyed, autothrottle on, identifies itself via a
real `User-Agent` with a contact email (see `settings.py`).

## 2. Database

Requires Docker (not available in the environment this was built in — bring
it up yourself and re-run the crawler against it):

```bash
cd database
docker compose up -d
```

Schema (`schema.sql`) is applied automatically on first start. Tables:
`brands`, `categories`, `products`, `product_categories`, `images`,
`stores`, `offers` (latest known price per product×store), `price_history`
(append-only, one row per crawl).

## 3. API

```bash
cd api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Endpoints: `GET /products`, `GET /products/{slug}`,
`GET /products/{slug}/price-history`, `GET /categories`, `GET /brands`.

## 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000`. Set `NEXT_PUBLIC_API_BASE` if the API isn't
on `localhost:8000`.

## 5. Deploying to vapetake.com

Once the local stack works end-to-end:

1. **Postgres + API (Railway is the path of least resistance):**
   - New Railway project → "Deploy from GitHub repo" → add a Postgres
     plugin (gives you a `DATABASE_URL` automatically) and a service
     pointed at `api/` (it'll pick up `api/Dockerfile`).
   - Railway injects `DATABASE_URL` into the API service automatically —
     `api/app/db.py` already prefers it over the discrete `VAPOSPY_PG_*`
     vars, no code changes needed.
   - Note the API's public URL (e.g. `https://vapetake-api.up.railway.app`).

2. **Frontend (Vercel):**
   - Import the repo, set the project root to `frontend/`.
   - Add env var `NEXT_PUBLIC_API_BASE` = your Railway API URL from step 1.
   - Deploy.

3. **Crawler (keeps prices fresh):**
   - `.github/workflows/crawl.yml` runs `scrapy crawl vapospy` daily via
     GitHub Actions — add your Railway Postgres's `DATABASE_URL` as a repo
     secret (Settings → Secrets and variables → Actions) and it writes
     straight into the same production DB. Trigger it once manually first
     (Actions tab → "Recrawl vapospy.com" → Run workflow) instead of
     waiting a day.

4. **Domain:**
   - In Vercel: Project → Settings → Domains → add `vapetake.com`, follow
     its DNS instructions (usually an `A` record to Vercel's IP or a
     `CNAME`, set at your registrar).
   - The API doesn't need the public domain — the frontend calls it
     server-side via `NEXT_PUBLIC_API_BASE`.

## Verified so far

- Crawler: run live against vapospy.com, confirmed correct extraction of
  products/offers/categories into CSV.
- API: imports cleanly, all routes registered (DB queries not yet exercised
  against a live Postgres — no Docker/Postgres available in this sandbox).
- Frontend: `npm run build` succeeds, both routes compile.

Still to do on your end: bring up Postgres, point the crawler + API at it,
and confirm the DB write path end-to-end.
