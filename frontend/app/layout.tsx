import type { ReactNode } from "react";
import type { Metadata, Viewport } from "next";
import Link from "next/link";
import { fetchCategories } from "@/lib/api";
import "./globals.css";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://vapetake.com";

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#101828",
};

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "VapeTake — Compare Vaporizer Prices Across Retailers",
    template: "%s | VapeTake",
  },
  description:
    "Compare vaporizer and dry-herb device prices across trusted retailers. Real-time offers, coupon codes, and price history in one place.",
  openGraph: {
    siteName: "VapeTake",
    type: "website",
  },
};

export default async function RootLayout({ children }: { children: ReactNode }) {
  let topCategories: Awaited<ReturnType<typeof fetchCategories>> = [];
  try {
    const all = await fetchCategories();
    topCategories = [...all].sort((a, b) => b.product_count - a.product_count).slice(0, 6);
  } catch {
    // Nav degrades gracefully to just Home + All Categories if the API is briefly unreachable.
  }

  return (
    <html lang="en">
      <body>
        <header className="site-header">
          <Link href="/" className="brand">
            VapeTake
          </Link>
          <nav className="site-nav" aria-label="Main">
            {topCategories.map((c) => (
              <Link key={c.uid} href={`/category/${c.uid}`}>
                {c.name}
              </Link>
            ))}
            <Link href="/category">All Categories</Link>
          </nav>
        </header>
        <main className="site-main">{children}</main>
        <footer className="site-footer">
          <p>VapeTake compares prices from independent retailers. Prices and availability update regularly.</p>
        </footer>
      </body>
    </html>
  );
}
