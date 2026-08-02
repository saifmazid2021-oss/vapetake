import csv
import os

from itemadapter import ItemAdapter

from vapospy_crawler.items import CollectionItem, OfferItem, PageItem, ProductItem

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "output")


class CsvExportPipeline:
    """
    Streams every item straight to the Phase 1 / Phase 2 output files as the
    crawl runs, so a crash partway through still leaves usable CSVs.
    """

    def open_spider(self, spider):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self._all_urls_fh = open(os.path.join(OUTPUT_DIR, "all_urls.txt"), "w", encoding="utf-8")

        self._sitemap_fh = open(os.path.join(OUTPUT_DIR, "sitemap.csv"), "w", newline="", encoding="utf-8")
        self._sitemap_writer = csv.writer(self._sitemap_fh)
        self._sitemap_writer.writerow(["url", "status", "title", "canonical", "page_type"])

        self._products_fh = open(os.path.join(OUTPUT_DIR, "products.csv"), "w", newline="", encoding="utf-8")
        self._products_writer = csv.writer(self._products_fh)
        self._products_writer.writerow([
            "uid", "source_id", "name", "brand", "url", "low_price", "high_price",
            "offer_count", "gtin", "categories", "image_count", "description",
        ])

        self._categories_fh = open(os.path.join(OUTPUT_DIR, "categories.csv"), "w", newline="", encoding="utf-8")
        self._categories_writer = csv.writer(self._categories_fh)
        self._categories_writer.writerow(["uid", "name", "url", "product_count"])

        self._offers_fh = open(os.path.join(OUTPUT_DIR, "offers.csv"), "w", newline="", encoding="utf-8")
        self._offers_writer = csv.writer(self._offers_fh)
        self._offers_writer.writerow([
            "product_uid", "store_uid", "store_name", "price", "old_price",
            "coupon_code", "affiliate_url", "position", "source_updated_at", "store_country",
        ])

        self._seen_brands = set()

    def close_spider(self, spider):
        brands_path = os.path.join(OUTPUT_DIR, "brands.csv")
        with open(brands_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["name"])
            for brand in sorted(self._seen_brands):
                writer.writerow([brand])

        for fh in (self._all_urls_fh, self._sitemap_fh, self._products_fh, self._categories_fh, self._offers_fh):
            fh.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        if isinstance(item, PageItem):
            self._all_urls_fh.write(adapter["url"] + "\n")
            self._sitemap_writer.writerow([
                adapter["url"], adapter["status"], adapter.get("title", ""),
                adapter.get("canonical", ""), adapter["page_type"],
            ])

        elif isinstance(item, ProductItem):
            if adapter.get("brand"):
                self._seen_brands.add(adapter["brand"])
            self._products_writer.writerow([
                adapter["uid"], adapter.get("source_id"), adapter.get("name"), adapter.get("brand"),
                adapter["url"], adapter.get("low_price"), adapter.get("high_price"),
                adapter.get("offer_count"), adapter.get("gtin"),
                "|".join(c["name"] for c in adapter.get("categories") or []),
                len(adapter.get("images") or []), (adapter.get("description") or "")[:500],
            ])

        elif isinstance(item, CollectionItem):
            self._categories_writer.writerow([
                adapter["uid"], adapter.get("name"), adapter["url"], len(adapter.get("product_urls") or []),
            ])

        elif isinstance(item, OfferItem):
            self._offers_writer.writerow([
                adapter["product_uid"], adapter.get("store_uid"), adapter.get("store_name"),
                adapter["price"], adapter.get("old_price"), adapter.get("coupon_code"),
                adapter["affiliate_url"], adapter.get("position"), adapter.get("source_updated_at"),
                adapter.get("store_country"),
            ])

        return item


