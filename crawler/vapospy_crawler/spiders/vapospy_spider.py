import json
import re
from urllib.parse import urljoin, urlparse

import scrapy

from vapospy_crawler.items import CollectionItem, OfferItem, PageItem, ProductItem

ALLOWED_DOMAIN = "www.vapospy.com"
BASE = f"https://{ALLOWED_DOMAIN}"

# Only the default (US / no-locale-suffix) sitemaps -- the *-de_de, *-fr_fr, etc.
# variants are the same catalog in other locales/currencies and are skipped to
# avoid crawling everything 15x. Drop this filter if you want every locale.
SITEMAP_INDEX = f"{BASE}/sitemap.xml"
DEFAULT_LOCALE_SITEMAP_RE = re.compile(r"^https://www\.vapospy\.com/(products|collections)\.xml$")

# The site's language switcher cross-links ~18 locale prefixes (/en_au/,
# /de_ch/kontakt, /pl_pl/regulamin, ...), each of which re-links to all the
# others -- an unbounded trap for a same-domain link crawler. Every URL in
# products.xml/collections.xml has no locale prefix, so that's the canonical
# default locale; skip anything under a locale prefix during generic discovery.
LOCALE_PREFIX_RE = re.compile(r"^/[a-z]{2}_[a-z]{2}(/|$)")

PRICE_RE = re.compile(r"[\d,.]+")


def parse_price(text):
    if not text:
        return None
    m = PRICE_RE.search(text.replace(",", ""))
    return float(m.group()) if m else None


