// How to pay for a confirmed booking by M-Pesa, and where the customer sends us their M-Pesa code (Django: booking_checkout.html).
import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import DjangoForm from "@/components/DjangoForm";
import WhatsAppFloat from "@/components/WhatsAppFloat";
import { getBooking, getForm, getSite } from "@/lib/api";
import { bookingUrl, keyQuery, pluralize, price, weekdayDate } from "@/lib/format";

export const metadata: Metadata = { title: "Pay for your booking - Karamu" };

export default async function BookingCheckout({ params, searchParams }: PageProps<"/bookings/[id]/pay">) {
  const { id } = await params;
  const { key } = await searchParams;
  const [booking, form, site] = await Promise.all([getBooking(id, key), getForm(`bookings/${id}/pay/`, { key }), getSite()]);
  if (!booking.customer_can_pay || !booking.price) redirect(bookingUrl(booking.id, "", key));

  return (
    <>
      <section className="acwrap">
        <div className="container">
          <div className="fcard bkconf">
            <Link href={bookingUrl(booking.id, "", key)} className="dbback"><i className="fas fa-arrow-left me-1"></i>Back to your booking</Link>
            <span className="slbl d-block">Booking {booking.payment_reference}</span>
            <h1 className="actitle">Pay with <span>M-Pesa</span></h1>

            <div className="paybox">
              <div className="payrow"><span>{booking.chef.name} &middot; {booking.package?.name ?? "Custom request"}</span></div>
              <div className="payrow"><span>{weekdayDate(booking.event_date)}, {booking.time_slot_display} &middot; {booking.guests} guest{pluralize(booking.guests)}</span></div>
              <div className="payrow paytotal"><span>Amount to pay</span><strong>KSh {price(booking.price)}</strong></div>
            </div>

            <h4 className="bkconfhd">1. Send the money</h4>
            {site.mpesa_paybill ? (
              <ol className="paysteps">
                <li>Open <strong>M-Pesa</strong> and choose <strong>Lipa na M-Pesa &rsaquo; Pay Bill</strong></li>
                <li>Business number: <strong className="paycode">{site.mpesa_paybill}</strong></li>
                <li>Account number: <strong className="paycode">{booking.payment_reference}</strong></li>
                <li>Amount: <strong>KSh {price(booking.price)}</strong></li>
                <li>Check the business name is <strong>Karamu</strong>, then enter your PIN</li>
              </ol>
            ) : (
              <p className="acsub">WhatsApp us on <a href={site.whatsapp_url} target="_blank" rel="noopener">{site.whatsapp_display}</a> with your booking reference <strong>{booking.payment_reference}</strong> and we&apos;ll send you the M-Pesa payment details.</p>
            )}
            <p className="paynote"><i className="fas fa-shield-alt"></i>Only pay to the details on this page. Karamu will never ask you to send money to a personal number.</p>

            <h4 className="bkconfhd">2. Enter your M-Pesa code</h4>
            <p className="acsub">You&apos;ll get an SMS from M-Pesa starting with a code like <strong>SJK4H7L2QP</strong>. Enter it here so we can match your payment.</p>
            <DjangoForm
              action={`/api/bookings/${booking.id}/pay/${keyQuery(key)}`}
              fields={form.fields}
              variant="stacked"
              showHelp={false}
              icon="fa-check"
              button="I've paid - send my code"
              buttonClass="btn-red w-100 justify-content-center mt-3"
            />
          </div>
        </div>
      </section>

      <WhatsAppFloat text={`Hi Karamu, I need help paying for booking ${booking.payment_reference} with ${booking.chef.name}.`} />
    </>
  );
}
