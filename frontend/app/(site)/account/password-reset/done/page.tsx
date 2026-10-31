// Django: accounts/password_reset_complete.html
import type { Metadata } from "next";
import Link from "next/link";
import AuthCard from "@/components/AuthCard";

export const metadata: Metadata = { title: "Password saved - Karamu" };

export default function PasswordSaved() {
  return (
    <AuthCard heading={<>Password <span>saved</span></>}>
      <p className="acsub">You can now log in with your email and new password.</p>
      <Link href="/account/login/" className="btn-red w-100 justify-content-center"><i className="fas fa-sign-in-alt"></i>Log in</Link>
    </AuthCard>
  );
}
