// The chef application page (Django: become_a_chef.html). ?sent=1 shows the thank-you.
import type { Metadata } from "next";
import Link from "next/link";
import ChefApplicationForm from "@/components/ChefApplicationForm";
import WhatsAppFloat from "@/components/WhatsAppFloat";
import { getForm } from "@/lib/api";

export const metadata: Metadata = {
  title: "Become a Chef - Karamu",
  description: "Cook for customers across Kenya with Karamu. Set your own menu, hours and prices, and get paid via M-Pesa. Apply in minutes.",
};

export default async function BecomeChef({ searchParams }: PageProps<"/become-a-chef">) {
  const sent = "sent" in (await searchParams);
  const form = sent ? null : await getForm("chef-applications/");

  return (
    <>
      <section className="mkhero dbhero">
        <div className="container">
          <span className="slbl">Chef partners</span>
          <h1 className="stitle">Become a <span>Chef</span></h1>
          <p className="sdesc">Professional chefs and talented home cooks: share your food with families, parties and offices near you.</p>
        </div>
      </section>

      <section className="dbmain">
        <div className="container">
          <div className="row g-4">
            <div className="col-lg-4">
              <div className="fcard bcside">
                <h4>How it works</h4>
                <ol className="bcsteps">
                  <li><strong>Apply</strong>Send your details, documents and a few photos of your dishes.</li>
                  <li><strong>We review</strong>Our team checks your ID and certificate within 3 working days.</li>
                  <li><strong>Set up your profile</strong>We email you a login. Add your menu, packages and prices.</li>
                  <li><strong>Take bookings</strong>Confirm the requests that suit you and get paid via M-Pesa.</li>
                </ol>
                <h4 className="mt-4">What you need</h4>
                <ul className="bcneeds">
                  <li><i className="fas fa-id-card"></i>National ID</li>
                  <li><i className="fas fa-file-medical"></i>Food handler&apos;s certificate</li>
                  <li><i className="fas fa-mobile-alt"></i>M-Pesa number for payouts</li>
                  <li><i className="fas fa-camera"></i>3 - 5 photos of your dishes</li>
                </ul>
              </div>
            </div>

            <div className="col-lg-8">
              <div className="fcard" id="apply">
                {form ? (
                  <>
                    <h4 style={{ fontSize: "1.3rem", marginBottom: 6 }}>Apply to Become a Chef</h4>
                    <p style={{ color: "#888", fontSize: ".85rem", marginBottom: 22 }}>Fill in your details below. Our team reviews every application before your profile goes live.</p>
                    <ChefApplicationForm fields={form.fields} />
                  </>
                ) : (
                  <div className="bcdone">
                    <i className="fas fa-check-circle"></i>
                    <h4>Application received!</h4>
                    <p>Thank you for applying. We&apos;ll review your details and contact you within 3 working days. Once you&apos;re approved, we&apos;ll email you a link to set up your chef login.</p>
                    <Link href="/marketplace/" className="btn-red"><i className="fas fa-store"></i>See chefs on the marketplace</Link>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      <WhatsAppFloat text="Hi Karamu, I'd like to join as a chef." />
    </>
  );
}
