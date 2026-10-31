// A booking's date, guests, place, package and price, as the chef sees them. The phone number shows once confirmed.
import type { ChefBooking } from "@/lib/api";
import { pluralize, price, timesince, weekdayDate } from "@/lib/format";

export default function BookingMeta({ booking, className = "bkmeta" }: { booking: ChefBooking; className?: string }) {
  return (
    <>
      <div className={className}>
        <span><i className="fas fa-calendar"></i>{weekdayDate(booking.event_date)}, {booking.time_slot_display}</span>
        <span><i className="fas fa-users"></i>{booking.guests} guest{pluralize(booking.guests)}</span>
        <span><i className="fas fa-map-marker-alt"></i>{booking.location}</span>
        <span><i className="fas fa-utensils"></i>{booking.package?.name ?? "Custom request"}</span>
        {booking.price ? <span><i className="fas fa-money-bill-wave"></i>KSh {price(booking.price)}</span> : null}
        {booking.phone && <span><i className="fas fa-phone-alt"></i>{booking.phone}</span>}
      </div>
      {booking.notes && <p className="bknotes"><strong>Requests:</strong> {booking.notes}</p>}
      <small className="bkwhen">Requested {timesince(booking.created_at)} ago</small>
    </>
  );
}

/** The booking's status, and its payment once there is a price to pay. */
export function BookingStatus({ booking }: { booking: ChefBooking }) {
  return (
    <>
      <span className={`bkstatus bk-${booking.status}`}>{booking.status_display}</span>
      {booking.price && booking.status !== "new" ? <span className={`bkstatus pay-${booking.payment_status}`}>{booking.payment_status_display}</span> : null}
    </>
  );
}
