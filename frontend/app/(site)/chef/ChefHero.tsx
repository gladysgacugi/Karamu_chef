import Link from "next/link";
import type { ReactNode } from "react";

/** The top of a chef dashboard page, with the way back to the bookings. */
export default function ChefHero({ eyebrow = "Chef dashboard", title, children }: { eyebrow?: string; title: ReactNode; children?: ReactNode }) {
  return (
    <section className="mkhero dbhero">
      <div className="container">
        <Link href="/chef/" className="dbback"><i className="fas fa-arrow-left"></i> Back to bookings</Link>
        <span className="slbl">{eyebrow}</span>
        <h1 className="stitle">{title}</h1>
        {children && <p className="sdesc">{children}</p>}
      </div>
    </section>
  );
}
