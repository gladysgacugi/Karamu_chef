// The team pages: a phone-friendly admin with a bottom menu, instead of the website's navbar and footer (Django: team/base.html).
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import Flash from "@/components/Flash";
import LogoutButton from "@/components/LogoutButton";
import { getTeamWaiting } from "@/lib/api";
import CurrentTeamNav, { TeamNav } from "./TeamNav";

export const metadata: Metadata = {
  title: { template: "%s - Karamu", default: "Team - Karamu" },
  robots: { index: false },
  icons: { icon: "/static/img/brand/karamu-icon-192.png" },
};

async function TeamNavWithBadges() {
  return <CurrentTeamNav waiting={await getTeamWaiting()} />;
}

export default function TeamLayout({ children }: LayoutProps<"/team">) {
  return (
    <div className="team">
      <header className="tmbar">
        <div className="container">
          <img src="/static/img/brand/karamu-icon-192.png" alt="" />
          <Link href="/team/" className="tmbrand">Karamu<small>Team</small></Link>
          <a href="/admin/" className="tmicon" title="Full admin"><i className="fas fa-cog"></i></a>
          <Link href="/" className="tmicon" title="View website"><i className="fas fa-globe-africa"></i></Link>
          <LogoutButton className="tmicon" title="Log out"><i className="fas fa-sign-out-alt"></i></LogoutButton>
        </div>
      </header>

      <main className="container tmmain">
        <Flash />
        {children}
      </main>

      <Suspense fallback={<TeamNav waiting={null} pathname={null} />}>
        <TeamNavWithBadges />
      </Suspense>
    </div>
  );
}
