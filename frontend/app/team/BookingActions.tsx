// Status and payment buttons for a booking, on the bookings list and a booking's page (Django: team/_booking_actions.html).
import ActionForm from "@/components/ActionForm";
import type { TeamBooking } from "@/lib/api";
import { dayMonth, waLink } from "@/lib/format";

/** A WhatsApp message to the customer about their booking */
export const whatsappCustomer = (booking: TeamBooking) =>
  waLink(booking.phone, `Hi ${booking.full_name}, this is Karamu about your booking with ${booking.chef.name} on ${dayMonth(booking.event_date)}.`);

export default function BookingActions({ booking }: { booking: TeamBooking }) {
  const decline = booking.status === "new" ? "Decline" : "Cancel";
  return (
    <>
      {booking.next_statuses.length > 0 && (
        <div className="tmrow">
          {booking.next_statuses.map((next) => (
            <ActionForm
              key={next}
              action={`/api/team/bookings/${booking.id}/status/`}
              confirm={next === "cancelled" ? `${decline} this booking? The customer will be emailed.` : undefined}
            >
              <input type="hidden" name="status" value={next} />
              {next === "confirmed" ? (
                <div className="tmprice">
                  <input
                    type="number" name="price" className="fctrl" min="1" required aria-label="Price for the customer (KSh)"
                    placeholder="Price (KSh)" defaultValue={booking.price ?? booking.suggested_price ?? ""}
                  />
                  <button type="submit" className="bkbtn"><i className="fas fa-check"></i>Confirm</button>
                </div>
              ) : next === "completed" ? (
                <button type="submit" className="bkbtn"><i className="fas fa-flag-checkered"></i>Completed</button>
              ) : (
                <button type="submit" className="bkbtn bkbtn-ghost"><i className="fas fa-times"></i>{decline}</button>
              )}
            </ActionForm>
          ))}
        </div>
      )}
      {booking.team_payment_actions.length > 0 && (
        <div className="tmrow">
          {booking.team_payment_actions.map((action) => (
            <ActionForm
              key={action}
              action={`/api/team/bookings/${booking.id}/payment/`}
              confirm={action === "unpaid" ? "Payment not found? The customer will be asked to check their M-Pesa code."
                : action === "refunded" ? `Have you sent KSh ${booking.price} back to ${booking.phone}?` : undefined}
            >
              <input type="hidden" name="payment_status" value={action} />
              {action === "paid" ? (
                <button type="submit" className="bkbtn"><i className="fas fa-check-double"></i>{booking.payment_status === "submitted" ? "Payment received" : "Mark paid"}</button>
              ) : action === "unpaid" ? (
                <button type="submit" className="bkbtn bkbtn-ghost"><i className="fas fa-question"></i>Not found</button>
              ) : (
                <button type="submit" className="bkbtn bkbtn-ghost"><i className="fas fa-undo"></i>Mark refunded</button>
              )}
            </ActionForm>
          ))}
        </div>
      )}
    </>
  );
}
