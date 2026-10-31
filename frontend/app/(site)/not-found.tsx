import Link from "next/link";

export default function NotFound() {
  return (
    <section className="mkresults">
      <div className="container">
        <div className="mkempty">
          <i className="fas fa-search"></i>
          <h5>We couldn&apos;t find that page</h5>
          <p>The chef may no longer be on Karamu, or the link may be wrong.</p>
          <Link href="/marketplace" className="btn-red"><i className="fas fa-store"></i>Browse the Marketplace</Link>
        </div>
      </div>
    </section>
  );
}
