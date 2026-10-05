import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 静的HTMLとして書き出す。Vercel / Cloudflare Pages / Netlify など、どこでも独自ドメインで配信できる
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
};

export default nextConfig;
