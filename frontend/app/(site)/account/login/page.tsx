// Log in with email and password (Django: accounts/login.html). Customer | Chef tabs (?role=) change the wording only:
// both post to the same login, which sends each user to their own home. The team logs in through either.
import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import AuthCard from "@/components/AuthCard";
import DjangoForm from "@/components/DjangoForm";
import { getForm } from "@/lib/api";
import { first } from "@/lib/format";

export const metadata: Metadata = { title: "Log in - Karamu" };

export default async function Login({ searchParams }: PageProps<"/account/login">) {
  const params = await searchParams;
  const next = first(params.next);
  const chef = first(params.role) === "chef";
  const form = await getForm<{ redirect: string | null }>("auth/login/", { next });
  if (form.redirect) redirect(form.redirect); // already logged in
  const nextQuery = next ? `?next=${encodeURIComponent(next)}` : "";
  const roleHref = (r: string) => `/account/login/?role=${r}${next ? `&next=${encodeURIComponent(next)}` : ""}`;

  return (
    <AuthCard eyebrow="Welcome back" heading={<>Log in to <span>Karamu</span></>}>
      <nav className="actabs" aria-label="Log in as">
        <Link href={roleHref("customer")} className={chef ? "" : "active"} aria-current={chef ? undefined : "page"} replace scroll={false}>
          <i className="fas fa-user" />Customer
        </Link>
        <Link href={roleHref("chef")} className={chef ? "active" : ""} aria-current={chef ? "page" : undefined} replace scroll={false}>
          <i className="fas fa-utensils" />Chef
        </Link>
      </nav>
      <p className="acsub">
        {chef ? "Manage your profile, menu and booking requests." : "See and manage your bookings."}
      </p>
      <DjangoForm
        action="/api/auth/login/"
        fields={form.fields}
        variant="stacked"
        hidden={{ next }}
        extra={<div className="acrow"><Link href="/account/password-reset/">Forgot password?</Link></div>}
        icon="fa-sign-in-alt"
        button={chef ? "Log in as a chef" : "Log in"}
      />
      {chef ? (
        <p className="acfoot">Not a chef partner yet? <Link href="/become-a-chef/">Apply to become a chef</Link>. We&apos;ll email your login once you&apos;re approved.</p>
      ) : (
        <p className="acfoot">New here? <Link href={`/account/signup/${nextQuery}`}>Create a customer account</Link></p>
      )}
    </AuthCard>
  );
}
