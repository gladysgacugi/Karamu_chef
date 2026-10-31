// Customers who want the team to pick a chef for them (Django: team/requests.html).
import type { Metadata } from "next";
import ActionForm from "@/components/ActionForm";
import { getTeamPage, type MatchRequest, type TeamList } from "@/lib/api";
import { dayMonth, timesince, waLink, weekdayDate } from "@/lib/format";
import StatusTabs from "../StatusTabs";

export const metadata: Metadata = { title: "Find-a-chef requests" };

const STATUS_CLASS = { new: "bk-new", matched: "bk-confirmed", closed: "bk-completed" };

export default async function TeamRequests({ searchParams }: PageProps<"/team/requests">) {
  const { status } = await searchParams;
  const list = await getTeamPage<TeamList<MatchRequest>>("requests/", { status });

  return (
    <>
      <h1 className="tmtitle">Find-a-chef requests<small>Customers who want you to pick a chef for them</small></h1>
      <StatusTabs path="/team/requests/" tabs={list} />

      {list.items.map((match) => (
        <div key={match.id} className="tmcard">
          <div className="bktop">
            <span className="bkname">{match.full_name}</span>
            <span className={`bkstatus ${STATUS_CLASS[match.status]}`}>{match.status_display}</span>
          </div>
          <div className="bkmeta">
            <span><i className="fas fa-glass-cheers"></i>{match.occasion_display}</span>
            <span><i className="fas fa-calendar"></i>{weekdayDate(match.event_date)}, {match.time_slot_display}</span>
            <span><i className="fas fa-users"></i>{match.guests_display}</span>
            <span><i className="fas fa-utensils"></i>{match.cuisine_display || "Chef decides"}</span>
            <span><i className="fas fa-map-marker-alt"></i>{match.location}</span>
            <span><i className="fas fa-phone-alt"></i>{match.phone}</span>
          </div>
          {match.notes && <p className="bknotes"><strong>Requests:</strong> {match.notes}</p>}
          <small className="bkwhen">Sent {timesince(match.created_at)} ago</small>
          <div className="tmrow">
            <a className="bkbtn bkbtn-wa" href={waLink(match.phone, `Hi ${match.full_name}, this is Karamu about your ${match.occasion_display.toLowerCase()} on ${dayMonth(match.event_date)}.`)} target="_blank" rel="noopener"><i className="fab fa-whatsapp"></i>WhatsApp</a>
            <a className="bkbtn bkbtn-plain" href={`tel:${match.phone}`}><i className="fas fa-phone-alt"></i>Call</a>
          </div>
          {match.status === "new" && (
            <div className="tmrow">
              <ActionForm action={`/api/team/requests/${match.id}/status/`}>
                <input type="hidden" name="status" value="matched" />
                <button type="submit" className="bkbtn"><i className="fas fa-handshake"></i>Matched</button>
              </ActionForm>
              <ActionForm action={`/api/team/requests/${match.id}/status/`}>
                <input type="hidden" name="status" value="closed" />
                <button type="submit" className="bkbtn bkbtn-ghost"><i className="fas fa-archive"></i>Close</button>
              </ActionForm>
            </div>
          )}
        </div>
      ))}
      {list.items.length === 0 && (
        <div className="mkempty"><i className="fas fa-concierge-bell"></i><p>{list.status === "new" ? "All caught up - no new requests." : "Nothing here."}</p></div>
      )}
    </>
  );
}
