// A chef's public profile (Django: chef_detail.html), with the booking form.
import type { Metadata } from "next";
import Link from "next/link";
import AwayDates from "@/components/AwayDates";
import BookingForm, { ChosenPackage, PackageLink } from "@/components/BookingForm";
import ChefCard from "@/components/ChefCard";
import WhatsAppFloat from "@/components/WhatsAppFloat";
import { getBookingForm, getChef, getChefReviews, getChefs } from "@/lib/api";
import { bookingUrl, cityUrl, dayMonth, dayMonthYear, pluralize, price, rating, serviceUrl } from "@/lib/format";

/** The 20 newest published reviews, as the Django page shows (the API sends 12 a page). */
async function latestReviews(slug: string) {
  const page1 = await getChefReviews(slug);
  const more = page1.next ? (await getChefReviews(slug, 2)).results : [];
  return [...page1.results, ...more].slice(0, 20);
}

/** {{ text|linebreaksbr }} */
function Lines({ text }: { text: string }) {
  return text.split(/\r?\n/).map((line, i) => (
    <span key={i}>{i > 0 && <br />}{line}</span>
  ));
}

export async function generateMetadata({ params }: PageProps<"/chefs/[slug]">): Promise<Metadata> {
  const chef = await getChef((await params).slug);
  return {
    title: `${chef.name} - ${chef.headline} | Karamu`,
    description: `${chef.name}, ${chef.cuisine} chef in ${chef.city.name}. From KSh ${chef.starting_price} ${chef.price_unit}. View menu, photos and reviews and book on Karamu.`,
  };
}