class VapospySpider(scrapy.Spider):
    """
    Rerunnable, full-site crawler for vapospy.com.

    Phase 1 (site map): discovers every internal URL by combining the site's
    own sitemap.xml (products + collections) with a same-domain link-follow
    from the homepage, and records url/status/title/canonical for each.

    Phase 2 (product data): for every URL in products.xml, parses full
    product detail + every retailer offer shown on the page.

    Run modes (via -a flag):
        scrapy crawl vapospy                     # full crawl
        scrapy crawl vapospy -a max_pages=50      # smoke test, caps total requests
    """

    name = "vapospy"
    allowed_domains = [ALLOWED_DOMAIN]

    def __init__(self, max_pages=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_pages = int(max_pages) if max_pages else None
        self._seen_urls = set()
        self._product_urls = set()
        self._collection_urls = set()
        self._pending_sitemaps = 0

    def start_requests(self):
        yield scrapy.Request(SITEMAP_INDEX, callback=self.parse_sitemap_index)

    async def start(self):
        # Scrapy >=2.13 replaced start_requests() with this async entry
        # point; older versions still call start_requests() directly, so
        # keep both and just delegate here for forward compatibility.
        for request in self.start_requests():
            yield request

    def parse_sitemap_index(self, response):
        response.selector.remove_namespaces()
        sub_sitemaps = response.xpath("//loc/text()").getall()
        targets = [u for u in sub_sitemaps if DEFAULT_LOCALE_SITEMAP_RE.match(u)]
        self.logger.info("Found %d default-locale sitemaps to expand", len(targets))
        self._pending_sitemaps = len(targets)
        for url in targets:
            yield scrapy.Request(url, callback=self.parse_url_sitemap)

    def parse_url_sitemap(self, response):
        response.selector.remove_namespaces()
        urls = response.xpath("//loc/text()").getall()
        is_products = response.url.endswith("/products.xml")
        for url in urls:
            if self._at_limit():
                break
            if is_products:
                self._product_urls.add(url)
                # Higher priority than the generic crawl below, so the real
                # product parse always wins if a link-crawled duplicate of
                # the same URL is discovered around the same time.
                yield scrapy.Request(url, callback=self.parse_product, priority=10,
                                      meta={"page_type": "product"})
            else:
                self._collection_urls.add(url)
                yield scrapy.Request(url, callback=self.parse_collection, priority=10,
                                      meta={"page_type": "collection"})

        # Only start the generic same-domain link crawl once every sitemap
        # has been fully expanded, so self._product_urls/_collection_urls
        # are complete and the generic crawler doesn't race the sitemap
        # requests for the same URLs (whichever request Scrapy's dupefilter
        # sees first wins, and we need that to always be the sitemap one).
        self._pending_sitemaps -= 1
        if self._pending_sitemaps == 0 and not self._at_limit():
            # Catches pages that aren't in products.xml/collections.xml
            # (about, deals, search, static pages, etc.)
            yield scrapy.Request(BASE + "/", callback=self.parse_generic_page)

    # ---------- Phase 1: generic discovery + sitemap.csv/all_urls.txt rows ----------

    def parse_generic_page(self, response):
        yield self._page_row(response, "page")
        if self._at_limit():
            return
        for href in response.css("a::attr(href)").getall():
            url = urljoin(response.url, href).split("#")[0]
            parsed = urlparse(url)
            if parsed.netloc != ALLOWED_DOMAIN:
                continue
            if LOCALE_PREFIX_RE.match(parsed.path):
                continue
            if url in self._seen_urls or self._at_limit():
                continue
            self._seen_urls.add(url)
            if url in self._product_urls:
                continue  # already scheduled via sitemap with the right callback
            if url in self._collection_urls:
                continue
            yield scrapy.Request(url, callback=self.parse_generic_page, errback=self.parse_generic_error)

    def parse_generic_error(self, failure):
        response = getattr(failure.value, "response", None)
        if response is not None:
            yield self._page_row(response, "page")

    def _page_row(self, response, page_type):
        title = response.css("title::text").get(default="").strip()
        canonical = response.css('link[rel="canonical"]::attr(href)').get()
        item = PageItem()
        item["url"] = response.url
        item["status"] = response.status
        item["title"] = title
        item["canonical"] = canonical
        item["page_type"] = page_type
        return item

    def _at_limit(self):
        return self.max_pages is not None and len(self._seen_urls) >= self.max_pages

    # ---------- Phase 2: product detail ----------

    def parse_product(self, response):
        yield self._page_row(response, "product")

        product_json = None
        breadcrumb_json = None
        for script in response.css('script[type="application/ld+json"]::text').getall():
            try:
                data = json.loads(script)
            except (json.JSONDecodeError, TypeError):
                continue
            if isinstance(data, dict) and data.get("@type") == "Product":
                product_json = data
            elif isinstance(data, dict) and data.get("@type") == "BreadcrumbList":
                breadcrumb_json = data

        name = response.css("h1::text").get(default="").strip()
        brand = response.css("p.product-brand::text").get(default="").strip() or None

        product_json = product_json or {}
        offers_agg = product_json.get("offers", {}) or {}

        categories = []
        if breadcrumb_json:
            for entry in breadcrumb_json.get("itemListElement", []):
                cat_url = entry.get("item")
                cat_name = entry.get("name")
                if cat_url and cat_name:
                    categories.append({
                        "uid": self._slug(cat_url),
                        "name": cat_name,
                        "url": cat_url,
                    })

        product_uid = "product_" + self._slug(response.url)
        product = ProductItem(
            url=response.url,
            uid=product_uid,
            source_id=product_json.get("productID"),
            name=name or product_json.get("name"),
            brand=brand or (product_json.get("brand") or {}).get("name"),
            description=product_json.get("description"),
            gtin=product_json.get("gtin14") or product_json.get("gtin"),
            low_price=parse_price(str(offers_agg.get("lowPrice", ""))),
            high_price=parse_price(str(offers_agg.get("highPrice", ""))),
            offer_count=offers_agg.get("offerCount"),
            images=product_json.get("image", []),
            categories=categories,
        )
        yield product

        for offer in self._parse_offers(response, product_uid):
            yield offer

    def _parse_offers(self, response, product_uid):
        for pos, block in enumerate(response.css("div.pli"), start=1):
            offer_link = block.css('a[data-click-name="offer"]')
            props_raw = offer_link.attrib.get("data-click-props", "")
            props = {}
            for token in props_raw.split(";"):
                if "=" in token:
                    k, v = token.split("=", 1)
                    props[k] = v

            price_text = block.css("span.pli-np::text").get()
            old_price_text = block.css("span.pli-np s::text").get()
            coupon_code = block.css("span.pli-nc strong::text").get()
            coupon_note = " ".join(t.strip() for t in block.css("span.pli-nc::text").getall() if t.strip())
            updated_text = block.css("small.pli-nu::text").get(default="")
            updated_text = updated_text.replace("↻", "").strip() or None
            about_paragraphs = block.css("div.mkdt-about-translated blockquote p::text").getall()
            country = block.css("p.ret-meta::text").get(default="").strip() or None
            store_name = block.css("img.pli-i::attr(alt)").get() or block.css("img.pli-i::attr(title)").get()
            store_logo = block.css("img.pli-i::attr(src)").get()
            affiliate_url = offer_link.attrib.get("href")

            price = parse_price(price_text)
            if price is None or not affiliate_url:
                continue  # not a real offer block

            yield OfferItem(
                product_uid=product_uid,
                store_uid=props.get("ruid"),
                store_name=store_name,
                store_logo=store_logo,
                store_country=country,
                store_about=" ".join(about_paragraphs).strip() or None,
                source_offer_id=int(props["oid"]) if props.get("oid", "").isdigit() else None,
                price=price,
                old_price=parse_price(old_price_text),
                coupon_code=coupon_code,
                coupon_note=coupon_note or None,
                affiliate_url=affiliate_url,
                position=int(props["pos"]) if props.get("pos", "").isdigit() else pos,
                source_updated_at=updated_text,
            )

    # ---------- Phase 2: collections/categories ----------

    def parse_collection(self, response):
        yield self._page_row(response, "collection")

        name = response.css("h1::text").get(default="").strip() or response.css("title::text").get(default="").strip()
        product_urls = response.css("a.pc-l::attr(href)").getall()

        yield CollectionItem(
            url=response.url,
            uid=self._slug(response.url),
            name=name,
            product_urls=product_urls,
        )

    @staticmethod
    def _slug(url):
        return urlparse(url).path.strip("/").replace("/", "_") or "home"
