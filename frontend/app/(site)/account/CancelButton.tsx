"use client";

import { goTo, post } from "@/lib/client";

export default function CancelButton({ bookingId }: { bookingId: number }) {
  async function cancel() {
    if (!confirm("Cancel this booking request?")) return;
    const answer = await post(`/api/account/bookings/${bookingId}/cancel/`);
    const error = answer.errors?.__all__?.[0];
    goTo("/account/", error ?? answer.message, !!error);
  }
  return <button type="button" className="bkbtn bkbtn-ghost" onClick={cancel}><i className="fas fa-times"></i>Cancel request</button>;
}
