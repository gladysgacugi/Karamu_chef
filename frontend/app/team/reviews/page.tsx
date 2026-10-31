// Reviews to publish or decline (Django: team/reviews.html).
import type { Metadata } from "next";
import Link from "next/link";
import ActionForm from "@/components/ActionForm";
import { getTeamPage, type TeamList, type TeamReview } from "@/lib/api";
import { dayMonth, timesince } from "@/lib/format";
import StatusTabs, { Stars } from "../StatusTabs";

export const metadata: Metadata = { title: "Reviews" };

export default async function TeamReviews({ searchParams }: PageProps<"/team/reviews">) {
  const { status } = await searchParams;
  const list = await getTeamPage<TeamList<TeamReview>>("reviews/", { status });

  return (
    <>
      <h1 className="tmtitle">Reviews<small>Publish honest reviews. Decline abusive, off-topic or fake ones.</small></h1>
      <StatusTabs path="/team/reviews/" tabs={list} />

      {list.items.map((review) => (
        <div key={review.id} className="tmcard">
          <div className="bktop">
            <span className="bkname">{review.customer_name}</span>
            <Stars rating={review.rating} />
            <span className={`bkstatus rv-${review.status}`}>{review.status_display}</span>
          </div>
          <div className="bkmeta">
            <span><i className="fas fa-utensils"></i>{review.chef}</span>
            {review.booking ? (
              <span><i className="fas fa-check-circle"></i><Link href={`/team/bookings/${review.booking.id}/`}>Booking {review.booking.payment_reference}, {dayMonth(review.booking.event_date)}</Link></span>
            ) : (
              <span><i className="fas fa-question-circle"></i>Not linked to a booking</span>
            )}
          </div>
          <p className="bknotes" style={{ whiteSpace: "pre-line" }}>{review.comment}</p>
          <small className="bkwhen">Written {timesince(review.created_at)} ago</small>
          <div className="tmrow">
            {review.status !== "published" && (
              <ActionForm action={`/api/team/reviews/${review.id}/status/`}>
                <input type="hidden" name="status" value="published" />
                <button type="submit" className="bkbtn"><i className="fas fa-check"></i>Publish</button>
              </ActionForm>
            )}
            {review.status !== "rejected" && (
              <ActionForm action={`/api/team/reviews/${review.id}/status/`} confirm={review.status === "published" ? "Take this review off the profile?" : undefined}>
                <input type="hidden" name="status" value="rejected" />
                <button type="submit" className="bkbtn bkbtn-ghost"><i className="fas fa-eye-slash"></i>{review.status === "published" ? "Unpublish" : "Decline"}</button>
              </ActionForm>
            )}
          </div>
        </div>
      ))}
      {list.items.length === 0 && (
        <div className="mkempty"><i className="fas fa-star"></i><p>{list.status === "pending" ? "All caught up - no reviews to check." : "Nothing here."}</p></div>
      )}
    </>
  );
}
