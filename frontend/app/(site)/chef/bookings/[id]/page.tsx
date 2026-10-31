// One booking: its details, confirm/decline, and messages with the customer (Django: chef/booking.html).
import type { Metadata } from "next";
import Link from "next/link";
import BookingMessages from "@/components/BookingMessages";
import DjangoForm from "@/components/DjangoForm";
import Flash from "@/components/Flash";
import { getChefPage, type BookingMessage, type ChefBooking, type ChefFormPage } from "@/lib/api";
import BookingActions from "../../BookingActions";
import BookingMeta, { BookingStatus } from "../../BookingMeta";

type BookingPage = ChefFormPage & { booking: ChefBooking; messages: BookingMessage[] };

const getBookingPage = (id: string) => getChefPage<BookingPage>(`bookings/${encodeURIComponent(id)}/`);

export async function generateMetadata({ params }: PageProps<"/chef/bookings/[id]">): Promise<Metadata> {
  const { booking } = await getBookingPage((await params).id);
  return { title: `Booking for ${booking.full_name} - Karamu` };
}

export default async function ChefBookingPage({ params }: PageProps<"/chef/bookings/[id]">) {
  const { chef, booking, messages, fields } = await getBookingPage((await params).id);
  const firstName = booking.full_name.split(" ")[0];

  return (
    <>
      <section className="mkhero dbhero">
        <div className="container">
          <Link href="/chef/" className="dbback"><i className="fas fa-arrow-left"></i> Back to bookings</Link>
          <span className="slbl">Booking #{booking.id}</span>
          <h1 className="stitle">{booking.full_name}</h1>
        </div>
      </section>

      <section className="dbmain">
        <div className="container">
          <Flash />
          <div className="row g-4">
            <div className="col-lg-5">
              <div className="fcard dbcard">
                <div className="bktop">
                  <h4 className="mb-0">Details</h4>
                  <BookingStatus booking={booking} />
                </div>
                <BookingMeta booking={booking} className="bkmeta dbmeta" />
                {booking.next_statuses.length > 0 && <div className="bkactions dbactions"><BookingActions booking={booking} /></div>}
              </div>
            </div>
            <div className="col-lg-7">
              <div className="fcard dbcard">
                <h4>Messages</h4>
                <p className="acsub">
                  {booking.has_email
                    ? `We email each message to ${firstName}, and they can reply from their booking page.`
                    : `${firstName} booked without an email, so they'll only see your messages on their booking page.`}
                </p>
                <BookingMessages messages={messages} chefName={chef.name} customerName={booking.full_name} viewer="chef" />
                <div className="msgform">
                  <DjangoForm
                    action={`/api/chef/bookings/${booking.id}/`}
                    fields={fields}
                    variant="stacked"
                    showHelp={false}
                    icon="fa-paper-plane"
                    button="Send"
                    buttonClass="bkbtn w-auto mt-2"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
