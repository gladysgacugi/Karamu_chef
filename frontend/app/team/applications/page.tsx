// Chef applications by status (Django: team/applications.html).
import type { Metadata } from "next";
import Link from "next/link";
import { getTeamPage, type Application, type TeamList } from "@/lib/api";
import { pluralize, timesince } from "@/lib/format";
import StatusTabs, { applicationStatusClass } from "../StatusTabs";

export const metadata: Metadata = { title: "Chef applications" };

export default async function Applications({ searchParams }: PageProps<"/team/applications">) {
  const { status } = await searchParams;
  const list = await getTeamPage<TeamList<Application>>("applications/", { status });

  return (
    <>
      <h1 className="tmtitle">Chef applications<small><Link href="/team/chefs/">All chefs on the marketplace</Link></small></h1>
      <StatusTabs path="/team/applications/" tabs={list} />

      {list.items.map((application) => (
        <Link key={application.id} href={`/team/applications/${application.id}/`} className="tmcard">
          <div className="bktop">
            <span className="bkname">{application.full_name}</span>
            <span className={`bkstatus ${applicationStatusClass(application.status)}`}>{application.status_display}</span>
          </div>
          <div className="bkmeta">
            <span><i className="fas fa-utensils"></i>{application.cuisine_display}</span>
            <span><i className="fas fa-map-marker-alt"></i>{application.location}</span>
            <span><i className="fas fa-award"></i>{application.years_experience} yr{pluralize(application.years_experience)} &middot; {application.chef_type_display}</span>
          </div>
          <small className="bkwhen">Applied {timesince(application.created_at)} ago</small>
        </Link>
      ))}
      {list.items.length === 0 && (
        <div className="mkempty"><i className="fas fa-user-check"></i><p>{list.status === "pending" ? "All caught up - no applications waiting." : "Nothing here."}</p></div>
      )}
    </>
  );
}