export default async function ChefProfile({ params, searchParams }: PageProps<"/chefs/[slug]">) {
  const { slug } = await params;
  const { package: chosen } = await searchParams;
  const [chef, reviews, booking] = await Promise.all([getChef(slug), latestReviews(slug), getBookingForm(slug, chosen)]);
  const similarChefs = (await getChefs({ city: chef.city.slug })).results.filter((c) => c.slug !== chef.slug).slice(0, 3);
  const next = encodeURIComponent(`/chefs/${chef.slug}/#book`);

  return (
    <>
      {/* PROFILE HEADER */}
      <section className="cphero" style={{ backgroundImage: `linear-gradient(rgba(17,17,17,.72),rgba(17,17,17,.82)),url('${chef.cover}')` }}>
        <div className="container">
          <Link href="/marketplace/" className="cpback"><i className="fas fa-arrow-left"></i> Back to marketplace</Link>
          {booking.is_own_profile && (
            <div className="cpown">
              <span><i className="fas fa-user-circle"></i>This is your profile{!chef.is_active && ". It is hidden from customers until our team sets it live"}.</span>
              <a href="/chef/profile/"><i className="fas fa-user-edit"></i>Edit profile</a>
            </div>
          )}
          <div className="cphead">
            <img src={chef.photo} alt={chef.name} className="cpphoto" />
            <div>
              <h1>{chef.name} {chef.is_verified && <i className="fas fa-check-circle" title="ID & food handler's certificate verified"></i>}</h1>
              <p className="cpheadline">{chef.headline}</p>
              <div className="cpmeta">
                <span>
                  {chef.review_count ? (
                    <><i className="fas fa-star"></i> {rating(chef.avg_rating)} ({chef.review_count} review{pluralize(chef.review_count)})</>
                  ) : (
                    <><i className="fas fa-seedling"></i> New on Karamu</>
                  )}
                </span>
                <span><i className="fas fa-map-marker-alt"></i>{chef.area && `${chef.area}, `}{chef.city.name}</span>
                <span><i className="fas fa-utensils"></i>{chef.cuisine}</span>
                {chef.years_experience > 0 && <span><i className="fas fa-award"></i>{chef.years_experience} yr{pluralize(chef.years_experience)} experience</span>}
              </div>
              <div className="mktags mt-2">{chef.services.map((s) => <Link key={s.slug} href={serviceUrl(s.slug)}>{s.name}</Link>)}</div>
            </div>
          </div>
        </div>
      </section>

      <section className="cpmain">
        <div className="container">
          <ChosenPackage initial={String(booking.fields.find((f) => f.name === "package")?.value ?? "")}>
          <div className="row g-5">
            {/* LEFT: profile content */}
            <div className="col-lg-7">
              <div className="cpblock">
                <h4>About {chef.name}</h4>
                <p className="sdesc"><Lines text={chef.bio} /></p>
              </div>

              <div className="cpblock">
                <h4>Menu &amp; Packages</h4>
                {chef.packages.map((pkg) => (
                  <div key={pkg.id} className="pkgcard">
                    <div>
                      <div className="pkgnm">{pkg.name}</div>
                      <p><Lines text={pkg.description} /></p>
                    </div>
                    <div className="pkgside">
                      <div className="pkgprice">KSh {price(pkg.price)}<small>{pkg.price_unit}</small></div>
                      <PackageLink id={pkg.id} className="pkgbtn">Select</PackageLink>
                    </div>
                  </div>
                ))}
                {chef.packages.length === 0 && (
                  <p className="sdesc">{chef.name} creates custom menus. Send a booking request with your idea and they&apos;ll get back to you with a quote.</p>
                )}
              </div>

              {chef.photos.length > 0 && (
                <div className="cpblock">
                  <h4>Photos</h4>
                  <div className="cpgallery">
                    {chef.photos.map((photo) => <img key={photo.image} src={photo.image} alt={photo.caption} loading="lazy" />)}
                  </div>
                </div>
              )}

              <div className="cpblock" id="reviews">
                <h4>Reviews {chef.review_count > 0 && <span className="cprvsum"><i className="fas fa-star"></i> {rating(chef.avg_rating)} &middot; {chef.review_count}</span>}</h4>
                {reviews.map((review) => (
                  <div key={review.id} className="rvcard">
                    <div className="rvtop">
                      <strong>{review.customer_name}</strong>
                      <span className="rvstars">{[1, 2, 3, 4, 5].map((n) => <i key={n} className={`${n <= review.rating ? "fas" : "far"} fa-star`}></i>)}</span>
                    </div>
                    <p>{review.comment}</p>
                    <small>{dayMonthYear(review.created_at)}</small>
                  </div>
                ))}
                {reviews.length === 0 && <p className="sdesc">No reviews yet.</p>}
                {booking.booking_to_review ? (
                  <div className="rvform">
                    <h6>How was your {dayMonth(booking.booking_to_review.event_date)} booking?</h6>
                    <Link href={bookingUrl(booking.booking_to_review.id, "review/")} className="btn-red"><i className="fas fa-star"></i>Review {chef.name}</Link>
                  </div>
                ) : (
                  <p className="rvnote"><i className="fas fa-shield-alt"></i>Reviews come only from customers who booked {chef.name} through Karamu. We send you a review link after your booking.</p>
                )}
              </div>
            </div>

            {/* RIGHT: booking */}
            <div className="col-lg-5">
              <div className="fcard cpbook" id="book">
                <div className="cpbookprice">From <strong>KSh {price(chef.starting_price)}</strong> <small>{chef.price_unit}</small></div>
                <h4>Request a Booking</h4>
                {!chef.is_accepting_bookings ? (
                  <p className="cppaused"><i className="fas fa-pause-circle"></i>{chef.name} is not taking new bookings right now. <Link href={cityUrl(chef.city.slug)}>See other chefs in {chef.city.name}</Link> or WhatsApp us and we&apos;ll help.</p>
                ) : (
                  <>
                    <p className="cpbooknote"><i className="fas fa-shield-alt"></i> No payment now. {chef.name} confirms first, then you pay securely via M-Pesa.</p>
                    <AwayDates timeOff={chef.time_off} />
                    {!booking.logged_in && (
                      <p className="cplogin"><Link href={`/account/login/?next=${next}`}>Log in</Link> or <Link href={`/account/signup/?next=${next}`}>create an account</Link> to fill in your details and track this booking.</p>
                    )}
                    <BookingForm slug={chef.slug} fields={booking.fields} />
                  </>
                )}
              </div>
            </div>
          </div>
          </ChosenPackage>

          {similarChefs.length > 0 && (
            <div className="mt-5 pt-4">
              <h4 className="mb-4">More Chefs in {chef.city.name}</h4>
              <div className="row g-4">
                {similarChefs.map((c) => <div key={c.slug} className="col-sm-6 col-lg-4"><ChefCard chef={c} /></div>)}
              </div>
            </div>
          )}
        </div>
      </section>

      <WhatsAppFloat text={`Hi Karamu, I'm interested in booking ${chef.name}.`} />
    </>
  );
}
