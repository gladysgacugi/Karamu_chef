// Ask for a "choose a new password" email (Django: accounts/password_reset_form.html).
import type { Metadata } from "next";
import Link from "next/link";
import AuthCard from "@/components/AuthCard";
import DjangoForm from "@/components/DjangoForm";
import { getForm } from "@/lib/api";

export const metadata: Metadata = { title: "Reset your password - Karamu" };

export default async function PasswordReset() {
  const form = await getForm("auth/password-reset/");
  return (
    <AuthCard heading={<>Forgot your <span>password?</span></>}>
      <p className="acsub">Enter the email you log in with and we&apos;ll send you a link to choose a new password.</p>
      <DjangoForm
        action="/api/auth/password-reset/"
        fields={form.fields}
        variant="stacked"
        icon="fa-paper-plane"
        button="Send reset link"
        buttonClass="btn-red w-100 justify-content-center mt-4"
      />
      <p className="acfoot"><Link href="/account/login/"><i className="fas fa-arrow-left me-1"></i>Back to log in</Link></p>
    </AuthCard>
  );
}
