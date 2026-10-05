import type { Metadata } from "next";
import Link from "next/link";
import { site } from "@/lib/site";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(site.url),
  title: { default: `${site.title} | ${site.teamName}`, template: `%s | ${site.teamName}` },
  description: site.description,
  openGraph: { title: site.title, description: site.description, siteName: site.teamName, type: "website" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Dela+Gothic+One&family=Zen+Kaku+Gothic+New:wght@400;500;700&family=JetBrains+Mono:wght@400;600&display=swap"
        />
      </head>
      <body>
        <div className="wrap">
          <nav className="site-nav">
            <Link href="/" className="brand">{site.teamName}</Link>
          </nav>
          {children}
          <footer className="site-foot">© {site.teamName}</footer>
        </div>
      </body>
    </html>
  );
}
