// Messages from the contact form (Django: team/inbox.html).
import type { Metadata } from "next";
import Link from "next/link";
import ActionForm from "@/components/ActionForm";
import { getTeamPage, type ContactMessage, type Waiting } from "@/lib/api";
import { timesince, waLink } from "@/lib/format";

export const metadata: Metadata = { title: "Inbox" };

export default async function TeamInbox({ searchParams }: PageProps<"/team/inbox">) {
  const { show } = await searchParams;
  const [{ items, show_all }, waiting] = await Promise.all([
    getTeamPage<{ items: ContactMessage[]; show_all: boolean }>("inbox/", { show }),
    getTeamPage<Waiting>("waiting/"),
  ]);

  return (
    <>
      <h1 className="tmtitle">Inbox<small>Messages from the contact form</small></h1>
      <div className="mkpills dbtabs tmtabs">
        <Link href="/team/inbox/" className={show_all ? "" : "active"}>To reply <span>{waiting.inbox}</span></Link>
        <Link href="/team/inbox/?show=all" className={show_all ? "active" : ""}>All</Link>
      </div>

      {items.map((msg) => (
        <div key={msg.id} className="tmcard">
          <div className="bktop">
            <span className="bkname">{msg.name}</span>
            <span className={`bkstatus ${msg.is_handled ? "bk-completed" : "bk-new"}`}>{msg.is_handled ? "Replied" : msg.subject_display}</span>
          </div>
          <div className="bkmeta">
            <span><i className="fas fa-envelope"></i>{msg.email}</span>
            {msg.phone && <span><i className="fas fa-phone-alt"></i>{msg.phone}</span>}
          </div>
          <p className="bknotes" style={{ color: "#444", whiteSpace: "pre-line" }}>{msg.message}</p>
          <small className="bkwhen">Sent {timesince(msg.created_at)} ago</small>
          <div className="tmrow">
            <a className="bkbtn bkbtn-plain" href={`mailto:${msg.email}?subject=${encodeURIComponent(`Re: ${msg.subject_display} - Karamu`)}`}><i className="fas fa-reply"></i>Email</a>
            {msg.phone && <a className="bkbtn bkbtn-wa" href={waLink(msg.phone, `Hi ${msg.name}, this is Karamu replying to your message.`)} target="_blank" rel="noopener"><i className="fab fa-whatsapp"></i>WhatsApp</a>}
            {!msg.is_handled && (
              <ActionForm action={`/api/team/inbox/${msg.id}/replied/`}>
                <button type="submit" className="bkbtn"><i className="fas fa-check"></i>Replied</button>
              </ActionForm>
            )}
          </div>
        </div>
      ))}
      {items.length === 0 && (
        <div className="mkempty"><i className="fas fa-envelope-open"></i><p>{show_all ? "No messages yet." : "All caught up - nothing to reply to."}</p></div>
      )}
    </>
  );
}
