// What needs the team today (Django: team/home.html).
import type { Metadata } from "next";
import Link from "next/link";
import { getTeamPage, type TeamBooking, type Waiting } from "@/lib/api";
import { pluralize, weekdayDayMonth } from "@/lib/format";

// The layout's "%s - Karamu" only applies to the pages below it
export const metadata: Metadata = { title: "Today - Karamu" };

type Home = { first_name: string; waiting: Waiting; upcoming: TeamBooking[]; chefs_waiting_to_go_live: number };

export default async function TeamHome() {
  const { first_name, waiting, upcoming, chefs_waiting_to_go_live: notLive } = await getTeamPage<Home>("");
  const tiles: [string, string, number, string][] = [
    ["/team/applications/", "fa-user-check", waiting.applications, `Chef application${pluralize(waiting.applications)} to review`],
    ["/team/bookings/", "fa-calendar-check", waiting.bookings, `New booking${pluralize(waiting.bookings)}`],
    ["/team/bookings/?payment=submitted&status=", "fa-mobile-alt", waiting.payments, `M-Pesa payment${pluralize(waiting.payments)} to check`],
    ["/team/reviews/", "fa-star", waiting.reviews, `Review${pluralize(waiting.reviews)} to check`],
    ["/team/requests/", "fa-concierge-bell", waiting.requests, `Find-a-chef request${pluralize(waiting.requests)}`],
    ["/team/inbox/", "fa-envelope", waiting.inbox, `Message${pluralize(waiting.inbox)} to reply to`],
  ];

  return (
    <>
      <h1 className="tmtitle">Hi {first_name}<small>Here&apos;s what needs you today</small></h1>

      <div className="tmtiles">
        {tiles.map(([href, icon, count, label]) => (
          <Link key={href} href={href} className={`tmtile${count ? " hot" : ""}`}>
            <i className={`fas ${icon}`}></i><strong>{count}</strong><span>{label}</span>
          </Link>
        ))}
      </div>

      {notLive > 0 && (
        <Link href="/team/chefs/?show=hidden" className="tmcard">
          <i className="fas fa-eye-slash me-2" style={{ color: "var(--secondary)" }}></i><strong>{notLive}</strong> chef profile{pluralize(notLive)} not live yet
          <p className="tmnote">Check their profile has a photo, packages and prices, then put it live.</p>
        </Link>
      )}

      <h2 className="tmsub">Coming up this week</h2>
      {upcoming.map((booking) => (
        <Link key={booking.id} href={`/team/bookings/${booking.id}/`} className="tmcard">
          <div className="bktop">
            <span className="bkname">{weekdayDayMonth(booking.event_date)} &middot; {booking.time_slot_display}</span>
            <span className={`bkstatus pay-${booking.payment_status}`}>{booking.payment_status_display}</span>
          </div>
          <div className="bkmeta">
            <span><i className="fas fa-user"></i>{booking.full_name}</span>
            <span><i className="fas fa-utensils"></i>{booking.chef.name}</span>
            <span><i className="fas fa-users"></i>{booking.guests} guest{pluralize(booking.guests)}</span>
            <span><i className="fas fa-map-marker-alt"></i>{booking.location}</span>
          </div>
        </Link>
      ))}
      {upcoming.length === 0 && <div className="mkempty"><i className="fas fa-calendar"></i><p>No confirmed bookings in the next 7 days.</p></div>}
    </>
  );
}
