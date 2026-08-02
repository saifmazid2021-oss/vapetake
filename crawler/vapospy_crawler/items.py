import scrapy


class PageItem(scrapy.Item):
    """One row of the Phase 1 site-wide crawl map (sitemap.csv / all_urls.txt)."""
    url = scrapy.Field()
    status = scrapy.Field()
    title = scrapy.Field()
    canonical = scrapy.Field()
    page_type = scrapy.Field()  # product | collection | page


class ProductItem(scrapy.Item):
    url = scrapy.Field()
    uid = scrapy.Field()
    source_id = scrapy.Field()
    name = scrapy.Field()
    brand = scrapy.Field()
    description = scrapy.Field()
    gtin = scrapy.Field()
    low_price = scrapy.Field()
    high_price = scrapy.Field()
    offer_count = scrapy.Field()
    images = scrapy.Field()          # list[str]
    categories = scrapy.Field()      # list[{uid, name, url}]
    offers = scrapy.Field()          # list[OfferItem-like dicts]


class OfferItem(scrapy.Item):
    product_uid = scrapy.Field()
    store_uid = scrapy.Field()
    store_name = scrapy.Field()
    store_logo = scrapy.Field()
    store_country = scrapy.Field()
    store_about = scrapy.Field()
    source_offer_id = scrapy.Field()
    price = scrapy.Field()
    old_price = scrapy.Field()
    coupon_code = scrapy.Field()
    coupon_note = scrapy.Field()
    affiliate_url = scrapy.Field()
    position = scrapy.Field()
    source_updated_at = scrapy.Field()


class CollectionItem(scrapy.Item):
    url = scrapy.Field()
    uid = scrapy.Field()
    name = scrapy.Field()
    product_urls = scrapy.Field()  # list[str], products listed on this page
