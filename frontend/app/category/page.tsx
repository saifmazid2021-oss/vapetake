import Link from "next/link";
import type { Metadata } from "next";
import { fetchCategories } from "@/lib/api";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "All Categories",
  description: "Browse every vaporizer and dry-herb device category on VapeTake.",
  alternates: { canonical: "/category" },
};

export default async function CategoryIndexPage() {
  const categories = await fetchCategories();
  const sorted = [...categories].sort((a, b) => a.name.localeCompare(b.name));

  return (
    <>
      <h1>All Categories</h1>
      <ul className="category-list">
        {sorted.map((c) => (
          <li key={c.uid}>
            <Link href={`/category/${c.uid}`}>
              {c.name} <span className="count">({c.product_count})</span>
            </Link>
          </li>
        ))}
      </ul>
    </>
  );
}
