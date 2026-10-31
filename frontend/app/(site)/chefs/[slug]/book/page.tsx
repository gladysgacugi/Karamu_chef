// The booking page (Django: booking.html). The form on the chef's profile does the same thing.
import type { Metadata } from "next";
import Link from "next/link";
import AwayDates from "@/components/AwayDates";
import BookingForm, { ChosenPackage, PackageLink } from "@/components/BookingForm";
import WhatsAppFloat from "@/components/WhatsAppFloat";
import { getBookingForm, getChef } from "@/lib/api";
import { chefUrl, cityUrl, first, price, rating } from "@/lib/format";

export async function generateMetadata({ params }: PageProps<"/chefs/[slug]/book">): Promise<Metadata> {
  const chef = await getChef((await params).slug);
  return {
    title: `Book ${chef.name} - Karamu`,
    description: `Request a booking with ${chef.name}, ${chef.cuisine} chef in ${chef.city.name}. No payment until the chef confirms.`,
  };
}

export default async function BookChef({ params, searchParams }: PageProps<"/chefs/[slug]/book">) {
  const { slug } = await params;
  const { package: chosen } = await searchParams;
  const [chef, booking] = await Promise.all([getChef(slug), getBookingForm(slug, chosen)]);
  const next = encodeURIComponent(`/chefs/${chef.slug}/book/${first(chosen) ? `?package=${first(chosen)}` : ""}`);

  return (
    <>
      <section className="mkhero dbhero">
        <div className="container">
          <Link href={chefUrl(chef.slug)} className="dbback"><i className="fas fa-arrow-left me-1"></i>Back to {chef.name}&apos;s profile</Link>
          <span className="slbl d-block">Request a booking</span>
          <h1 className="stitle">Book <span>{chef.name}</span></h1>
          <p className="sdesc">Tell {chef.name} about your event. No payment now: the chef confirms first, then you pay securely via M-Pesa.</p>
        </div>
      </section>

      <section className="dbmain">
        <div className="container">
          <ChosenPackage initial={String(booking.fields.find((f) => f.name === "package")?.value ?? "")}>
            <div className="row g-4">
              <div className="col-lg-7 order-2 order-lg-1">
                <div className="fcard" id="book">
                  <h4 style={{ fontSize: "1.2rem", fontWeight: 800 }}>Your event</h4>
                  {!chef.is_accepting_bookings ? (
                    <p className="cppaused"><i className="fas fa-pause-circle"></i>{chef.name} is not taking new bookings right now. <Link href={cityUrl(chef.city.slug)}>See other chefs in {chef.city.name}</Link> or WhatsApp us and we&apos;ll help.</p>
                  ) : (
                    <>
                      <AwayDates timeOff={chef.time_off} />
                      {!booking.logged_in && (
                        <p className="cplogin"><Link href={`/account/login/?next=${next}`}>Log in</Link> or <Link href={`/account/signup/?next=${next}`}>create an account</Link> to fill in your details and track this booking.</p>
                      )}
                      <BookingForm slug={chef.slug} fields={booking.fields} />
                    </>
                  )}
                </div>
              </div>

              <div className="col-lg-5 order-1 order-lg-2">
                <div className="fcard cpbook">
                  <div className="bkchef">
                    <img src={chef.photo} alt={chef.name} className="bkphoto" />
                    <div>
                      <Link href={chefUrl(chef.slug)} className="bkname">{chef.name} {chef.is_verified && <i className="fas fa-check-circle" style={{ color: "var(--green)" }} title="ID & food handler's certificate verified"></i>}</Link>
                      <div className="bkmeta">
                        <span>{chef.review_count ? <><i className="fas fa-star"></i>{rating(chef.avg_rating)} ({chef.review_count})</> : <><i className="fas fa-seedling"></i>New</>}</span>
                        <span><i className="fas fa-map-marker-alt"></i>{chef.city.name}</span>
                      </div>
                    </div>
                  </div>
                  <div className="cpbookprice mt-3">From <strong>KSh {price(chef.starting_price)}</strong> <small>{chef.price_unit}</small></div>
                  {chef.packages.length > 0 && (
                    <>
                      <h6 className="bkpkghd">Packages</h6>
                      {chef.packages.map((pkg) => (
                        <PackageLink key={pkg.id} id={pkg.id} className="bkpkg" onClass="on">
                          <span>{pkg.name}</span>
                          <strong>KSh {price(pkg.price)} <small>{pkg.price_unit}</small></strong>
                        </PackageLink>
                      ))}
                    </>
                  )}
                  <p className="cpbooknote mt-3 mb-0"><i className="fas fa-shield-alt"></i> No payment now. {chef.name} confirms first, then you pay securely via M-Pesa.</p>
                </div>
              </div>
            </div>
          </ChosenPackage>
        </div>
      </section>

      <WhatsAppFloat text={`Hi Karamu, I'd like help booking ${chef.name}.`} />
    </>
  );
}
