import Link from "next/link";
import Image from "next/image";
import type { Metadata } from "next";
import { fetchProduct } from "@/lib/api";
import { notFound } from "next/navigation";

export async function generateMetadata({ params }: { params: { slug: string } }): Promise<Metadata> {
  let product;
  try {
    product = await fetchProduct(params.slug);
  } catch {
    return {};
  }

  const priceLine =
    product.low_price != null
      ? ` — from $${product.low_price.toFixed(2)} across ${product.offer_count ?? product.offers.length} retailers`
      : "";
  const title = product.brand ? `${product.name} — ${product.brand}` : product.name;

  return {
    title,
    description: (product.description || `Compare prices for ${product.name}.`).slice(0, 160) + priceLine,
    alternates: { canonical: `/products/${product.slug}` },
    openGraph: {
      title,
      description: product.description?.slice(0, 200),
      images: product.images[0] ? [product.images[0].url] : undefined,
    },
  };
}

export default async function ProductPage({ params }: { params: { slug: string } }) {
  let product;
  try {
    product = await fetchProduct(params.slug);
  } catch {
    notFound();
  }

  return (
    <>
      <p className="breadcrumb">
        <Link href="/">Home</Link>
        {product.categories.map((c) => (
          <span key={c.uid}>
            {" / "}
            <Link href={`/category/${c.uid}`}>{c.name}</Link>
          </span>
        ))}
      </p>

      <div className="product-detail">
        {product.images[0] && (
          <Image src={product.images[0].url} alt={product.name} width={320} height={320} priority />
        )}
        <div>
          <h1>{product.name}</h1>
          {product.brand && <p className="brand">{product.brand}</p>}
          {product.description && <p>{product.description}</p>}
        </div>
      </div>

      <h2>Compare {product.offers.length} offers</h2>
      <div className="offer-list">
        {product.offers.map((offer, i) => (
          <div className="offer-row" key={i}>
            {offer.store_logo && (
              <Image className="logo" src={offer.store_logo} alt={offer.store_name} width={90} height={40} />
            )}
            <div>
              <div className="store-name">{offer.store_name}</div>
              {offer.store_country && <div className="updated">{offer.store_country}</div>}
              {offer.coupon_code && (
                <div className="coupon">
                  Code {offer.coupon_code}
                  {offer.coupon_note ? ` — ${offer.coupon_note}` : ""}
                </div>
              )}
              {offer.source_updated_at && <div className="updated">Updated {offer.source_updated_at}</div>}
              {offer.store_about && (
                <details className="seller-trust">
                  <summary>About this seller</summary>
                  <p>{offer.store_about}</p>
                </details>
              )}
            </div>
            <div className="price-block">
              {offer.old_price && <span className="old-price">${offer.old_price.toFixed(2)}</span>}
              <span className="price">${offer.price.toFixed(2)}</span>
            </div>
            <a className="buy-btn" href={offer.affiliate_url} target="_blank" rel="noopener noreferrer sponsored">
              Buy Now
            </a>
          </div>
        ))}
      </div>
    </>
  );
}
