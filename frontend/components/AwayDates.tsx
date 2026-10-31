// The dates a chef is away, above the booking form (Django: partials/time_off.html).
import type { ChefDetail } from "@/lib/api";
import { dayMonth } from "@/lib/format";

export default function AwayDates({ timeOff }: { timeOff: ChefDetail["time_off"] }) {
  if (timeOff.length === 0) return null;
  return (
    <p className="cpaway"><i className="fas fa-plane"></i><strong>Away:</strong>{" "}
      {timeOff.map((t) => (t.start_date === t.end_date ? dayMonth(t.start_date) : `${dayMonth(t.start_date)} - ${dayMonth(t.end_date)}`)).join(", ")}
    </p>
  );
}
