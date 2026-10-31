// One booking: details, status and payment buttons, messages, review, and the price and team notes (Django: team/booking.html).
import type { Metadata } from "next";
import Link from "next/link";
import BookingMessages from "@/components/BookingMessages";
import DjangoForm from "@/components/DjangoForm";
import { getTeamPage, type BookingMessage, type FormInfo, type TeamBooking, type TeamReview } from "@/lib/api";
import { chefUrl, dayMonthTime, dayMonthYearTime, price, weekdayDate, weekdayDayMonth } from "@/lib/format";
import BookingActions, { whatsappCustomer } from "../../BookingActions";
import { Stars } from "../../StatusTabs";

type BookingPage = FormInfo & { booking: TeamBooking; messages: BookingMessage[]; review: TeamReview | null; clash: boolean };

const getBookingPage = (id: string) => getTeamPage<BookingPage>(`bookings/${encodeURIComponent(id)}/`);

export async function generateMetadata({ params }: PageProps<"/team/bookings/[id]">): Promise<Metadata> {
  return { title: `Booking ${(await getBookingPage((await params).id)).booking.payment_reference}` };
}

export default async function TeamBookingPage({ params }: PageProps<"/team/bookings/[id]">) {
  const { booking, messages, review, clash, fields } = await getBookingPage((await params).id);
  const pkg = booking.package;

  return (
    <>
      <Link href="/team/bookings/" className="dbback"><i className="fas fa-arrow-left me-1"></i>Bookings</Link>
      <h1 className="tmtitle">{booking.full_name}<small>Booking {booking.payment_reference} &middot; requested {dayMonthYearTime(booking.created_at)}</small></h1>

      <div className="tmrow mt-0 mb-3">
        <a className="bkbtn bkbtn-wa" href={whatsappCustomer(booking)} target="_blank" rel="noopener"><i className="fab fa-whatsapp"></i>WhatsApp</a>
        <a className="bkbtn bkbtn-plain" href={`tel:${booking.phone}`}><i className="fas fa-phone-alt"></i>Call</a>
        {booking.email && <a className="bkbtn bkbtn-plain" href={`mailto:${booking.email}`}><i className="fas fa-envelope"></i>Email</a>}
      </div>

      {clash && (
        <div className="tmcard tmalert"><i className="fas fa-exclamation-triangle me-2"></i>{booking.chef.name} already has a confirmed booking at this time. Find another chef or ask the customer to change the time.</div>
      )}

      <div className="tmcard">
        <div className="bktop">
          <span className="bkname">{weekdayDate(booking.event_date)} &middot; {booking.time_slot_display}</span>
          <span className={`bkstatus bk-${booking.status}`}>{booking.status_display}</span>
        </div>
        <dl className="tmdl">
          <dt>Chef</dt><dd><a href={chefUrl(booking.chef.slug)} target="_blank" rel="noopener">{booking.chef.name}</a></dd>
          <dt>Package</dt><dd>{pkg ? `${pkg.name} (KSh ${price(pkg.price)} ${pkg.price_unit})` : "Custom request"}</dd>
          <dt>Guests</dt><dd>{booking.guests}</dd>
          <dt>Location</dt><dd>{booking.location}</dd>
          <dt>Phone</dt><dd>{booking.phone}</dd>
          <dt>Email</dt><dd>{booking.email || "-"}</dd>
          <dt>Account</dt><dd>{booking.customer_email ?? "Booked as a guest"}</dd>
          {booking.notes && <><dt>Requests</dt><dd>{booking.notes}</dd></>}
          {booking.reminder_sent_at && <><dt>Reminder</dt><dd>Sent {dayMonthTime(booking.reminder_sent_at)}</dd></>}
        </dl>
        <BookingActions booking={booking} />
      </div>

      <div className="tmcard">
        <div className="bktop">
          <h2 className="tmsub mb-0">Payment</h2>
          <span className={`bkstatus pay-${booking.payment_status}`}>{booking.payment_status_display}</span>
        </div>
        <dl className="tmdl">
          <dt>Price</dt><dd>{booking.price ? `KSh ${price(booking.price)}` : "Not set - it is set when the booking is confirmed"}</dd>
          <dt>Account number</dt><dd>{booking.payment_reference}</dd>
          <dt>M-Pesa code</dt><dd>{booking.mpesa_code || "-"}</dd>
          {booking.paid_at && <><dt>Paid</dt><dd>{dayMonthYearTime(booking.paid_at)}</dd></>}
        </dl>
        {booking.payment_status === "submitted" && booking.price && (
          <p className="tmnote">Search the M-Pesa statement for <strong>{booking.mpesa_code}</strong> and check the amount is KSh {price(booking.price)}.</p>
        )}
      </div>

      {messages.length > 0 && (
        <div className="tmcard">
          <h2 className="tmsub">Messages between chef and customer</h2>
          <BookingMessages messages={messages} chefName={booking.chef.name} customerName={booking.full_name} viewer="team" />
        </div>
      )}

      {review && (
        <div className="tmcard">
          <div className="bktop">
            <h2 className="tmsub mb-0">Review</h2>
            <Stars rating={review.rating} />
            <span className={`bkstatus rv-${review.status}`}>{review.status_display}</span>
          </div>
          <p className="bknotes">{review.comment}</p>
          <Link href={`/team/reviews/?status=${review.status}`} className="tmnote">Moderate reviews</Link>
        </div>
      )}

      <div className="tmcard">
        <h2 className="tmsub">Edit</h2>
        <DjangoForm
          action={`/api/team/bookings/${booking.id}/`}
          fields={fields}
          variant="stacked"
          icon="fa-save"
          button="Save"
          buttonClass="bkbtn w-auto mt-3"
        />
        <p className="tmnote">Changing the price here does not email anyone. Let the customer know on WhatsApp. <a href={`/admin/SimplyChefKe/bookingrequest/${booking.id}/change/`}>Full admin</a> for anything else.</p>
      </div>
    </>
  );
}