class PostgresPipeline:
    """
    Upserts products/brands/categories/stores/offers and appends a
    price_history row per offer on every crawl run. Disabled by setting
    PG_ENABLED = False (or VAPOSPY_PG_ENABLED=0) for CSV-only dry runs.
    """

    def __init__(self, pg_dsn, enabled):
        self.pg_dsn = pg_dsn
        self.enabled = enabled
        self.conn = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings.get("PG_DSN"), crawler.settings.getbool("PG_ENABLED", True))

    def open_spider(self, spider):
        if not self.enabled:
            spider.logger.info("PostgresPipeline disabled (PG_ENABLED=0)")
            return
        self.spider = spider
        self._connect()

    def _connect(self):
        import os

        import psycopg2

        database_url = os.environ.get("DATABASE_URL")
        if database_url:
            self.conn = psycopg2.connect(database_url)
        else:
            self.conn = psycopg2.connect(**self.pg_dsn)
        self.conn.autocommit = True

    def close_spider(self, spider):
        if self.conn:
            self.conn.close()

    def process_item(self, item, spider):
        if not self.enabled:
            return item
        adapter = ItemAdapter(item)

        try:
            self._process(adapter, item)
        except Exception:
            # Long crawls can outlive a proxied/idle DB connection (e.g.
            # Railway's public TCP proxy). Reconnect once and retry this
            # single item rather than silently losing everything after
            # the drop.
            spider.logger.warning("DB error, reconnecting and retrying item", exc_info=True)
            self._connect()
            self._process(adapter, item)

    def _process(self, adapter, item):
        if isinstance(item, ProductItem):
            self._upsert_product(adapter)
        elif isinstance(item, CollectionItem):
            self._upsert_category(adapter)
        elif isinstance(item, OfferItem):
            self._upsert_offer(adapter)

        return item

    def _upsert_product(self, p):
        with self.conn.cursor() as cur:
            brand_id = None
            if p.get("brand"):
                cur.execute(
                    """INSERT INTO brands (name, slug) VALUES (%s, %s)
                       ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                       RETURNING id""",
                    (p["brand"], self._slugify(p["brand"])),
                )
                brand_id = cur.fetchone()[0]

            slug = p["url"].rstrip("/").rsplit("/", 1)[-1]
            cur.execute(
                """INSERT INTO products
                       (source_id, uid, name, slug, url, brand_id, description, gtin,
                        low_price, high_price, offer_count, last_crawled_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
                   ON CONFLICT (uid) DO UPDATE SET
                       name = EXCLUDED.name, brand_id = EXCLUDED.brand_id,
                       description = EXCLUDED.description, gtin = EXCLUDED.gtin,
                       low_price = EXCLUDED.low_price, high_price = EXCLUDED.high_price,
                       offer_count = EXCLUDED.offer_count, last_crawled_at = now()
                   RETURNING id""",
                (
                    p.get("source_id"), p["uid"], p.get("name"), slug, p["url"], brand_id,
                    p.get("description"), p.get("gtin"), p.get("low_price"), p.get("high_price"),
                    p.get("offer_count"),
                ),
            )
            product_id = cur.fetchone()[0]

            for pos, image_url in enumerate(p.get("images") or []):
                cur.execute(
                    """INSERT INTO images (product_id, url, position) VALUES (%s, %s, %s)
                       ON CONFLICT (product_id, url) DO NOTHING""",
                    (product_id, image_url, pos),
                )

            for cat in p.get("categories") or []:
                cur.execute(
                    """INSERT INTO categories (uid, name, url) VALUES (%s, %s, %s)
                       ON CONFLICT (uid) DO UPDATE SET name = EXCLUDED.name
                       RETURNING id""",
                    (cat["uid"], cat["name"], cat["url"]),
                )
                category_id = cur.fetchone()[0]
                cur.execute(
                    """INSERT INTO product_categories (product_id, category_id) VALUES (%s, %s)
                       ON CONFLICT DO NOTHING""",
                    (product_id, category_id),
                )

    def _upsert_category(self, c):
        with self.conn.cursor() as cur:
            cur.execute(
                """INSERT INTO categories (uid, name, url) VALUES (%s, %s, %s)
                   ON CONFLICT (uid) DO UPDATE SET name = EXCLUDED.name""",
                (c["uid"], c.get("name"), c["url"]),
            )

    def _upsert_offer(self, o):
        with self.conn.cursor() as cur:
            cur.execute("SELECT id FROM products WHERE uid = %s", (o["product_uid"],))
            row = cur.fetchone()
            if not row:
                return  # product not loaded yet (out-of-order item); skip, next crawl fixes it
            product_id = row[0]

            store_uid = o.get("store_uid") or self._slugify(o.get("store_name") or o["affiliate_url"])
            cur.execute(
                """INSERT INTO stores (uid, name, logo_url, country, about_text)
                   VALUES (%s, %s, %s, %s, %s)
                   ON CONFLICT (uid) DO UPDATE SET
                       name = EXCLUDED.name, logo_url = EXCLUDED.logo_url,
                       country = EXCLUDED.country, about_text = EXCLUDED.about_text
                   RETURNING id""",
                (store_uid, o.get("store_name") or store_uid, o.get("store_logo"),
                 o.get("store_country"), o.get("store_about")),
            )
            store_id = cur.fetchone()[0]

            cur.execute(
                """INSERT INTO offers
                       (product_id, store_id, source_offer_id, price, old_price, coupon_code,
                        coupon_note, affiliate_url, position, source_updated_at, last_crawled_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
                   ON CONFLICT (product_id, store_id) DO UPDATE SET
                       price = EXCLUDED.price, old_price = EXCLUDED.old_price,
                       coupon_code = EXCLUDED.coupon_code, coupon_note = EXCLUDED.coupon_note,
                       affiliate_url = EXCLUDED.affiliate_url, position = EXCLUDED.position,
                       source_updated_at = EXCLUDED.source_updated_at, last_crawled_at = now()""",
                (product_id, store_id, o.get("source_offer_id"), o["price"], o.get("old_price"),
                 o.get("coupon_code"), o.get("coupon_note"), o["affiliate_url"], o.get("position"),
                 o.get("source_updated_at")),
            )

            cur.execute(
                """INSERT INTO price_history (product_id, store_id, price, old_price)
                   VALUES (%s, %s, %s, %s)""",
                (product_id, store_id, o["price"], o.get("old_price")),
            )

    @staticmethod
    def _slugify(text):
        return "".join(c.lower() if c.isalnum() else "-" for c in text).strip("-")
