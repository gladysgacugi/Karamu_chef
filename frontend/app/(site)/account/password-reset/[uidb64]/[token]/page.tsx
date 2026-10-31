// The "choose a password" link from a password reset or chef invite email (Django: accounts/password_reset_confirm.html).
import type { Metadata } from "next";
import Link from "next/link";
import AuthCard from "@/components/AuthCard";
import DjangoForm from "@/components/DjangoForm";
import { getForm } from "@/lib/api";

// The link works like a password: keep it out of the Referer header sent to other sites
export const metadata: Metadata = { title: "Choose a password - Karamu", referrer: "same-origin" };

export default async function SetPassword({ params }: PageProps<"/account/password-reset/[uidb64]/[token]">) {
  const { uidb64, token } = await params;
  const path = `auth/password-reset/${encodeURIComponent(uidb64)}/${encodeURIComponent(token)}/`;
  const form = await getForm<{ validlink: boolean; username: string }>(path);

  return (
    <AuthCard heading={<>Choose a <span>password</span></>}>
      {form.validlink ? (
        <>
          <p className="acsub">Logging in as <strong>{form.username}</strong>.</p>
          <DjangoForm
            action={`/api/${path}`}
            fields={form.fields}
            variant="stacked"
            icon="fa-lock"
            button="Save password"
            buttonClass="btn-red w-100 justify-content-center mt-4"
          />
        </>
      ) : (
        <>
          <p className="acsub">This link has expired or was already used. Request a new one below.</p>
          <Link href="/account/password-reset/" className="btn-red w-100 justify-content-center"><i className="fas fa-redo"></i>Send a new link</Link>
        </>
      )}
    </AuthCard>
  );
}
