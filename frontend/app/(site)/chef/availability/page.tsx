// Time off and pausing new bookings (Django: chef/availability.html).
import type { Metadata } from "next";
import ActionForm from "@/components/ActionForm";
import DjangoForm from "@/components/DjangoForm";
import Flash from "@/components/Flash";
import { getChefPage, type ChefBooking, type ChefFormPage, type TimeOff } from "@/lib/api";
import { pluralize, weekdayDate, weekdayDayMonth } from "@/lib/format";
import ChefHero from "../ChefHero";

export const metadata: Metadata = { title: "Availability - Karamu" };

export default async function Availability() {
  const { chef, fields, time_off, upcoming } = await getChefPage<ChefFormPage & { time_off: TimeOff[]; upcoming: ChefBooking[] }>("availability/");

  return (
    <>
      <ChefHero title={<>Your <span>availability</span></>}>
        Customers can&apos;t book you on days you&apos;re away, or at a time you already have a confirmed booking.
      </ChefHero>

      <section className="dbmain">
        <div className="container">
          <Flash />
          <div className="row g-4">
            <div className="col-lg-6">
              <div className="fcard dbcard">
                <h4>New bookings</h4>
                {chef.is_accepting_bookings ? (
                  <>
                    <p className="acsub"><span className="bkstatus bk-confirmed">Taking bookings</span> Customers can send you booking requests.</p>
                    <ActionForm action="/api/chef/availability/accepting/" confirm="Pause new bookings? Your profile stays visible but customers cannot send requests.">
                      <input type="hidden" name="accepting" value="0" />
                      <button type="submit" className="bkbtn bkbtn-ghost w-auto"><i className="fas fa-pause"></i>Pause new bookings</button>
                    </ActionForm>
                    <small className="achelp">Bookings you&apos;ve already confirmed are not affected.</small>
                  </>
                ) : (
                  <>
                    <p className="acsub"><span className="bkstatus bk-new">Paused</span> Customers can see your profile but can&apos;t send requests.</p>
                    <ActionForm action="/api/chef/availability/accepting/">
                      <input type="hidden" name="accepting" value="1" />
                      <button type="submit" className="bkbtn w-auto"><i className="fas fa-play"></i>Start taking bookings</button>
                    </ActionForm>
                  </>
                )}
              </div>

              <div className="fcard dbcard mt-4">
                <h4>Add time off</h4>
                <DjangoForm
                  action="/api/chef/availability/"
                  fields={fields}
                  wide={["note"]}
                  stars={false}
                  showHelp
                  icon="fa-plane"
                  button="Save time off"
                  buttonClass="btn-red"
                />
              </div>
            </div>

            <div className="col-lg-6">
              <div className="fcard dbcard">
                <h4>Days you&apos;re away</h4>
                {time_off.map((t) => (
                  <div key={t.id} className="dbitem avitem">
                    <div>
                      <strong>{t.start_date === t.end_date ? weekdayDate(t.start_date) : `${weekdayDayMonth(t.start_date)} - ${weekdayDate(t.end_date)}`}</strong>
                      {t.note && <small className="d-block">{t.note}</small>}
                    </div>
                    <ActionForm action={`/api/chef/availability/${t.id}/delete/`}>
                      <button type="submit" className="bkbtn bkbtn-ghost w-auto"><i className="fas fa-trash-alt"></i>Remove</button>
                    </ActionForm>
                  </div>
                ))}
                {time_off.length === 0 && <p className="acsub mb-0">No time off planned. You can be booked any day.</p>}
              </div>

              <div className="fcard dbcard mt-4">
                <h4>Confirmed bookings coming up</h4>
                {upcoming.map((booking) => (
                  <div key={booking.id} className="dbitem">
                    <strong>{weekdayDayMonth(booking.event_date)}</strong> &middot; {booking.time_slot_display}
                    <small className="d-block">{booking.full_name}, {booking.guests} guest{pluralize(booking.guests)} &middot; {booking.location}</small>
                  </div>
                ))}
                {upcoming.length === 0 && <p className="acsub mb-0">No confirmed bookings yet.</p>}
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
