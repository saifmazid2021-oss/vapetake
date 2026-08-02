import Link from "next/link";
import Image from "next/image";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { fetchCategories, fetchProducts } from "@/lib/api";

export async function generateMetadata({ params }: { params: { uid: string } }): Promise<Metadata> {
  const categories = await fetchCategories();
  const category = categories.find((c) => c.uid === params.uid);
  if (!category) return {};
  return {
    title: category.name,
    description: `Compare prices on ${category.name} across trusted retailers. ${category.product_count} products tracked.`,
    alternates: { canonical: `/category/${category.uid}` },
  };
}

export default async function CategoryPage({ params }: { params: { uid: string } }) {
  const categories = await fetchCategories();
  const category = categories.find((c) => c.uid === params.uid);
  if (!category) notFound();

  const { items, total } = await fetchProducts({ category: category.uid, limit: 60 });

  return (
    <>
      <p className="breadcrumb">
        <Link href="/category">All Categories</Link> / {category.name}
      </p>
      <h1>{category.name}</h1>
      <p className="result-count">{total} products</p>
      <div className="product-grid">
        {items.map((p) => (
          <Link key={p.uid} className="product-card" href={`/products/${p.slug}`}>
            {p.image && (
              <Image src={p.image} alt={p.name} width={220} height={220} className="product-card-img" />
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
