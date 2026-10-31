"use client";

// The marketplace search form. Changing a dropdown searches straight away, like the Django page.
import Form from "next/form";
import type { City, Service } from "@/lib/api";

export const SORT_OPTIONS: Record<string, string> = {
  featured: "Featured",
  rating: "Top rated",
  price_low: "Price: low to high",
  price_high: "Price: high to low",
};

type Props = { services: Service[]; cities: City[]; query: string; service?: string; city?: string; sort: string };

export default function Filters({ services, cities, query, service, city, sort }: Props) {
  const submit = (e: React.ChangeEvent<HTMLSelectElement>) => e.currentTarget.form?.requestSubmit();
  return (
    // Keyed by the search so the fields reset to the URL after navigating
    <Form action="/marketplace" className="mkfilter" key={[query, service, city, sort].join("|")}>
      <div className="mkfield mkq">
        <i className="fas fa-search"></i>
        <input type="text" name="q" defaultValue={query} placeholder="Search chefs, dishes or areas..." />
      </div>
      <div className="mkfield">
        <select name="service" defaultValue={service ?? ""} onChange={submit}>
          <option value="">All services</option>
          {services.map((s) => <option key={s.slug} value={s.slug}>{s.name}</option>)}
        </select>
      </div>
      <div className="mkfield">
        <select name="city" defaultValue={city ?? ""} onChange={submit}>
          <option value="">All cities</option>
          {cities.map((c) => <option key={c.slug} value={c.slug}>{c.name}</option>)}
        </select>
      </div>
      <div className="mkfield">
        <select name="sort" defaultValue={sort} onChange={submit}>
          {Object.entries(SORT_OPTIONS).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
        </select>
      </div>
      <button type="submit" className="btn-red"><i className="fas fa-search"></i>Search</button>
    </Form>
  );
}
