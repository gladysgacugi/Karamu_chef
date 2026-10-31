"use client";

// Opened by the search button in the navbar. The form searches the marketplace.
import Form from "next/form";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import type { Service } from "@/lib/api";
import { serviceUrl } from "@/lib/format";

const POPULAR = ["Nyama Choma", "Pilau", "Mukimo", "Chapati", "Biryani", "Birthday"];

export default function SearchOverlay({ services }: { services: Service[] }) {
  const [open, setOpen] = useState(false);
  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const show = () => {
      setOpen(true);
      setTimeout(() => input.current?.focus(), 220);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("open-search", show);
    document.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("open-search", show);
      document.removeEventListener("keydown", onKey);
    };
  }, []);

  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  const close = () => setOpen(false);

  return (
    <div id="searchOv" className={open ? "open" : ""} onClick={(e) => e.target === e.currentTarget && close()}>
      <button className="sovclose" onClick={close}><i className="fas fa-times"></i></button>
      <div className="sovbox">
        <h4>What are you craving today?</h4>
        <Form className="sovinput" action="/marketplace" onSubmit={close}>
          <input ref={input} type="text" name="q" placeholder="Search nyama choma, pilau, chapati, chefs..." autoComplete="off" />
          <button type="submit" aria-label="Search"><i className="fas fa-search"></i></button>
        </Form>
        <div className="sovcats">
          {services.map((service) => (
            <Link key={service.slug} className="sovcat" href={serviceUrl(service.slug)} onClick={close}>
              <i className={`fas ${service.icon}`}></i>{service.name}
            </Link>
          ))}
        </div>
        <div className="sovtrend">
          <p><i className="fas fa-fire me-1" style={{ color: "var(--secondary)" }}></i>Popular Searches</p>
          {POPULAR.map((term) => (
            <Link key={term} className="ttag" href={`/marketplace?q=${term.toLowerCase().replace(" ", "+")}`} onClick={close}>{term}</Link>
          ))}
        </div>
      </div>
    </div>
  );
}
