"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect } from "react";
import type { User } from "@/lib/api";
import { logOut } from "./LogoutButton";

/** The navbar for the current page. */
export default function CurrentNav({ user }: { user: User | null }) {
  return <Nav user={user} pathname={usePathname()} />;
}

/** The page and visitor are only known at request time, so the prerendered shell shows the navbar logged out with nothing active. */
export function Nav({ user, pathname }: { user: User | null; pathname: string | null }) {
  const isHome = pathname === "/";
  // Section links like #about only work on the homepage; elsewhere they point back to "/"
  const prefix = isHome ? "" : "/";
  const onMarketplace = !!pathname?.startsWith("/marketplace") || !!pathname?.startsWith("/chefs/");
  const onLogin = !!pathname?.startsWith("/account/login") || !!pathname?.startsWith("/account/signup");

  // Close the mobile menu after moving to another page
  useEffect(() => {
    document.getElementById("navmenu")?.classList.remove("show");
  }, [pathname]);

  return (
    <nav className="navbar navbar-expand-lg" id="nav">
      <div className="container">
        <Link className="navbar-brand" href="/">
          <div className="blogo">
            <img className="bico" src="/static/img/brand/karamu-mark.svg" alt="" />
            <div>
              <div className="bname">Karamu</div>
              <div className="bsub">Private chefs &middot; at your table</div>
            </div>
          </div>
        </Link>
        <button className="navbar-toggler border-0" type="button" data-bs-toggle="collapse" data-bs-target="#navmenu">
          <i className="fas fa-bars" style={{ color: "var(--primary)", fontSize: "1.35rem" }}></i>
        </button>
        <div className="collapse navbar-collapse" id="navmenu">
          <ul className="navbar-nav mx-auto">
            <li className="nav-item"><a className={`nav-link${isHome ? " active" : ""}`} href={`${prefix}#hero`}>Home</a></li>
            <li className="nav-item"><Link className={`nav-link${onMarketplace ? " active" : ""}`} href="/marketplace/">Find a Chef</Link></li>
            <li className="nav-item"><a className="nav-link" href={`${prefix}#menu`}>Packages</a></li>
            <li className="nav-item"><a className="nav-link" href={`${prefix}#history`}>How It Works</a></li>
            <li className="nav-item"><a className="nav-link" href={`${prefix}#hours`}>Become a Chef</a></li>
            <li className="nav-item"><a className="nav-link" href={`${prefix}#contact-section`}>Contact</a></li>
          </ul>
          <div className="d-flex align-items-center gap-1">
            {isHome && (
              <button id="navSearchBtn" title="Search" onClick={() => window.dispatchEvent(new Event("open-search"))}>
                <i className="fas fa-search"></i>
              </button>
            )}
            {user ? (
              <div className="dropdown">
                <a href="#" className="nav-link nav-acct dropdown-toggle" data-bs-toggle="dropdown" aria-expanded="false"><i className="fas fa-user-circle me-1"></i>{user.first_name || "My account"}</a>
                <ul className="dropdown-menu dropdown-menu-end acmenu">
                  {user.is_staff && <li><Link className="dropdown-item" href="/team/"><i className="fas fa-clipboard-check"></i>Team dashboard</Link></li>}
                  {user.is_chef && (
                    <>
                      <li><Link className="dropdown-item" href="/chef/"><i className="fas fa-calendar-check"></i>Chef bookings</Link></li>
                      <li><Link className="dropdown-item" href="/chef/profile/"><i className="fas fa-user-edit"></i>Edit my profile</Link></li>
                      <li><Link className="dropdown-item" href="/chef/availability/"><i className="fas fa-calendar-alt"></i>Availability</Link></li>
                    </>
                  )}
                  <li><Link className="dropdown-item" href="/account/"><i className="fas fa-receipt"></i>My bookings</Link></li>
                  <li><hr className="dropdown-divider" /></li>
                  <li><button type="button" className="dropdown-item" onClick={logOut}><i className="fas fa-sign-out-alt"></i>Log out</button></li>
                </ul>
              </div>
            ) : (
              <Link href="/account/login/" className={`nav-link nav-acct${onLogin ? " active" : ""}`}><i className="fas fa-user me-1"></i>Log in</Link>
            )}
            <Link href="/marketplace/" className="nav-link nav-cta"><i className="fas fa-store me-1"></i>Browse Marketplace</Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
