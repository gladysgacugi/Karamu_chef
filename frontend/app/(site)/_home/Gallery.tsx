"use client";

// "Food Made With Love": clicking a photo opens it in a popup with prev/next.
import { useEffect, useState } from "react";

const ITEMS = [
  { img: "work1.jpg", title: "Nyama Choma Nights", alt: "Nyama Choma", desc: "Charcoal-grilled goat and beef, prepared on site by our grill chefs for birthdays and weekend get-togethers." },
  { img: "work2.jpg", title: "Swahili Coastal Feasts", alt: "Swahili food", desc: "Biryani, pilau, samaki wa kupaka and viazi karai - the flavours of the Kenyan coast, cooked fresh in Nairobi." },
  { img: "work3.jpg", title: "Private Dinners at Home", alt: "Private dinner", desc: "Intimate dinners for couples and families, with a chef who plans the menu, cooks and cleans up after." },
  { img: "work4.jpg", title: "Events & Celebrations", alt: "Events catering", desc: "From ruracio and weddings to office parties, our chefs cater events of every size." },
  { img: "work5.jpg", title: "Weekly Meal Prep", alt: "Meal prep", desc: "Healthy, home-cooked meals prepared for the whole week, so your family eats well even on busy days." },
];

const src = (img: string) => `/static/img/portfolio/${img}`;

export default function Gallery() {
  const [open, setOpen] = useState<number | null>(null);
  const item = ITEMS[open ?? 0];
  const step = (by: number) => setOpen((i) => ((i ?? 0) + by + ITEMS.length) % ITEMS.length);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(null);
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    document.body.style.overflow = open === null ? "" : "hidden";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <>
      <div className="ggrid" data-aos="fade-up">
        {ITEMS.map((g, i) => (
          <div key={g.img} className="gitem" onClick={() => setOpen(i)}>
            <img src={src(g.img)} alt={g.alt} />
            <div className="gover"><span><i className="fas fa-expand-alt"></i> {g.title}</span></div>
          </div>
        ))}
      </div>
      <div id="galPop" className={open === null ? "" : "open"} onClick={(e) => e.target === e.currentTarget && setOpen(null)}>
        <div className="gpbox">
          <button className="gpclose" onClick={() => setOpen(null)}><i className="fas fa-times"></i></button>
          {open !== null && <img src={src(item.img)} alt="" />}
          <div className="gpcap">
            <h5>{open !== null && item.title}</h5>
            <p>{open !== null && item.desc}</p>
          </div>
          <div className="gpnav">
            <button onClick={() => step(-1)}><i className="fas fa-chevron-left me-1"></i>Prev</button>
            <button onClick={() => step(1)}>Next <i className="fas fa-chevron-right ms-1"></i></button>
          </div>
        </div>
      </div>
    </>
  );
}
