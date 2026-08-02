import type { ReactNode } from "react";
import "./globals.css";

export const metadata = {
  title: "VapeTake",
  description: "Price comparison for vaporizers across retailers",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="site-header">
          <a href="/" className="brand">VapeTake</a>
        </header>
        <main className="site-main">{children}</main>
      </body>
    </html>
  );
}
