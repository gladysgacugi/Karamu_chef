// The chef marketplace (Django: marketplace.html), with the same ?service=, ?city=, ?q=, ?sort= and ?page= filters.
import type { Metadata } from "next";
import Link from "next/link";
import ChefCard from "@/components/ChefCard";
import WhatsAppFloat from "@/components/WhatsAppFloat";
import { getChefsPage, getCities, getServices, PAGE_SIZE } from "@/lib/api";
import { first, pluralize } from "@/lib/format";
import Filters, { SORT_OPTIONS } from "./Filters";

type Search = Record<string, string | string[] | undefined>;

/** The filters in the URL, matched against the real services and cities as views.filter_marketplace does. */
async function readFilters(searchParams: Promise<Search>) {
  const [params, services, cities] = await Promise.all([searchParams, getServices(), getCities()]);
  const sort = first(params.sort);
  return {
    params,
    services,
    cities,
    service: services.find((s) => s.slug === first(params.service)),
    city: cities.find((c) => c.slug === first(params.city)),
    query: first(params.q).trim(),
    sort: sort in SORT_OPTIONS ? sort : "featured",
  };
}

export async function generateMetadata({ searchParams }: PageProps<"/marketplace">): Promise<Metadata> {
  const { service, city } = await readFilters(searchParams);
  const where = city ? ` in ${city.name}` : "";
  return {
    title: `${service ? service.name : "Find a Chef"}${where} - Karamu`,
    description: `Browse verified private chefs, caterers and home cooks${city ? ` in ${city.name}` : " across Kenya"}. Compare menus, prices and reviews, then book in minutes.`,
  };
}

export default async function Marketplace({ searchParams }: PageProps<"/marketplace">) {
  const { params, services, cities, service, city, query, sort } = await readFilters(searchParams);
  const { page, number } = await getChefsPage({
    service: first(params.service), city: first(params.city), q: query, sort, page: first(params.page),
  });
  const pages = Math.max(1, Math.ceil(page.count / PAGE_SIZE));

  // Keep the active filters when moving between pages
  const filterParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (key !== "page") for (const v of [value ?? []].flat()) filterParams.append(key, v);
  }
  const pageUrl = (n: number) => `/marketplace?${filterParams.size ? `${filterParams}&` : ""}page=${n}`;
  const cityParam = city ? `city=${city.slug}` : "";

  return (
    <>
      {/* MARKETPLACE HEADER */}
      <section className="mkhero">
        <div className="container">
          <span className="slbl">The Chef Marketplace</span>
          <h1 className="stitle">
            {service ? service.name : <>Find Your <span>Perfect Chef</span></>}
            {city && <> in <span>{city.name}</span></>}
          </h1>
          <p className="sdesc">{service ? service.description : "Private chefs, caterers, meal prep and cooking classes. Compare real profiles, menus and prices, then book in minutes."}</p>

          <Filters services={services} cities={cities} query={query} service={service?.slug} city={city?.slug} sort={sort} />

          {/* SERVICE PILLS */}
          <div className="mkpills">
            <Link href={`/marketplace?${cityParam}`} className={service ? "" : "active"}>All</Link>
            {services.map((s) => (
              <Link key={s.slug} href={`/marketplace?service=${s.slug}${cityParam && `&${cityParam}`}`} className={s.slug === service?.slug ? "active" : ""}>
                <i className={`fas ${s.icon}`}></i>{s.name}
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* RESULTS */}
      <section className="mkresults">
        <div className="container">
          <div className="mkcount">
            <strong>{page.count}</strong> chef{pluralize(page.count)} found
            {(query || service || city) && <> <Link href="/marketplace"><i className="fas fa-times"></i> Clear filters</Link></>}
          </div>
          <div className="row g-4">
            {page.results.map((chef) => (
              <div key={chef.slug} className="col-sm-6 col-lg-4 col-xl-3"><ChefCard chef={chef} /></div>
            ))}
            {page.results.length === 0 && (
              <div className="col-12">
                <div className="mkempty">
                  <i className="fas fa-search"></i>
                  <h5>No chefs match your search yet</h5>
                  <p>Try another service or city, or tell us what you need and we&apos;ll find a chef for you.</p>
                  <Link href="/#contact-section" className="btn-red"><i className="fas fa-paper-plane"></i>Request a Chef</Link>
                </div>
              </div>
            )}
          </div>

          {pages > 1 && (
            <nav className="mkpages">
              {number > 1 && <Link href={pageUrl(number - 1)}><i className="fas fa-chevron-left"></i></Link>}
              {Array.from({ length: pages }, (_, i) => i + 1).map((n) => (
                <Link key={n} href={pageUrl(n)} className={n === number ? "active" : ""}>{n}</Link>
              ))}
              {number < pages && <Link href={pageUrl(number + 1)}><i className="fas fa-chevron-right"></i></Link>}
            </nav>
          )}
        </div>
      </section>

      {/* CTA */}
      <section className="mkcta">
        <div className="container text-center">
          <h2 className="stitle" style={{ color: "#fff" }}>Are You a <span style={{ color: "var(--secondary)" }}>Chef?</span></h2>
          <p>Join Karamu, get bookings from customers near you and get paid via M-Pesa.</p>
          <Link href="/#hours" className="btn-red"><i className="fas fa-user-plus"></i>Become a Chef Partner</Link>
        </div>
      </section>

      <WhatsAppFloat />
    </>
  );
}
