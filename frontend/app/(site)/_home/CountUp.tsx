"use client";

// A hero stat that counts up from 0 once the visitor scrolls past the hero, as main.js does.
import { useEffect, useState } from "react";

export default function CountUp({ value }: { value: number }) {
  const [shown, setShown] = useState(value);

  useEffect(() => {
    let timer: ReturnType<typeof setInterval> | undefined;
    function onScroll() {
      const hero = document.getElementById("hero");
      if (!hero || window.scrollY <= hero.offsetHeight - 300) return;
      window.removeEventListener("scroll", onScroll);
      const step = Math.ceil(value / 55);
      let n = 0;
      timer = setInterval(() => {
        n = Math.min(n + step, value);
        setShown(n);
        if (n >= value) clearInterval(timer);
      }, 1400 / 55);
    }
    window.addEventListener("scroll", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      clearInterval(timer);
    };
  }, [value]);

  return <span className="snum">{shown}</span>;
}
