import Link from "next/link";
import type { ChefCard as Chef } from "@/lib/api";
import { chefUrl, price, rating } from "@/lib/format";

export default function ChefCard({ chef }: { chef: Chef }) {
  return (
    <Link href={chefUrl(chef.slug)} className="mkcard">
      <div className="mkimg">
        <img src={chef.photo} alt={chef.name} loading="lazy" />
        {chef.is_verified && <span className="mkbadge"><i className="fas fa-check-circle"></i> Verified</span>}
      </div>
      <div className="mkbody">
        <div className="mkrow">
          <div className="mknm">{chef.name}</div>
          <div className="mkrate">
            {chef.review_count ? (
              <><i className="fas fa-star"></i> {rating(chef.avg_rating)} <span>({chef.review_count})</span></>
            ) : (
              <span className="mknew">New</span>
            )}
          </div>
        </div>
        <div className="mkhead">{chef.headline}</div>
        <div className="mkloc"><i className="fas fa-map-marker-alt"></i>{chef.area && `${chef.area}, `}{chef.city.name}</div>
        <div className="mktags">{chef.services.slice(0, 2).map((s) => <span key={s.slug}>{s.name}</span>)}</div>
        <div className="mkfoot">
          <div className="mkprice">From <strong>KSh {price(chef.starting_price)}</strong> <small>{chef.price_unit}</small></div>
          <span className="mkview">View <i className="fas fa-arrow-right"></i></span>
        </div>
      </div>
    </Link>
  );
}
