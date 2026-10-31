// Based on the "Sarab" template, Copyright (c) Bestwpware, distributed by ThemeWagon. MIT License - see /static/THIRD_PARTY_LICENSES.txt
// The page around everything. The website's top bar, navbar and footer are in (site)/layout.tsx; the team pages have a
// phone-friendly layout of their own (team/layout.tsx).
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Karamu - Your Chef is One Tap Away",
  description:
    "Karamu - book local chefs in Kenya for private dinners, parties, events and weekly meal prep. Compare menus and prices, then pay with M-Pesa once your chef confirms.",
  authors: [{ name: "Karamu" }],
  icons: { icon: "/static/img/brand/karamu-mark.svg", apple: "/static/img/brand/apple-touch-icon.png" },
};

// The same stylesheets as base.html, served by Django
const STYLESHEETS = ["bootstrap.min.css", "aos.css", "swiper-bundle.min.css", "all.min.css", "magnific-popup.css", "style.css", "marketplace.css", "team.css"];

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <head>
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;800;900&family=Poppins:wght@300;400;500;600;700&family=Dancing+Script:wght@700&display=swap"
        />
        {STYLESHEETS.map((file) => (
          <link key={file} rel="stylesheet" href={`/static/css/${file}`} />
        ))}
      </head>
      <body>{children}</body>
    </html>
  );
}
