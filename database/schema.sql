-- vapospy-clone schema
-- One row per product, per retailer offer, with historical price tracking.

CREATE TABLE IF NOT EXISTS brands (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    slug        TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS categories (
    id          SERIAL PRIMARY KEY,
    uid         TEXT NOT NULL UNIQUE,   -- e.g. "collection_pax_vaporizers"
    name        TEXT NOT NULL,
    url         TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS stores (
    id          SERIAL PRIMARY KEY,
    uid         TEXT NOT NULL UNIQUE,   -- retailer uid, e.g. "portablehookahs"
    name        TEXT NOT NULL,
    logo_url    TEXT,
    country     TEXT,
    about_text  TEXT
);

CREATE TABLE IF NOT EXISTS products (
    id              SERIAL PRIMARY KEY,
    source_id       INTEGER,            -- vapospy internal product id (pid)
    uid             TEXT NOT NULL UNIQUE, -- e.g. "product_pax3"
    name            TEXT NOT NULL,
    slug            TEXT NOT NULL UNIQUE, -- last path segment of url
    url             TEXT NOT NULL UNIQUE,
    brand_id        INTEGER REFERENCES brands(id),
    description     TEXT,
    gtin            TEXT,
    low_price       NUMERIC(10,2),
    high_price      NUMERIC(10,2),
    offer_count     INTEGER,
    first_seen_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_crawled_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS product_categories (
    product_id      INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    category_id     INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (product_id, category_id)
);

CREATE TABLE IF NOT EXISTS images (
    id          SERIAL PRIMARY KEY,
    product_id  INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    url         TEXT NOT NULL,
    position    INTEGER NOT NULL DEFAULT 0,
    UNIQUE (product_id, url)
);

-- Current/latest known offer per (product, store) -- upserted on every crawl.
CREATE TABLE IF NOT EXISTS offers (
    id              SERIAL PRIMARY KEY,
    product_id      INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    store_id        INTEGER NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    source_offer_id INTEGER,            -- vapospy offer id (oid)
    price           NUMERIC(10,2) NOT NULL,
    old_price       NUMERIC(10,2),
    coupon_code     TEXT,
    coupon_note     TEXT,
    affiliate_url   TEXT NOT NULL,
    position        INTEGER,
    availability    TEXT,               -- in_stock / out_of_stock / unknown
    source_updated_at TIMESTAMPTZ,       -- "updated" timestamp shown on vapospy
    last_crawled_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (product_id, store_id)
);

-- Append-only price history: one row per crawl per (product, store).
CREATE TABLE IF NOT EXISTS price_history (
    id              BIGSERIAL PRIMARY KEY,
    product_id      INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    store_id        INTEGER NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    price           NUMERIC(10,2) NOT NULL,
    old_price       NUMERIC(10,2),
    availability    TEXT,
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand_id);
CREATE INDEX IF NOT EXISTS idx_offers_product ON offers(product_id);
CREATE INDEX IF NOT EXISTS idx_offers_store ON offers(store_id);
CREATE INDEX IF NOT EXISTS idx_price_history_product_time ON price_history(product_id, recorded_at);
