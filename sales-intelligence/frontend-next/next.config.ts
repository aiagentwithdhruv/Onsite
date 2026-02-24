import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    serverActions: {
      bodySizeLimit: "100mb",
    },
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: (process.env.API_URL || "http://localhost:8000") + "/api/:path*",
      },
    ];
  },
};

export default nextConfig;
