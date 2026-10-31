// The logged-in customer's bookings (Django: accounts/account.html).
import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import Flash from "@/components/Flash";
import WhatsAppFloat from "@/components/WhatsAppFloat";
import { getAccount, getSite } from "@/lib/api";
import { bookingUrl, chefUrl, dayMonth, pluralize, price, weekdayDate } from "@/lib/format";
import CancelButton from "./CancelButton";

export const metadata: Metadata = { title: "My bookings - Karamu" };

export default async function Account() {
  const [account, site] = await Promise.all([getAccount(), getSite()]);
  if (!account) redirect(`/account/login/?next=${encodeURIComponent("/account/")}`);
  const { user, bookings } = account;

  return (
    <>
      <section className="mkhero dbhero">
        <div className="container">
          <span className="slbl">Hi {user.first_name || "there"}</span>
          <h1 className="stitle">My <span>Bookings</span></h1>
          <p className="sdesc">Every chef you&apos;ve booked while logged in. We&apos;ll email and SMS you as soon as a chef confirms.</p>
          {user.is_chef && <Link href="/chef/" className="btn-red mt-2"><i className="fas fa-calendar-check"></i>Go to your chef dashboard</Link>}
        </div>
      </section>

      <section className="dbmain">
        <div className="container">
          <Flash />
          {bookings.map((booking) => (
            <div key={booking.id} className="bkcard">
              <img src={booking.chef.photo} alt={booking.chef.name} className="bkphoto" />
              <div className="bkinfo">
                <div className="bktop">
                  <Link href={chefUrl(booking.chef.slug)} className="bkname">{booking.chef.name}</Link>
                  <span className={`bkstatus bk-${booking.status}`}>{booking.status_display}</span>
                  {booking.price && booking.status !== "new" && <span className={`bkstatus pay-${booking.payment_status}`}>{booking.payment_status_display}</span>}
                </div>
                <div className="bkmeta">
                  <span><i className="fas fa-calendar"></i>{weekdayDate(booking.event_date)}, {booking.time_slot_display}</span>
                  <span><i className="fas fa-users"></i>{booking.guests} guest{pluralize(booking.guests)}</span>
                  <span><i className="fas fa-map-marker-alt"></i>{booking.location}</span>
                  <span><i className="fas fa-utensils"></i>{booking.package?.name ?? "Custom request"}</span>
                  {booking.price && <span><i className="fas fa-money-bill-wave"></i>KSh {price(booking.price)}</span>}
                </div>
                {booking.notes && <p className="bknotes">{booking.notes}</p>}
              </div>
              <div className="bkactions">
                <Link href={bookingUrl(booking.id)} className="bkbtn bkbtn-ghost"><i className="fas fa-info-circle"></i>Details</Link>
                {booking.customer_can_cancel ? (
                  <CancelButton bookingId={booking.id} />
                ) : booking.can_be_reviewed ? (
                  <Link href={bookingUrl(booking.id, "review/")} className="bkbtn"><i className="fas fa-star"></i>Leave a review</Link>
                ) : booking.customer_can_pay ? (
                  <Link href={bookingUrl(booking.id, "pay/")} className="bkbtn"><i className="fas fa-mobile-alt"></i>Pay now</Link>
                ) : booking.status === "confirmed" ? (
                  <a href={`${site.whatsapp_url}?text=${encodeURIComponent(`Hi Karamu, about my booking with ${booking.chef.name} on ${dayMonth(booking.event_date)}.`)}`} target="_blank" rel="noopener" className="bkbtn bkbtn-ghost"><i className="fab fa-whatsapp"></i>Change booking</a>
                ) : null}
              </div>
            </div>
          ))}
          {bookings.length === 0 && (
            <div className="mkempty">
              <i className="fas fa-receipt"></i>
              <h5>No bookings yet</h5>
              <p>Find a chef for your next family lunch, party or weekly meal prep.</p>
              <Link href="/marketplace/" className="btn-red"><i className="fas fa-search"></i>Find a Chef</Link>
            </div>
          )}
        </div>
      </section>

      <WhatsAppFloat />
    </>
  );
}
