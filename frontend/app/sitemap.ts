import type { MetadataRoute } from "next";
import { fetchCategories, fetchProducts } from "@/lib/api";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://vapetake.com";

async function fetchAllProducts() {
  const products = [];
  let offset = 0;
  const limit = 100;
  for (;;) {
    const { items, total } = await fetchProducts({ limit, offset });
    products.push(...items);
    offset += limit;
    if (offset >= total || items.length === 0) break;
  }
  return products;
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const [categories, products] = await Promise.all([
    fetchCategories().catch(() => []),
    fetchAllProducts().catch(() => []),
  ]);

  const staticEntries: MetadataRoute.Sitemap = [
    { url: `${SITE_URL}/`, changeFrequency: "daily", priority: 1 },
    { url: `${SITE_URL}/category`, changeFrequency: "daily", priority: 0.8 },
  ];

  const categoryEntries: MetadataRoute.Sitemap = categories.map((c) => ({
    url: `${SITE_URL}/category/${c.uid}`,
    changeFrequency: "daily",
    priority: 0.7,
  }));

  const productEntries: MetadataRoute.Sitemap = products.map((p) => ({
    url: `${SITE_URL}/products/${p.slug}`,
    changeFrequency: "daily",
    priority: 0.6,
  }));

  return [...staticEntries, ...categoryEntries, ...productEntries];
}
