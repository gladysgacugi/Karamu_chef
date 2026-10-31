"use client";

// The team's bottom menu, with badges for what is waiting (Django: team/base.html).
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Waiting } from "@/lib/api";

/** The menu for the current page. */
export default function CurrentTeamNav({ waiting }: { waiting: Waiting | null }) {
  return <TeamNav waiting={waiting} pathname={usePathname()} />;
}

const Badge = ({ n }: { n: number | null | undefined }) => (n ? <span className="tmbadge">{n}</span> : null);

/** The page is only known at request time, so the prerendered shell shows the menu with nothing active and no badges. */
export function TeamNav({ waiting, pathname }: { waiting: Waiting | null; pathname: string | null }) {
  const on = (...prefixes: string[]) => (pathname && prefixes.some((p) => pathname.startsWith(p)) ? "active" : "");
  return (
    <nav className="tmnav">
      <Link href="/team/" className={pathname === "/team/" || pathname === "/team" ? "active" : on("/team/reviews")}>
        <i className="fas fa-home"></i>Home<Badge n={waiting?.reviews} />
      </Link>
      <Link href="/team/applications/" className={on("/team/applications", "/team/chefs")}>
        <i className="fas fa-user-check"></i>Chefs<Badge n={waiting?.applications} />
      </Link>
      <Link href="/team/bookings/" className={on("/team/bookings")}>
        <i className="fas fa-calendar-check"></i>Bookings<Badge n={waiting && waiting.bookings + waiting.payments} />
      </Link>
      <Link href="/team/requests/" className={on("/team/requests")}>
        <i className="fas fa-concierge-bell"></i>Requests<Badge n={waiting?.requests} />
      </Link>
      <Link href="/team/inbox/" className={on("/team/inbox")}>
        <i className="fas fa-envelope"></i>Inbox<Badge n={waiting?.inbox} />
      </Link>
    </nav>
  );
}
