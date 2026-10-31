// Confirm (with the price), complete, decline or cancel a booking (Django: chef/_booking_actions.html).
import ActionForm from "@/components/ActionForm";
import type { ChefBooking } from "@/lib/api";

export default function BookingActions({ booking }: { booking: ChefBooking }) {
  return booking.next_statuses.map((next) => (
    <ActionForm
      key={next}
      action={`/api/chef/bookings/${booking.id}/status/`}
      confirm={next === "cancelled" ? "Decline this booking? The customer will be told you can't make it." : undefined}
    >
      <input type="hidden" name="status" value={next} />
      {next === "confirmed" ? (
        <>
          <label className="flbl" htmlFor={`price-${booking.id}`}>Price for the customer (KSh)</label>
          <input
            type="number" name="price" id={`price-${booking.id}`} className="fctrl bkprice" min="1" required
            defaultValue={booking.price ?? booking.suggested_price ?? ""} placeholder="e.g. 6000"
          />
          <button type="submit" className="bkbtn mt-2"><i className="fas fa-check"></i>Confirm</button>
        </>
      ) : next === "completed" ? (
        <button type="submit" className="bkbtn"><i className="fas fa-flag-checkered"></i>Mark completed</button>
      ) : (
        <button type="submit" className="bkbtn bkbtn-ghost"><i className="fas fa-times"></i>{booking.status === "new" ? "Decline" : "Cancel"}</button>
      )}
    </ActionForm>
  ));
}
