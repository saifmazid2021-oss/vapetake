# Vapospy page-layout structure (reference notes, not copied HTML/CSS)

These are structural observations only — section order, purpose, and data
shown per section — so you can design your own look for each page type. No
markup, class names as design tokens, colors, fonts, or CSS were copied.

## Homepage

1. **Top nav** — logo, search box, region/currency selector.
2. **Main content** (two-column: content + right sidebar)
   - Primary content: category/brand entry points.
   - Sidebar: filter or quick-nav links.
3. **Region picker footer band** — links grouped by Americas / Europe / Asia
   Pacific, reflecting the multi-locale/multi-currency catalog (matches the
   15+ locale sitemaps found: en_gb, de_de, fr_ca, en_au, etc.).
4. **Footer** — standard site links.

## Category / brand page (e.g. `/pax-vaporizers`)

1. **Breadcrumb** — Category > Subcategory trail.
2. **H1** — category/brand name, often with a price-range subtitle
   ("KandyPens Vaporizer • from $50 to $80").
3. **Product grid** — responsive card grid (1 col mobile / 2 col tablet /
   3 col desktop). Each card:
   - Product image (square, lazy-loaded except first/above-fold)
   - Product name
   - "from $X" starting price
   - 1–2 line description excerpt
   - Whole card links to the product detail page
4. No pagination observed on the sampled categories (all products render in
   one page) — categories in this catalog are small (single digits to ~30
   products); worth re-checking on the largest category before assuming this
   holds everywhere.

## Product detail page (e.g. `/pax-3`)

1. **Breadcrumb** — Category > Brand.
2. **Header** — H1 product name + brand line.
3. **Structured data** (JSON-LD `Product` + `AggregateOffer`) driving
   price-range display: low/high price and total offer count.
4. **Media gallery** — multiple product images; often includes embedded
   YouTube review/tutorial videos (`VideoObject` JSON-LD).
5. **Offer comparison list** — the core "price comparison" feature. Repeated
   per retailer, ordered by `position`:
   - Retailer logo + name
   - Current price, with old/strikethrough price if discounted
   - Optional coupon code + savings note
   - "Buy Now" affiliate button (opens retailer site in new tab)
   - "Last updated" timestamp (freshness signal, builds trust)
   - Expandable "About the seller" — free-text blurb, country flag/name,
     "Verified by X" / "Authorized retailer" trust badges
6. Long-form **description** further down (likely SEO/AI-generated content,
   below the fold).

## Design takeaways worth carrying into your own build

- Price comparison lives at the **offer**, not the product, level — every
  product is really "1 product, N retailer offers." Your DB schema already
  reflects this (`products` 1—N `offers` 1—N `price_history`).
- Trust signals per offer (last-updated timestamp, seller verification,
  country) meaningfully differentiate a comparison site from a plain
  product catalog — worth keeping in your own UI even with a different look.
- Multi-locale/currency is baked in at the URL/sitemap level on Vapospy;
  your MVP can ignore this and add it later if you expand beyond one market.
