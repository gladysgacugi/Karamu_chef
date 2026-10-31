"use client";

// The site-wide behaviour from base.html and main.js: Bootstrap (mobile menu), the navbar/back-to-top
// scroll effects, homepage scroll-spy and smooth scrolling to #sections. AOS is on the homepage (app/_home/Aos.tsx).
import Script from "next/script";
import { usePathname } from "next/navigation";
import { useEffect } from "react";

export default function SiteScripts() {
  const pathname = usePathname();

  useEffect(() => {
    const isHome = pathname === "/";
    function onScroll() {
      document.getElementById("nav")?.classList.toggle("scrolled", window.scrollY > 60);
      document.getElementById("btt")?.classList.toggle("show", window.scrollY > 300);
      if (!isHome) return;
      document.querySelectorAll<HTMLElement>("section[id]").forEach((sec) => {
        const top = sec.offsetTop - 110;
        if (window.scrollY >= top && window.scrollY < top + sec.offsetHeight) {
          document.querySelectorAll(".nav-link").forEach((l) => l.classList.remove("active"));
          document.querySelector(`.nav-link[href="#${sec.id}"]`)?.classList.add("active");
        }
      });
    }

    function onClick(e: MouseEvent) {
      const link = (e.target as Element).closest?.('a[href^="#"]');
      const href = link?.getAttribute("href");
      if (!href || href === "#") return;
      const target = document.querySelector<HTMLElement>(href);
      if (!target) return;
      e.preventDefault();
      document.getElementById("navmenu")?.classList.remove("show");
      setTimeout(() => window.scrollTo({ top: target.offsetTop - 78, behavior: "smooth" }), 50);
    }

    window.addEventListener("scroll", onScroll);
    document.addEventListener("click", onClick);
    return () => {
      window.removeEventListener("scroll", onScroll);
      document.removeEventListener("click", onClick);
    };
  }, [pathname]);

  return (
    <>
      <button id="btt" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}><i className="fas fa-chevron-up"></i></button>
      <Script src="/static/js/bootstrap.bundle.min.js" />
    </>
  );
}
