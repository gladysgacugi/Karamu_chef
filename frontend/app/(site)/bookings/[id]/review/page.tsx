// Customers review a chef from their completed booking, so every review is from a real booking (Django: booking_review.html).
import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import DjangoForm from "@/components/DjangoForm";
import WhatsAppFloat from "@/components/WhatsAppFloat";
import { getBooking, getForm } from "@/lib/api";
import { bookingUrl, keyQuery, weekdayDate } from "@/lib/format";

export async function generateMetadata({ params, searchParams }: PageProps<"/bookings/[id]/review">): Promise<Metadata> {
  const booking = await getBooking((await params).id, (await searchParams).key);
  return { title: `Review ${booking.chef.name} - Karamu` };
}

export default async function BookingReview({ params, searchParams }: PageProps<"/bookings/[id]/review">) {
  const { id } = await params;
  const { key } = await searchParams;
  const [booking, form] = await Promise.all([getBooking(id, key), getForm(`bookings/${id}/review/`, { key })]);
  const tooEarly = booking.status !== "completed";
  if (!booking.can_be_reviewed && !tooEarly) redirect(bookingUrl(booking.id, "", key)); // already reviewed

  return (
    <>
      <section className="acwrap">
        <div className="container">
          <div className="fcard bkconf">
            <Link href={bookingUrl(booking.id, "", key)} className="dbback"><i className="fas fa-arrow-left me-1"></i>Back to your booking</Link>
            <div className="bkchef mt-2">
              <img src={booking.chef.photo} alt={booking.chef.name} className="bkphoto" />
              <div>
                <h1 className="actitle mb-0">Review <span>{booking.chef.name}</span></h1>
                <div className="bkmeta"><span><i className="fas fa-calendar"></i>{weekdayDate(booking.event_date)} &middot; {booking.package?.name ?? "Custom request"}</span></div>
              </div>
            </div>
            {tooEarly ? (
              <div className="acmsg acmsg-err mt-3"><i className="fas fa-exclamation-circle"></i>You can review your chef once the booking is completed.</div>
            ) : (
              <>
                <p className="acsub mt-3">Be honest and specific: the food, how it was served, timekeeping and clean-up. Our team checks every review before it goes on the profile.</p>
                <DjangoForm
                  action={`/api/bookings/${booking.id}/review/${keyQuery(key)}`}
                  fields={form.fields}
                  wide={["comment"]}
                  stars={false}
                  helpFor={{ customer_name: "Shown with your review. Your first name is enough." }}
                  icon="fa-star"
                  button="Submit review"
                  buttonClass="btn-red"
                />
              </>
            )}
          </div>
        </div>
      </section>

      <WhatsAppFloat />
    </>
  );
}
