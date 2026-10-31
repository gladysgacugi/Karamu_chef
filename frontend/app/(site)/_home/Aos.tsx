"use client";

// AOS scroll animations for the homepage's [data-aos] sections. AOS adds classes to those sections, so it loads
// here rather than in the layout: this only runs once React has hydrated the page, which would fail on the changed classes.
import Script from "next/script";

declare global {
  interface Window {
    AOS?: { init: (options: object) => void; refreshHard: () => void };
  }
}

let started = false;

// Coming back to the homepage brings new [data-aos] elements, but AOS should only be set up once
function start() {
  if (!window.AOS) return;
  if (started) window.AOS.refreshHard();
  else window.AOS.init({ duration: 680, once: true, offset: 55 });
  started = true;
}

export default function Aos() {
  return <Script src="/static/js/aos.js" onReady={start} />;
}
