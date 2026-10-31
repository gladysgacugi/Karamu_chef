// Django: accounts/password_reset_done.html
import type { Metadata } from "next";
import Link from "next/link";
import AuthCard from "@/components/AuthCard";
import { getSite } from "@/lib/api";

export const metadata: Metadata = { title: "Check your email - Karamu" };

export default async function PasswordResetSent() {
  const site = await getSite();
  return (
    <AuthCard heading={<>Check your <span>email</span></>}>
      <p className="acsub">If an account exists for that address, we&apos;ve sent a link to choose a new password. It works for 3 days.</p>
      <p className="acsub">Nothing arrived? Check your spam folder, or WhatsApp us on <a href={site.whatsapp_url} target="_blank" rel="noopener">{site.whatsapp_display}</a>.</p>
      <Link href="/account/login/" className="btn-red w-100 justify-content-center"><i className="fas fa-arrow-left"></i>Back to log in</Link>
    </AuthCard>
  );
}
