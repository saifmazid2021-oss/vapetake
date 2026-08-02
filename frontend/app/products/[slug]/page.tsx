import { fetchProduct } from "@/lib/api";
import { notFound } from "next/navigation";

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
        {product.categories.map((c) => c.name).join(" / ") || "Vaporizers"}
      </p>

      <div className="product-detail">
        {product.images[0] && <img src={product.images[0].url} alt={product.name} />}
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
            {offer.store_logo && <img className="logo" src={offer.store_logo} alt={offer.store_name} />}
            <div>
              <div className="store-name">{offer.store_name}</div>
              {offer.store_country && <div className="updated">{offer.store_country}</div>}
              {offer.coupon_code && (
                <div className="coupon">Code {offer.coupon_code}{offer.coupon_note ? ` — ${offer.coupon_note}` : ""}</div>
              )}
              {offer.source_updated_at && <div className="updated">Updated {offer.source_updated_at}</div>}
            </div>
            <div className="price-block">
              {offer.old_price && <span className="old-price">${offer.old_price.toFixed(2)}</span>}
              <span className="price">${offer.price.toFixed(2)}</span>
            </div>
            <a className="buy-btn" href={offer.affiliate_url} target="_blank" rel="noopener noreferrer">
              Buy Now
            </a>
          </div>
        ))}
      </div>
    </>
  );
}
