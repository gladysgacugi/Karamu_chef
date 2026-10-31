// Customer sign-up (Django: accounts/signup.html). Chefs get their login from the team instead.
import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import AuthCard from "@/components/AuthCard";
import DjangoForm from "@/components/DjangoForm";
import { getForm } from "@/lib/api";
import { first } from "@/lib/format";

export const metadata: Metadata = { title: "Create an account - Karamu" };

export default async function SignUp({ searchParams }: PageProps<"/account/signup">) {
  const next = first((await searchParams).next);
  const form = await getForm<{ redirect: string | null }>("auth/signup/");
  if (form.redirect) redirect(form.redirect); // already logged in

  return (
    <AuthCard eyebrow="Join Karamu" heading={<>Create your <span>account</span></>}>
      <p className="acsub">Book chefs faster with your details filled in, and follow every booking in one place.</p>
      <DjangoForm
        action="/api/auth/signup/"
        fields={form.fields}
        variant="stacked"
        hidden={{ next }}
        icon="fa-user-plus"
        button="Create account"
        buttonClass="btn-red w-100 justify-content-center mt-4"
      />
      <p className="acfoot">Already have an account? <Link href={`/account/login/${next ? `?next=${encodeURIComponent(next)}` : ""}`}>Log in</Link></p>
    </AuthCard>
  );
}
