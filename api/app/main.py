from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.db import query, query_one

app = FastAPI(title="vapospy-clone API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/brands")
def list_brands():
    return query("SELECT id, name, slug FROM brands ORDER BY name")


@app.get("/categories")
def list_categories():
    return query(
        """SELECT c.id, c.uid, c.name, c.url, count(pc.product_id) AS product_count
           FROM categories c
           LEFT JOIN product_categories pc ON pc.category_id = c.id
           GROUP BY c.id ORDER BY c.name"""
    )


@app.get("/products")
def list_products(
    q: Optional[str] = None,
    brand: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(24, le=100),
    offset: int = 0,
):
    # Exclude products with zero retailer offers -- these are "ghost" entries
    # (discontinued/redirected pages on the source site) with no image, price,
    # or comparison value, so listing them is just broken-looking empty cards.
    clauses = ["EXISTS (SELECT 1 FROM offers o WHERE o.product_id = p.id)"]
    params = []

    if q:
        clauses.append("p.name ILIKE %s")
        params.append(f"%{q}%")
    if brand:
        clauses.append("b.slug = %s")
        params.append(brand)
    if category:
        clauses.append(
            "p.id IN (SELECT pc.product_id FROM product_categories pc "
            "JOIN categories c ON c.id = pc.category_id WHERE c.uid = %s)"
        )
        params.append(category)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    rows = query(
        f"""SELECT p.id, p.uid, p.name, p.slug, p.url, p.low_price, p.high_price,
                   p.offer_count, b.name AS brand,
                   (SELECT url FROM images WHERE product_id = p.id ORDER BY position LIMIT 1) AS image
            FROM products p
            LEFT JOIN brands b ON b.id = p.brand_id
            {where}
            ORDER BY p.last_crawled_at DESC
            LIMIT %s OFFSET %s""",
        [*params, limit, offset],
    )
    total = query_one(
        f"""SELECT count(*) AS n FROM products p LEFT JOIN brands b ON b.id = p.brand_id {where}""",
        params,
    )
    return {"items": rows, "total": total["n"] if total else 0, "limit": limit, "offset": offset}


@app.get("/products/{slug}")
def get_product(slug: str):
    product = query_one(
        """SELECT p.*, b.name AS brand
           FROM products p LEFT JOIN brands b ON b.id = p.brand_id
           WHERE p.slug = %s""",
        (slug,),
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product["images"] = query(
        "SELECT url FROM images WHERE product_id = %s ORDER BY position", (product["id"],)
    )
    product["categories"] = query(
        """SELECT c.uid, c.name, c.url FROM categories c
           JOIN product_categories pc ON pc.category_id = c.id
           WHERE pc.product_id = %s""",
        (product["id"],),
    )
    product["offers"] = query(
        """SELECT o.price, o.old_price, o.coupon_code, o.coupon_note, o.affiliate_url,
                  o.position, o.source_updated_at, s.name AS store_name, s.logo_url AS store_logo,
                  s.country AS store_country, s.about_text AS store_about
           FROM offers o JOIN stores s ON s.id = o.store_id
           WHERE o.product_id = %s ORDER BY o.position""",
        (product["id"],),
    )
    return product


@app.get("/products/{slug}/price-history")
def get_price_history(slug: str):
    product = query_one("SELECT id FROM products WHERE slug = %s", (slug,))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return query(
        """SELECT ph.recorded_at, ph.price, ph.old_price, s.name AS store_name
           FROM price_history ph JOIN stores s ON s.id = ph.store_id
           WHERE ph.product_id = %s ORDER BY ph.recorded_at""",
        (product["id"],),
    )
