// The chef's booking requests, by status (Django: chef/dashboard.html).
import type { Metadata } from "next";
import Link from "next/link";
import Flash from "@/components/Flash";
import { getChefPage, type ChefBooking, type ChefPage, type StatusTabs } from "@/lib/api";
import { chefUrl } from "@/lib/format";
import BookingActions from "./BookingActions";
import BookingMeta, { BookingStatus } from "./BookingMeta";

export const metadata: Metadata = { title: "Chef dashboard - Karamu" };

export default async function ChefDashboard({ searchParams }: PageProps<"/chef">) {
  const { status: wanted } = await searchParams;
  const { chef, bookings, status, status_tabs, total } = await getChefPage<ChefPage & StatusTabs & { bookings: ChefBooking[] }>("", { status: wanted });

  return (
    <>
      <section className="mkhero dbhero">
        <div className="container">
          <div className="dbhead">
            <img src={chef.photo} alt={chef.name} className="bkphoto" />
            <div>
              <span className="slbl">Chef dashboard</span>
              <h1 className="stitle">{chef.name}</h1>
              <div className="dblinks">
                <Link href="/chef/profile/"><i className="fas fa-user-edit"></i>Profile, menu &amp; prices</Link>
                <Link href="/chef/photos/"><i className="fas fa-images"></i>Food photos</Link>
                <Link href="/chef/documents/"><i className="fas fa-id-card"></i>Documents</Link>
                <Link href="/chef/availability/"><i className="fas fa-calendar-alt"></i>Availability</Link>
                <Link href={chefUrl(chef.slug)}><i className="fas fa-eye"></i>View public profile</Link>
              </div>
            </div>
          </div>
          {!chef.is_active ? (
            <p className="dbnote"><i className="fas fa-eye-slash"></i>Your profile is not live yet. Add a photo, your packages and prices, and our team will publish it.</p>
          ) : !chef.is_accepting_bookings ? (
            <p className="dbnote"><i className="fas fa-pause-circle"></i>New bookings are paused. <Link href="/chef/availability/">Start taking bookings again</Link></p>
          ) : null}
        </div>
      </section>

      <section className="dbmain">
        <div className="container">
          <Flash />

          <div className="mkpills dbtabs">
            <Link href="/chef/" className={status ? "" : "active"}>All <span>{total}</span></Link>
            {status_tabs.map(([value, label, count]) => (
              <Link key={value} href={`/chef/?status=${value}`} className={value === status ? "active" : ""}>{label} <span>{count}</span></Link>
            ))}
          </div>

          {bookings.map((booking) => (
            <div key={booking.id} className="bkcard">
              <div className="bkinfo">
                <div className="bktop">
                  <Link href={`/chef/bookings/${booking.id}/`} className="bkname">{booking.full_name}</Link>
                  <BookingStatus booking={booking} />
                </div>
                <BookingMeta booking={booking} />
              </div>
              <div className="bkactions">
                <BookingActions booking={booking} />
                <Link href={`/chef/bookings/${booking.id}/#messages`} className="bkbtn bkbtn-ghost">
                  <i className="fas fa-comments"></i>{booking.message_count ? `Messages (${booking.message_count})` : "Message customer"}
                </Link>
              </div>
            </div>
          ))}
          {bookings.length === 0 && (
            <div className="mkempty">
              <i className="fas fa-calendar"></i>
              <h5>{status ? `No ${status} bookings` : "No booking requests yet"}</h5>
              <p>A complete profile with a good photo, clear packages and prices gets more bookings.</p>
              <Link href="/chef/profile/" className="btn-red"><i className="fas fa-user-edit"></i>Improve my profile</Link>
            </div>
          )}
        </div>
      </section>
    </>
  );
}
