const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export type ProductSummary = {
  id: number;
  uid: string;
  name: string;
  slug: string;
  url: string;
  brand: string | null;
  low_price: number | null;
  high_price: number | null;
  offer_count: number | null;
  image: string | null;
};

export type Offer = {
  price: number;
  old_price: number | null;
  coupon_code: string | null;
  coupon_note: string | null;
  affiliate_url: string;
  position: number;
  source_updated_at: string | null;
  store_name: string;
  store_logo: string | null;
  store_country: string | null;
};

export type ProductDetail = ProductSummary & {
  description: string | null;
  images: { url: string }[];
  categories: { uid: string; name: string; url: string }[];
  offers: Offer[];
};

export async function fetchProducts(params: { q?: string; brand?: string; category?: string } = {}) {
  const search = new URLSearchParams(params as Record<string, string>);
  const res = await fetch(`${API_BASE}/products?${search}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load products (${res.status})`);
  return res.json() as Promise<{ items: ProductSummary[]; total: number }>;
}

export async function fetchProduct(slug: string) {
  const res = await fetch(`${API_BASE}/products/${slug}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load product (${res.status})`);
  return res.json() as Promise<ProductDetail>;
}
