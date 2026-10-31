import type { NextConfig } from "next";

const djangoUrl = process.env.DJANGO_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  // The dev server only trusts localhost; without this, opening http://127.0.0.1:3000 blocks its websocket, the page
  // never hydrates and AOS/Bootstrap never load, so every [data-aos] section stays invisible
  allowedDevOrigins: ["127.0.0.1"],
  // The same URLs as the Django site (/marketplace/, /account/login/...), so links in emails and on Django pages work
  trailingSlash: true,
  async rewrites() {
    return {
      beforeFiles: [],
      afterFiles: [],
      // Anything without a Next.js page goes to Django: the API, the chef and team dashboards, admin, static files and
      // uploads. Both sites then share one address, so the Django login session works on both.
      fallback: [
        { source: "/:path*/", destination: `${djangoUrl}/:path*/` },
        { source: "/:path*", destination: `${djangoUrl}/:path*` },
      ],
    };
  },
};

export default nextConfig;
