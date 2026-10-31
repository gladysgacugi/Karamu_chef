// The website: top bar, navbar and footer around every page except the team pages (base.html).
import { Suspense } from "react";
import Footer from "@/components/Footer";
import CurrentNav, { Nav } from "@/components/Nav";
import SiteScripts from "@/components/SiteScripts";
import Topbar from "@/components/Topbar";
import { getMe } from "@/lib/api";

/** The navbar with the visitor's account menu if they are logged in. */
async function VisitorNav() {
  return <CurrentNav user={await getMe()} />;
}

export default function SiteLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Suspense>
        <Topbar />
      </Suspense>
      <Suspense fallback={<Nav user={null} pathname={null} />}>
        <VisitorNav />
      </Suspense>
      {children}
      <Suspense>
        <Footer />
      </Suspense>
      <Suspense>
        <SiteScripts />
      </Suspense>
    </>
  );
}
