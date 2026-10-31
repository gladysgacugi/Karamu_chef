// A booking's summary, payment and what happens next (Django: booking_confirmation.html).
// For its customer only: logged in as them, booked in this browser, or opened with the ?key= from their email.
import type { Metadata } from "next";
import Link from "next/link";
import BookingMessages from "@/components/BookingMessages";
import DjangoForm from "@/components/DjangoForm";
import Flash from "@/components/Flash";
import WhatsAppFloat from "@/components/WhatsAppFloat";
import { getBooking, getForm, getMe, getSite } from "@/lib/api";
import { bookingUrl, chefUrl, dayMonth, dayMonthYear, keyQuery, pluralize, price, weekdayDate } from "@/lib/format";

export async function generateMetadata({ params, searchParams }: PageProps<"/bookings/[id]">): Promise<Metadata> {
  const booking = await getBooking((await params).id, (await searchParams).key);
  return { title: `Booking with ${booking.chef.name} - Karamu` };
}

export default async function BookingConfirmation({ params, searchParams }: PageProps<"/bookings/[id]">) {
  const { id } = await params;
  const { key } = await searchParams;
  const [booking, user, site, messageForm] = await Promise.all([
    getBooking(id, key), getMe(), getSite(), getForm(`bookings/${id}/messages/`, { key }),
  ]);
  const whatsappText = `Hi Karamu, about my booking #${booking.id} with ${booking.chef.name} on ${dayMonth(booking.event_date)}.`;
  const pkg = booking.package;

  return (
    <>
      <section className="acwrap">
        <div className="container">
          <div className="fcard bkconf">
            <Flash />
            {booking.status === "new" ? (
              <div className="bcdone">
                <i className="fas fa-check-circle"></i>
                <h1 className="actitle">Booking request <span>sent!</span></h1>
                <p>{booking.chef.name} will confirm their availability and the price. We&apos;ll then send you a link to pay by M-Pesa{booking.email && ` at ${booking.email}`}.</p>
              </div>
            ) : (
              <>
                <span className="slbl">Booking #{booking.id}</span>
                <h1 className="actitle">Your booking with <span>{booking.chef.name}</span></h1>
              </>
            )}

            <div className="bkcard mt-4 mb-0">
              <img src={booking.chef.photo} alt={booking.chef.name} className="bkphoto" />
              <div className="bkinfo">
                <div className="bktop">
                  <Link href={chefUrl(booking.chef.slug)} className="bkname">{booking.chef.name}</Link>
                  <span className={`bkstatus bk-${booking.status}`}>{booking.status_display}</span>
                </div>
                <div className="bkmeta">
                  <span><i className="fas fa-hashtag"></i>Booking {booking.id}</span>
                  <span><i className="fas fa-calendar"></i>{weekdayDate(booking.event_date)}, {booking.time_slot_display}</span>
                  <span><i className="fas fa-users"></i>{booking.guests} guest{pluralize(booking.guests)}</span>
                  <span><i className="fas fa-map-marker-alt"></i>{booking.location}</span>
                  <span><i className="fas fa-utensils"></i>{pkg ? `${pkg.name} (KSh ${price(pkg.price)} ${pkg.price_unit})` : "Custom request"}</span>
                </div>
                {booking.notes && <p className="bknotes">{booking.notes}</p>}
              </div>
            </div>

            {booking.price ? (
              <div className="paybox">
                <div className="payrow"><span>Agreed price</span><strong>KSh {price(booking.price)}</strong></div>
                <div className="payrow"><span>Payment</span><span className={`bkstatus pay-${booking.payment_status}`}>{booking.payment_status_display}</span></div>
                {booking.customer_can_pay ? (
                  <Link href={bookingUrl(booking.id, "pay/", key)} className="btn-red w-100 justify-content-center mt-3"><i className="fas fa-mobile-alt"></i>Pay KSh {price(booking.price)} with M-Pesa</Link>
                ) : booking.payment_status === "submitted" ? (
                  <p className="paynote"><i className="fas fa-hourglass-half"></i>We&apos;re checking your M-Pesa payment ({booking.mpesa_code}). We&apos;ll email you once it&apos;s confirmed, usually within a few hours.</p>
                ) : booking.payment_status === "paid" ? (
                  <p className="paynote"><i className="fas fa-check-circle"></i>Paid{booking.paid_at && ` on ${dayMonthYear(booking.paid_at)}`}{booking.mpesa_code && <> &middot; M-Pesa {booking.mpesa_code}</>}. Thank you!</p>
                ) : booking.payment_status === "refunded" ? (
                  <p className="paynote"><i className="fas fa-undo"></i>Your payment was refunded to {booking.phone}.</p>
                ) : null}
              </div>
            ) : null}

            {booking.status === "new" || booking.status === "confirmed" ? (
              <>
                <h4 className="bkconfhd">What happens next</h4>
                <ol className="bcsteps">
                  <li className={booking.status === "confirmed" ? "done" : ""}><strong>{booking.chef.name} confirms</strong>The chef checks they&apos;re free on {dayMonth(booking.event_date)} and sets the price. If they can&apos;t make it, we&apos;ll help you find another chef.</li>
                  <li className={booking.payment_status === "paid" ? "done" : ""}><strong>You pay via M-Pesa</strong>We email you a payment link once the chef confirms. Nothing is charged before that.</li>
                  <li><strong>Enjoy your meal</strong>Your chef arrives at {booking.location} for {booking.time_slot_display.toLowerCase()}. We&apos;ll remind you the day before.</li>
                </ol>
              </>
            ) : booking.can_be_reviewed ? (
              <div className="rvform">
                <h6>How was the food?</h6>
                <p className="acsub">Your review helps other customers and helps {booking.chef.name} get more bookings.</p>
                <Link href={bookingUrl(booking.id, "review/", key)} className="btn-red"><i className="fas fa-star"></i>Review {booking.chef.name}</Link>
              </div>
            ) : booking.review_status ? (
              <p className="paynote mt-3"><i className="fas fa-star"></i>Thanks for reviewing {booking.chef.name}{booking.review_status === "pending" && ". It will appear on their profile once our team has checked it"}.</p>
            ) : null}

            <h4 className="bkconfhd">Messages with {booking.chef.name}</h4>
            <BookingMessages messages={booking.messages} chefName={booking.chef.name} customerName={booking.full_name} viewer="customer" />
            <div className="msgform">
              <DjangoForm
                action={`/api/bookings/${booking.id}/messages/${keyQuery(key)}`}
                fields={messageForm.fields}
                variant="stacked"
                showHelp={false}
                idPrefix="msg_"
                icon="fa-paper-plane"
                button="Send"
                buttonClass="bkbtn w-auto mt-2"
              />
            </div>

            <div className="bkconfbtns">
              {booking.is_owner ? (
                <Link href="/account/" className="btn-red"><i className="fas fa-receipt"></i>My bookings</Link>
              ) : (
                <Link href="/marketplace/" className="btn-red"><i className="fas fa-store"></i>Back to the marketplace</Link>
              )}
              <a href={`${site.whatsapp_url}?text=${encodeURIComponent(whatsappText)}`} target="_blank" rel="noopener" className="bkbtn bkbtn-ghost"><i className="fab fa-whatsapp"></i>Questions? WhatsApp us</a>
            </div>
            {!user && (
              <p className="acfoot">We&apos;ll keep you updated by SMS and email. <Link href="/account/signup/">Create an account</Link> to track future bookings in one place.</p>
            )}
          </div>
        </div>
      </section>

      <WhatsAppFloat text={whatsappText} />
    </>
  );
}
