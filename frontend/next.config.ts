import path from "path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  outputFileTracingRoot: path.join(__dirname),
  async rewrites() {
    const dest = process.env.API_INTERNAL_URL ?? "http://localhost:8020";
    return [{ source: "/api/:path*", destination: `${dest}/:path*` }];
  },
};

export default nextConfig;
