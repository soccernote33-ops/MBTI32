import type { NextConfig } from "next";

// GitHub Pages の https://<owner>.github.io/<repo>/ で配信するときは "/<repo>" を渡す。
// 独自ドメインで配信するときは空のまま
const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

const nextConfig: NextConfig = {
  // 静的HTMLとして書き出す。GitHub Pages / Vercel / Cloudflare Pages など、どこでも配信できる
  output: "export",
  trailingSlash: true,
  basePath,
  images: { unoptimized: true },
};

export default nextConfig;
