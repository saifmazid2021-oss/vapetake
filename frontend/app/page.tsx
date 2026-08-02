import Link from "next/link";
import Image from "next/image";
import type { Metadata } from "next";
import { fetchProducts } from "@/lib/api";

export function generateMetadata({ searchParams }: { searchParams: { q?: string } }): Metadata {
  if (searchParams.q) {
    return {
      title: `Search results for "${searchParams.q}"`,
      description: `Compare prices for vaporizers matching "${searchParams.q}" across trusted retailers.`,
    };
  }
  return { alternates: { canonical: "/" } };
}

export default async function HomePage({
  searchParams,
}: {
  searchParams: { q?: string };
}) {
  const { items, total } = await fetchProducts({ q: searchParams.q });

  return (
    <>
      <form className="search-bar" action="/">
        <input
          type="text"
          name="q"
          placeholder="Search vaporizers..."
          defaultValue={searchParams.q}
          aria-label="Search vaporizers"
        />
      </form>
      <p className="result-count">{total} products</p>
      <div className="product-grid">
        {items.map((p, i) => (
          <Link key={p.uid} className="product-card" href={`/products/${p.slug}`}>
            {p.image && (
              <Image
                src={p.image}
                alt={p.name}
                width={220}
                height={220}
                className="product-card-img"
                priority={i < 4}
              />
            )}
            <div className="name">{p.name}</div>
            {p.brand && <div className="brand">{p.brand}</div>}
            {p.low_price != null && (
              <div className="price">
                from ${p.low_price.toFixed(2)}
                {p.offer_count ? ` · ${p.offer_count} offers` : ""}
              </div>
            )}
          </Link>
        ))}
      </div>
    </>
  );
}
