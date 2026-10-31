// Every chef profile, with the switches to put them live, on the homepage or verified (Django: team/chefs.html).
import type { Metadata } from "next";
import Link from "next/link";
import ActionForm from "@/components/ActionForm";
import { getTeamPage, type TeamChef, type Waiting } from "@/lib/api";
import { chefUrl, rating } from "@/lib/format";

export const metadata: Metadata = { title: "Chefs" };

type Chefs = { items: TeamChef[]; show: string; filters: [string, string, number][] };

export default async function TeamChefs({ searchParams }: PageProps<"/team/chefs">) {
  const { show: wanted } = await searchParams;
  const [{ items, show, filters }, waiting] = await Promise.all([
    getTeamPage<Chefs>("chefs/", { show: wanted }),
    getTeamPage<Waiting>("waiting/"),
  ]);

  return (
    <>
      <h1 className="tmtitle">Chefs<small><Link href="/team/applications/">Applications{waiting.applications > 0 && ` (${waiting.applications} waiting)`}</Link></small></h1>
      <div className="mkpills dbtabs tmtabs">
        {filters.map(([key, label, count]) => (
          <Link key={key} href={`/team/chefs/?show=${key}`} className={key === show ? "active" : ""}>{label} <span>{count}</span></Link>
        ))}
      </div>

      {items.map((chef) => (
        <div key={chef.id} className="tmcard">
          <div className="bktop">
            <a href={chefUrl(chef.slug)} target="_blank" rel="noopener" className="bkname">{chef.name}</a>
            <span className={`bkstatus ${chef.is_active ? "bk-confirmed" : "bk-new"}`}>{chef.is_active ? "Live" : "Not live"}</span>
            {!chef.is_accepting_bookings && <span className="bkstatus bk-completed">Paused</span>}
            {chef.is_featured && <span className="bkstatus bk-completed">Homepage</span>}
            {chef.is_verified ? <span className="bkstatus bk-confirmed">Verified</span> : chef.documents_updated_at && <span className="bkstatus bk-new">New documents</span>}
          </div>
          <div className="bkmeta">
            <span><i className="fas fa-map-marker-alt"></i>{chef.area && `${chef.area}, `}{chef.city}</span>
            <span><i className="fas fa-utensils"></i>{chef.cuisine}</span>
            <span>{chef.review_count ? <><i className="fas fa-star"></i>{rating(chef.avg_rating)} ({chef.review_count})</> : <><i className="fas fa-seedling"></i>No reviews</>}</span>
            <span><i className="fas fa-phone-alt"></i>{chef.phone}</span>
            {!chef.has_login && <span><i className="fas fa-user-slash"></i>No login</span>}
          </div>
          <div className="tmrow">
            <ActionForm action={`/api/team/chefs/${chef.id}/live/`} confirm={chef.is_active ? `Hide ${chef.name} from the marketplace?` : undefined}>
              <input type="hidden" name="on" value={chef.is_active ? "0" : "1"} />
              {chef.is_active
                ? <button type="submit" className="bkbtn bkbtn-ghost"><i className="fas fa-eye-slash"></i>Hide</button>
                : <button type="submit" className="bkbtn"><i className="fas fa-rocket"></i>Put live</button>}
            </ActionForm>
            <ActionForm action={`/api/team/chefs/${chef.id}/featured/`}>
              <input type="hidden" name="on" value={chef.is_featured ? "0" : "1"} />
              <button type="submit" className="bkbtn bkbtn-plain"><i className="fas fa-home"></i>{chef.is_featured ? "Off homepage" : "On homepage"}</button>
            </ActionForm>
            {chef.application_id && <Link className="bkbtn bkbtn-plain" href={`/team/applications/${chef.application_id}/`}><i className="fas fa-id-card"></i>Application</Link>}
          </div>
          <div className="tmrow">
            {chef.national_id && <a className="bkbtn bkbtn-plain" href={chef.national_id} target="_blank" rel="noopener"><i className="fas fa-id-card"></i>ID</a>}
            {chef.food_handler_certificate && <a className="bkbtn bkbtn-plain" href={chef.food_handler_certificate} target="_blank" rel="noopener"><i className="fas fa-certificate"></i>Food handler&apos;s cert</a>}
            <ActionForm action={`/api/team/chefs/${chef.id}/verified/`}>
              <input type="hidden" name="on" value={chef.is_verified ? "0" : "1"} />
              <button type="submit" className={`bkbtn ${chef.is_verified ? "bkbtn-plain" : "bkbtn-ghost"}`}><i className="fas fa-check-circle"></i>{chef.is_verified ? "Unverify" : "Mark verified"}</button>
            </ActionForm>
          </div>
        </div>
      ))}
      {items.length === 0 && <div className="mkempty"><i className="fas fa-user"></i><p>Nothing here.</p></div>}
    </>
  );
}
