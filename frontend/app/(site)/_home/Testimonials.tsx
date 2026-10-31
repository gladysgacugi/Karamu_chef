"use client";

// Published 4- and 5-star reviews in a Swiper slider, using the same swiper-bundle.min.js as the Django site.
import Link from "next/link";
import Script from "next/script";
import { useRef } from "react";
import type { Review } from "@/lib/api";
import { chefUrl, monthYear, truncate } from "@/lib/format";

declare global {
  interface Window {
    Swiper?: new (el: HTMLElement, options: object) => { destroy: () => void };
  }
}

export default function Testimonials({ reviews }: { reviews: Review[] }) {
  const el = useRef<HTMLDivElement>(null);
  const swiper = useRef<{ destroy: () => void }>(null);

  function start() {
    if (!el.current || !window.Swiper) return;
    swiper.current?.destroy();
    swiper.current = new window.Swiper(el.current, {
      slidesPerView: 1,
      spaceBetween: 22,
      loop: reviews.length > 3,
      autoplay: { delay: 4000, disableOnInteraction: false },
      pagination: { el: el.current.querySelector(".swiper-pagination"), clickable: true },
      breakpoints: { 640: { slidesPerView: 2 }, 1024: { slidesPerView: 3 } },
    });
  }

  return (
    <div ref={el} className="swiper tesSwiper" data-aos="fade-up">
      <div className="swiper-wrapper">
        {reviews.map((review) => (
          <div key={review.id} className="swiper-slide">
            <div className="tescard">
              <div className="tesq">&quot;</div>
              <div className="tess">{[1, 2, 3, 4, 5].map((n) => <i key={n} className={`${n <= review.rating ? "fas" : "far"} fa-star`}></i>)}</div>
              <p className="testxt">{truncate(review.comment, 260)}</p>
              <div className="tesauth">
                <div className="tesav">{review.customer_name.charAt(0).toUpperCase()}</div>
                <div>
                  <div className="tesnm">{review.customer_name}</div>
                  <div className="tesrl">Booked <Link href={chefUrl(review.chef.slug)}>{review.chef.name}</Link> &middot; {monthYear(review.created_at)}</div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="swiper-pagination mt-4" style={{ position: "static" }}></div>
      <Script src="/static/js/swiper-bundle.min.js" onReady={start} />
    </div>
  );
}
