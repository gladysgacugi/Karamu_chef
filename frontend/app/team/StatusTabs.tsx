// The status tabs above a team list, then "All" (Django: team/_tabs.html).
import Link from "next/link";
import type { Application, StatusTabs as Tabs } from "@/lib/api";

export const applicationStatusClass = (status: Application["status"]) =>
  status === "pending" ? "bk-new" : status === "approved" ? "bk-confirmed" : "bk-cancelled";

export default function StatusTabs({ path, tabs }: { path: string; tabs: Tabs }) {
  return (
    <div className="mkpills dbtabs tmtabs">
      {tabs.status_tabs.map(([value, label, count]) => (
        <Link key={value} href={`${path}?status=${value}`} className={value === tabs.status ? "active" : ""}>{label} <span>{count}</span></Link>
      ))}
      <Link href={`${path}?status=`} className={tabs.status ? "" : "active"}>All <span>{tabs.total}</span></Link>
    </div>
  );
}

/** A review's rating as five stars */
export function Stars({ rating }: { rating: number }) {
  return (
    <span className="rvstars">
      {[1, 2, 3, 4, 5].map((i) => <i key={i} className={`${i <= rating ? "fas" : "far"} fa-star`}></i>)}
    </span>
  );
}
