// Bookings by status, or the M-Pesa payments to check with ?payment=submitted (Django: team/bookings.html).
import type { Metadata } from "next";
import Link from "next/link";
import { getTeamPage, type TeamBooking, type TeamList, type Waiting } from "@/lib/api";
import { pluralize, price, timesince, weekdayDate } from "@/lib/format";
import BookingActions, { whatsappCustomer } from "../BookingActions";
import StatusTabs from "../StatusTabs";

export const metadata: Metadata = { title: "Bookings" };

export default async function TeamBookings({ searchParams }: PageProps<"/team/bookings">) {
  const { status, payment } = await searchParams;
  const [list, waiting] = await Promise.all([
    getTeamPage<TeamList<TeamBooking> & { checking_payments: boolean }>("bookings/", { status, payment }),
    getTeamPage<Waiting>("waiting/"),
  ]);

  return (
    <>
      {list.checking_payments ? (
        <>
          <h1 className="tmtitle">Payments to check<small>Find each M-Pesa code on the statement, then mark it paid or not found</small></h1>
          <Link href="/team/bookings/" className="dbback"><i className="fas fa-arrow-left me-1"></i>All bookings</Link>
        </>
      ) : (
        <>
          <h1 className="tmtitle">Bookings<small>Confirming here emails the customer and the chef</small></h1>
          {waiting.payments > 0 && (
            <Link href="/team/bookings/?payment=submitted&status=" className="tmcard tmalert"><i className="fas fa-mobile-alt me-2"></i><strong>{waiting.payments}</strong> M-Pesa payment{pluralize(waiting.payments)} to check</Link>
          )}
          <StatusTabs path="/team/bookings/" tabs={list} />
        </>
      )}

      {list.items.map((booking) => (
        <div key={booking.id} className="tmcard">
          <div className="bktop">
            <Link href={`/team/bookings/${booking.id}/`} className="bkname">{booking.full_name} <i className="fas fa-chevron-right"></i></Link>
            <span className={`bkstatus bk-${booking.status}`}>{booking.status_display}</span>
            {booking.price ? <span className={`bkstatus pay-${booking.payment_status}`}>{booking.payment_status_display}</span> : null}
          </div>
          <div className="bkmeta">
            <span><i className="fas fa-utensils"></i>{booking.chef.name} &middot; {booking.package?.name ?? "Custom request"}</span>
            <span><i className="fas fa-calendar"></i>{weekdayDate(booking.event_date)}, {booking.time_slot_display}</span>
            <span><i className="fas fa-users"></i>{booking.guests} guest{pluralize(booking.guests)}</span>
            <span><i className="fas fa-map-marker-alt"></i>{booking.location}</span>
            <span><i className="fas fa-phone-alt"></i>{booking.phone}</span>
            {booking.price ? <span><i className="fas fa-money-bill-wave"></i>KSh {price(booking.price)} &middot; {booking.payment_reference}</span> : null}
            {booking.mpesa_code && <span><i className="fas fa-receipt"></i>M-Pesa {booking.mpesa_code}</span>}
          </div>
          {booking.notes && <p className="bknotes"><strong>Requests:</strong> {booking.notes}</p>}
          <small className="bkwhen">Requested {timesince(booking.created_at)} ago{!booking.email && <> &middot; no email given, contact them on WhatsApp</>}</small>
          <div className="tmrow">
            <a className="bkbtn bkbtn-wa" href={whatsappCustomer(booking)} target="_blank" rel="noopener"><i className="fab fa-whatsapp"></i>WhatsApp</a>
            <a className="bkbtn bkbtn-plain" href={`tel:${booking.phone}`}><i className="fas fa-phone-alt"></i>Call</a>
          </div>
          <BookingActions booking={booking} />
        </div>
      ))}
      {list.items.length === 0 && (
        <div className="mkempty"><i className="fas fa-calendar"></i><p>{list.checking_payments ? "No payments waiting to be checked." : list.status === "new" ? "All caught up - no new bookings." : "Nothing here."}</p></div>
      )}
    </>
  );
}
