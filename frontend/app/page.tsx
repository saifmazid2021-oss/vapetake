import { fetchProducts } from "@/lib/api";

export default async function HomePage({
  searchParams,
}: {
  searchParams: { q?: string };
}) {
  const { items, total } = await fetchProducts({ q: searchParams.q });

  return (
    <>
      <form className="search-bar" action="/">
        <input type="text" name="q" placeholder="Search vaporizers..." defaultValue={searchParams.q} />
      </form>
      <p className="breadcrumb">{total} products</p>
      <div className="product-grid">
        {items.map((p) => (
          <a key={p.uid} className="product-card" href={`/products/${p.slug}`}>
            {p.image && <img src={p.image} alt={p.name} />}
            <div className="name">{p.name}</div>
            {p.brand && <div className="brand">{p.brand}</div>}
            {p.low_price != null && (
              <div className="price">
                from ${p.low_price.toFixed(2)}
                {p.offer_count ? ` · ${p.offer_count} offers` : ""}
              </div>
            )}
          </a>
        ))}
      </div>
    </>
  );
}
