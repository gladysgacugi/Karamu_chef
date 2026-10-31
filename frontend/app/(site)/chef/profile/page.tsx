// Profile, packages and prices (Django: chef/profile_edit.html).
import type { Metadata } from "next";
import Flash from "@/components/Flash";
import { getChefPage, type ChefFormPage, type Formset } from "@/lib/api";
import ChefHero from "../ChefHero";
import ProfileForm from "./ProfileForm";

export const metadata: Metadata = { title: "Profile, menu & prices - Karamu" };

export default async function ProfileEdit() {
  const { chef, fields, packages } = await getChefPage<ChefFormPage & { packages: Formset }>("profile/");

  return (
    <>
      <ChefHero title={<>Edit <span>{chef.name}</span></>}>
        Changes show on your public profile straight away{!chef.is_active && ", once our team has set it live"}. To change your display name, WhatsApp us.
      </ChefHero>

      <section className="dbmain">
        <div className="container">
          <Flash />
          <ProfileForm fields={fields} packages={packages} />
        </div>
      </section>
    </>
  );
}
