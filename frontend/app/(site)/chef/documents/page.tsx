// The chef's ID and food handler's certificate. A new upload goes back to the team to check (Django: chef/documents.html).
import type { Metadata } from "next";
import Flash from "@/components/Flash";
import { getChefPage, type ChefFormPage } from "@/lib/api";
import { dayMonthYear } from "@/lib/format";
import ChefHero from "../ChefHero";
import DocumentsForm from "./DocumentsForm";

export const metadata: Metadata = { title: "Documents - Karamu" };

export default async function Documents() {
  const { chef, fields } = await getChefPage<ChefFormPage>("documents/");

  return (
    <>
      <ChefHero title={<>Your <span>documents</span></>}>
        Only you and the Karamu team can see these. Upload a new copy when one expires or changes.
      </ChefHero>

      <section className="dbmain">
        <div className="container">
          <Flash />
          <div className="fcard dbcard dbnarrow">
            <div className="bktop">
              <h4 className="mb-0">Verification</h4>
              {chef.is_verified ? (
                <span className="bkstatus bk-confirmed"><i className="fas fa-check-circle me-1"></i>Verified</span>
              ) : chef.documents_updated_at ? (
                <span className="bkstatus bk-new">Being checked</span>
              ) : (
                <span className="bkstatus bk-completed">Not verified</span>
              )}
            </div>
            <p className="acsub">
              {chef.is_verified
                ? "Customers see a \"verified\" badge on your profile."
                : chef.documents_updated_at
                  ? `You uploaded new documents on ${dayMonthYear(chef.documents_updated_at)}. We'll check them and put your "verified" badge back.`
                  : "Upload your ID and food handler's certificate to get a \"verified\" badge on your profile."}
            </p>
            <DocumentsForm fields={fields} verified={chef.is_verified} />
          </div>
        </div>
      </section>
    </>
  );
}
