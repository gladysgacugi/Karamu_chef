"use client";

// Popular chef packages, with buttons to filter them by service.
// Cards are hidden with inline styles, never by changing className, because AOS keeps its own classes on them.
import Link from "next/link";
import { useState } from "react";
import type { PackageWithChef, Service } from "@/lib/api";
import { chefUrl, price, truncate } from "@/lib/format";

export default function PackageGrid({ packages, services }: { packages: PackageWithChef[]; services: Service[] }) {
  const [filter, setFilter] = useState<string | null>(null); // null until a button is pressed
  const [fading, setFading] = useState(false);

  // Fade the remaining cards back in, as main.js does
  function choose(f: string) {
    setFilter(f);
    setFading(true);
    setTimeout(() => setFading(false), 60);
  }

  const buttonClass = (f: string) => `filtbtn${(filter ?? "all") === f ? " active" : ""}`;

  return (
    <>
      {services.length > 1 && (
        <div className="text-center mb-4" data-aos="fade-up">
          <button className={buttonClass("all")} onClick={() => choose("all")}>All</button>
          {services.map((service) => (
            <button key={service.slug} className={buttonClass(service.slug)} onClick={() => choose(service.slug)}>{service.name}</button>
          ))}
        </div>
      )}
      <div className="row g-4" id="mgrid">
        {packages.map((pkg, i) => {
          const category = pkg.service?.slug ?? "other";
          const hidden = filter !== null && filter !== "all" && filter !== category;
          return (
            <div
              key={pkg.id}
              className="col-sm-6 col-lg-4 mwrap"
              data-c={category}
              data-aos="fade-up"
              data-aos-delay={[0, 80, 160][i % 3]}
              style={
                filter === null
                  ? undefined
                  : hidden
                    ? { display: "none" }
                    : { transition: "opacity .38s,transform .38s", opacity: fading ? 0 : 1, transform: `translateY(${fading ? 16 : 0}px)` }
              }
            >
              <Link href={`${chefUrl(pkg.chef.slug)}?package=${pkg.id}#book`} className="mcard pkglink">
                <div className="mimg">
                  <img src={pkg.chef.photo} alt={pkg.chef.name} loading="lazy" />
                  {pkg.chef.is_verified && <div className="mbdg new"><i className="fas fa-check-circle"></i> Verified</div>}
                </div>
                <div className="mbody">
                  <div className="mcat">{pkg.service && <>{pkg.service.name} &middot; </>}{pkg.chef.name}, {pkg.chef.city}</div>
                  <div className="mtit">{pkg.name}</div>
                  <div className="mdesc">{truncate(pkg.description, 90)}</div>
                  <div className="mfoot">
                    <div className="mprice">KSh {price(pkg.price)} <small style={{ textDecoration: "none" }}>{pkg.price_unit}</small></div>
                    <span className="madd" title="Book this package"><i className="fas fa-arrow-right"></i></span>
                  </div>
                </div>
              </Link>
            </div>
          );
        })}
        {packages.length === 0 && (
          <div className="col-12 text-center">
            <p className="sdesc">Our chefs are adding their menus now. <Link href="/marketplace">Browse chefs</Link> or <a href="#reservation">tell us what you need</a> and we&apos;ll find you one.</p>
          </div>
        )}
      </div>
    </>
  );
}
