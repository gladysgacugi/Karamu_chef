// The homepage (Django: index.html), with its four forms.
import Link from "next/link";
import ChefApplicationForm from "@/components/ChefApplicationForm";
import ChefCard from "@/components/ChefCard";
import DjangoForm from "@/components/DjangoForm";
import SocialLinks from "@/components/SocialLinks";
import WhatsAppFloat from "@/components/WhatsAppFloat";
import { getChefs, getCities, getForm, getPackages, getReviews, getServices, getSite, getStats } from "@/lib/api";
import { cityUrl, pluralize, price, serviceUrl } from "@/lib/format";
import Aos from "./_home/Aos";
import CountUp from "./_home/CountUp";
import Gallery from "./_home/Gallery";
import PackageGrid from "./_home/PackageGrid";
import SearchOverlay from "./_home/SearchOverlay";
import SubscribeForm from "./_home/SubscribeForm";
import Testimonials from "./_home/Testimonials";

const MARQUEE = ["Nyama Choma", "Chicken Pilau", "Mukimo & Beef Stew", "Soft Layered Chapati", "Swahili Biryani", "Mandazi & Chai", "Private Chef Dinners"];

const STEPS = [
  { title: "Tell Us the Occasion", text: "Share the date, location, number of guests and the kind of food you love - private dinner, party, meal prep or a cooking class." },
  { title: "Pick Your Chef", text: "Compare verified chefs by cuisine, reviews and price, or let us match you with the best available chef near you." },
  { title: "Confirm & Pay with M-Pesa", text: "Your chef confirms their availability and agrees the menu with you. We then send you the M-Pesa payment details to lock in your booking." },
  { title: "Sit Back & Enjoy", text: "Your chef arrives, cooks fresh in your kitchen, serves and cleans up. Afterwards, rate your experience to help others choose." },
];

const OFFERS = [
  { icon: "fas fa-wine-glass-alt", title: "Private Dinners", text: "Couples, families & friends" },
  { icon: "fas fa-birthday-cake", title: "Parties & Events", text: "Birthdays, ruracio, office parties" },
  { icon: "fas fa-box-open", title: "Meal Prep", text: "Weekly home-cooked meals" },
];

const offerIcon = {
  width: 46, height: 46, borderRadius: 11, background: "rgba(181, 70, 42,.2)", display: "flex", alignItems: "center",
  justifyContent: "center", color: "var(--primary)", fontSize: "1.1rem", flexShrink: 0,
} as const;
const offerLabel = { display: "block", color: "#ccc", fontSize: ".78rem", textTransform: "uppercase", letterSpacing: ".8px" } as const;
const hoursHeading = { color: "#fff", marginBottom: 18, fontFamily: "'Poppins',sans-serif", fontSize: ".95rem", fontWeight: 700 } as const;
const gold = { color: "var(--secondary)" };

export default async function Home() {
  const [site, services, cities, featured, packagePage, reviewPage, stats, chefForm, matchForm, contactForm, subscribeForm] = await Promise.all([
    getSite(), getServices(), getCities(), getChefs({ featured: "1" }), getPackages(), getReviews({ min_rating: "4" }), getStats(),
    getForm("chef-applications/"), getForm("match-requests/"), getForm("contact/"), getForm("subscribe/"),
  ]);
  const featuredChefs = featured.results.slice(0, 4);
  const packages = packagePage.results.slice(0, 6);
  const reviews = reviewPage.results.slice(0, 8);
  // The services the packages shown belong to, in the usual service order
  const packageServices = services.filter((s) => packages.some((p) => p.service?.slug === s.slug));

  return (
    <>
      <SearchOverlay services={services} />

      {/* HERO */}
      <section id="hero">
        <div className="hs hs1"></div>
        <div className="hs hs2"></div>
        <div className="hbgtxt">CHEF</div>
        <div className="container">
          <div className="row align-items-center g-5" style={{ minHeight: "88vh" }}>
            <div className="col-lg-6">
              <div className="hbadge">
                <div className="hbi"><i className="fas fa-star"></i></div>
                <span>Kenya&apos;s Home-Chef Marketplace</span>
              </div>
              <h1 className="htitle">Your Chef is <span className="hl">One Tap</span><br />Away</h1>
              <p className="hdesc">Book a local chef to cook at your home, party or event, or to prep your family&apos;s meals for the week. Compare real menus and prices, send a request, and pay with M-Pesa once your chef confirms.</p>
              <div className="d-flex flex-wrap gap-3 mb-2">
                <a href="#menu" className="btn-red"><i className="fas fa-utensils"></i>See Chef Packages</a>
                <Link href="/marketplace" className="btn-play">
                  <div className="pico"><i className="fas fa-user-tie"></i></div>
                  <span>Find a Private Chef</span>
                </Link>
              </div>
              {stats.chefs > 0 && (
                <div className="hstats d-flex gap-3 flex-wrap mt-4">
                  <div className="hstat"><CountUp value={stats.chefs} /><small>Chef{pluralize(stats.chefs)} Live</small></div>
                  {stats.verified > 0 && (
                    <><div className="sdiv"></div>
                    <div className="hstat"><CountUp value={stats.verified} /><small>ID &amp; Certificate Checked</small></div></>
                  )}
                  {stats.packages > 0 && (
                    <><div className="sdiv"></div>
                    <div className="hstat"><CountUp value={stats.packages} /><small>Package{pluralize(stats.packages)} to Book</small></div></>
                  )}
                  <div className="sdiv"></div>
                  <div className="hstat"><CountUp value={stats.cities} /><small>Cit{pluralize(stats.cities, "ies", "y")}</small></div>
                </div>
              )}
            </div>
            <div className="col-lg-6">
              <div style={{ position: "relative", textAlign: "center" }}>
                <div className="hcircle">
                  <img src="/static/img/banner-img.jpg" alt="Home-cooked meal" />
                </div>
                <div className="fcard fc1">
                  <div className="fcoi r"><i className="fas fa-user-check"></i></div>
                  <div><span className="fcnum">Verified</span><span className="fcsm">Vetted local chefs</span></div>
                </div>
                <div className="fcard fc2">
                  <div className="fcoi y"><i className="fas fa-mobile-alt"></i></div>
                  <div><span className="fcnum">M-Pesa</span><span className="fcsm">Pay after confirmation</span></div>
                </div>
                <div className="fcard fc3">
                  <div className="fcoi g"><i className="fas fa-tags"></i></div>
                  <div><span className="fcnum">Clear Prices</span><span className="fcsm">See menus before you book</span></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* MARQUEE */}
      <div className="mqsec">
        <div className="mqtrack">
          {[...MARQUEE, ...MARQUEE].map((item, i) => (
            <div key={i} className="mqitem"><i className="fas fa-circle"></i>{item}</div>
          ))}
        </div>
      </div>

      {/* BROWSE BY SERVICE */}
      <section id="category">
        <div className="container">
          <div className="text-center mb-5" data-aos="fade-up">
            <span className="slbl">The Chef Marketplace</span>
            <h2 className="stitle">Browse by <span>Service</span></h2>
            <div className="sline"></div>
            <p className="sdesc mx-auto" style={{ maxWidth: 520 }}>Private chefs, caterers, meal prep and more. Compare real profiles, menus and prices, then book in minutes.</p>
          </div>
          <div className="row g-4">
            {services.map((service, i) => (
              <div key={service.slug} className="col-sm-6 col-lg-4" data-aos="fade-up" data-aos-delay={[0, 80, 160][i % 3]}>
                <Link href={serviceUrl(service.slug)} className="svcard">
                  <div className="svico"><i className={`fas ${service.icon}`}></i></div>
                  <div>
                    <div className="svnm">{service.name}</div>
                    <p className="svdesc">{service.description}</p>
                    <div className="svprice">From KSh {price(service.starting_price)} <small>{service.price_unit}</small></div>
                  </div>
                  <i className="fas fa-arrow-right svarrow"></i>
                </Link>
              </div>
            ))}
          </div>
          <div className="row g-4 mt-4">
            <div className="col-6 col-lg-3" data-aos="fade-up"><div className="whyitem"><i className="fas fa-id-badge"></i><strong>Real Profiles</strong><span>See menus, photos and prices before you book.</span></div></div>
            <div className="col-6 col-lg-3" data-aos="fade-up" data-aos-delay="80"><div className="whyitem"><i className="fas fa-star"></i><strong>Genuine Reviews</strong><span>Every review is checked by our team.</span></div></div>
            <div className="col-6 col-lg-3" data-aos="fade-up" data-aos-delay="160"><div className="whyitem"><i className="fas fa-mobile-alt"></i><strong>M-Pesa Payments</strong><span>Pay safely once your chef confirms.</span></div></div>
            <div className="col-6 col-lg-3" data-aos="fade-up" data-aos-delay="240"><div className="whyitem"><i className="fas fa-headset"></i><strong>Real Support</strong><span>Call or WhatsApp us any day of the week.</span></div></div>
          </div>
          <div className="text-center mt-5" data-aos="fade-up">
            <Link href="/marketplace" className="btn-red"><i className="fas fa-store"></i>Explore the Marketplace</Link>
          </div>
        </div>
      </section>

      {/* ABOUT */}
      <section id="about">
        <div className="container">
          <div className="row align-items-center g-5">
            <div className="col-lg-5" data-aos="fade-right">
              <div className="astack">
                <div className="aexp"><span className="anum">2</span><small>Ways to<br />Eat Well</small></div>
                <div className="amain"><img src="/static/img/about1.jpg" alt="Chef cooking" /></div>
                <div className="asm"><img src="/static/img/about2.jpg" alt="" /></div>
              </div>
            </div>
            <div className="col-lg-7" data-aos="fade-left">
              <span className="slbl">About Karamu</span>
              <h2 className="stitle text-start">Talented Local Chefs,<br /><span>One Simple Marketplace</span></h2>
              <div className="sline lft"></div>
              <p className="sdesc mb-4">Karamu connects you with skilled home chefs and professional cooks across Kenya. Want home-cooked meals for the week? Book a chef to prep them for you. Hosting a dinner, birthday or office event? Book a private chef who comes to you, shops for the ingredients and cooks on site.</p>
              <div className="mb-4">
                <div className="fti">
                  <div className="ftico r"><i className="fas fa-shopping-bag"></i></div>
                  <div>
                    <h6>Home-Cooked Meals &amp; Meal Prep</h6>
                    <p>Browse chefs near you, compare their menus and prices, and book home-cooked meals for your family or your week.</p>
                  </div>
                </div>
                <div className="fti">
                  <div className="ftico y"><i className="fas fa-concierge-bell"></i></div>
                  <div>
                    <h6>Book a Private Chef</h6>
                    <p>Hire a chef for private dinners, parties, corporate events, weekly meal prep or cooking classes, at your place.</p>
                  </div>
                </div>
                <div className="fti">
                  <div className="ftico g"><i className="fas fa-shield-alt"></i></div>
                  <div>
                    <h6>Verified Chefs &amp; Safe M-Pesa Payments</h6>
                    <p>Every chef sends us their national ID and food handler&apos;s certificate before their profile goes live. You pay with M-Pesa only after your chef confirms.</p>
                  </div>
                </div>
              </div>
              <div className="d-flex flex-wrap gap-3">
                <a href="#menu" className="btn-red"><i className="fas fa-book-open"></i>Browse Packages</a>
                <a href="#chefs" className="btn-red"><i className="fas fa-user-tie"></i>Meet the Chefs</a>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CHEF PACKAGES */}
      <section id="menu">
        <div className="container">
          <div className="text-center mb-5" data-aos="fade-up">
            <span className="slbl">Fresh From Our Chefs</span>
            <h2 className="stitle">Popular <span>Chef</span> Packages</h2>
            <div className="sline"></div>
            <p className="sdesc mx-auto" style={{ maxWidth: 520 }}>Real menus with real prices. Pick a package and send the chef a booking request. No payment until they confirm.</p>
          </div>
          <PackageGrid packages={packages} services={packageServices} />
          <div className="text-center mt-5"><Link href="/marketplace" className="btn-red"><i className="fas fa-th-large"></i>Browse All Chefs</Link></div>
        </div>
      </section>

      {/* SPECIAL OFFER */}
      <section id="special">
        <div className="spbg"></div>
        <div className="container" style={{ position: "relative", zIndex: 2 }}>
          <div className="row align-items-center g-5">
            <div className="col-lg-6" data-aos="fade-right">
              <div className="sptag"><i className="fas fa-calendar-alt me-1"></i>Hosting This Weekend?</div>
              <h2 className="sptitle">Let a<br /><span>Private Chef</span><br />Do the Cooking</h2>
              <p className="spdesc">Book a Karamu private chef for dinner with family or friends. They plan the menu, shop and cook at your place. You just enjoy the meal. Weekends fill up fast, so book at least 48 hours ahead.</p>
              <div className="d-flex flex-wrap gap-3">
                <Link href="/marketplace?service=private-chefs" className="btn-red"><i className="fas fa-user-tie"></i>Browse Private Chefs</Link>
                <a href="#reservation" className="btn-red"><i className="fas fa-calendar-check"></i>Help Me Choose</a>
              </div>
            </div>
            <div className="col-lg-6" data-aos="fade-left">
              <div className="spimgw">
                <div className="spglow"></div>
                <img src="/static/img/off-img.jpg" alt="Private chef dinner" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* GALLERY */}
      <section id="gallery">
        <div className="container">
          <div className="text-center mb-5" data-aos="fade-up">
            <span className="slbl">From Our Chefs&apos; Kitchens</span>
            <h2 className="stitle">Food Made With <span>Love</span></h2>
            <div className="sline"></div>
          </div>
          <Gallery />
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="history">
        <div className="container">
          <div className="text-center mb-5" data-aos="fade-up">
            <span className="slbl">How It Works</span>
            <h2 className="stitle">Book a Chef in <span>4 Easy Steps</span></h2>
            <div className="sline"></div>
            <p className="sdesc mx-auto" style={{ maxWidth: 480 }}>Whether it&apos;s a quiet dinner for two or a party for fifty, getting a great chef takes just a few taps.</p>
          </div>
          <div className="timeline" data-aos="fade-up">
            {STEPS.map((step, i) => {
              // The same text on both sides; the CSS shows one side per row
              const side = (
                <>
                  <div className="tlyear">Step {i + 1}</div>
                  <h5>{step.title}</h5>
                  <p>{step.text}</p>
                </>
              );
              return (
                <div key={step.title} className="tli">
                  <div className="tl-left">{side}</div>
                  <div className="tl-center"><div className="tldot"></div></div>
                  <div className="tl-right">{side}</div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* FEATURED CHEFS */}
      <section id="chefs">
        <div className="container">
          <div className="text-center mb-5" data-aos="fade-up">
            <span className="slbl">Our Chef Community</span>
            <h2 className="stitle">Meet Our Top <span>Chefs</span></h2>
            <div className="sline"></div>
          </div>
          <div className="row g-4">
            {featuredChefs.map((chef, i) => (
              <div key={chef.slug} className="col-sm-6 col-lg-3" data-aos="fade-up" data-aos-delay={[0, 80, 160, 240][i % 4]}>
                <ChefCard chef={chef} />
              </div>
            ))}
            {featuredChefs.length === 0 && (
              <div className="col-12 text-center"><p className="sdesc">Our first chefs are joining now. <a href="#hours">Are you a chef? Apply today.</a></p></div>
            )}
          </div>
          <div className="text-center mt-5"><Link href="/marketplace" className="btn-red"><i className="fas fa-user-tie"></i>Browse All Chefs</Link></div>
        </div>
      </section>

      {/* CHEFS BY CITY */}
      <section id="cities">
        <div className="container">
          <div className="text-center mb-5" data-aos="fade-up">
            <span className="slbl">Near You</span>
            <h2 className="stitle">Find Chefs in <span>Your City</span></h2>
            <div className="sline"></div>
          </div>
          <div className="citygrid" data-aos="fade-up">
            {cities.map((city) => (
              <Link key={city.slug} href={cityUrl(city.slug)} className="citylink"><i className="fas fa-map-marker-alt"></i>Chefs in {city.name}</Link>
            ))}
          </div>
          <div className="text-center mt-4"><Link href="/marketplace" className="blmore">Browse all chefs <i className="fas fa-arrow-right"></i></Link></div>
        </div>
      </section>

      {/* BECOME A CHEF */}
      <section id="hours">
        <div className="hrsbg"></div>
        <div className="container" style={{ position: "relative", zIndex: 2 }}>
          <div className="text-center mb-5" data-aos="fade-up">
            <span className="slbl" style={{ color: "#a5d6bc" }}>For Chefs</span>
            <h2 className="stitle" style={{ color: "#fff" }}>Cook. Earn. <span style={gold}>Grow.</span></h2>
            <div className="sline"></div>
            <p className="sdesc mx-auto" style={{ maxWidth: 520, color: "rgba(255,255,255,.7)" }}>Are you a professional chef or a talented home cook? Join Karamu, reach new customers and earn on your own schedule.</p>
          </div>
          <div className="row g-4 align-items-start">
            <div className="col-lg-5" data-aos="fade-right">
              <div className="hrscard">
                <h5 style={hoursHeading}><i className="fas fa-gift me-2" style={gold}></i>Why Join</h5>
                {[
                  ["fa-store", "Show your menus & prices online"],
                  ["fa-calendar-alt", "Get private chef & event bookings"],
                  ["fa-clock", "Set your own hours & prices"],
                  ["fa-mobile-alt", "Get paid via M-Pesa"],
                  ["fa-star", "Build your brand with reviews"],
                ].map(([icon, text]) => (
                  <div key={text} className="hrsrow">
                    <span className="hrsday"><i className={`fas ${icon} me-2`} style={gold}></i>{text}</span>
                    <div className="d-flex align-items-center gap-2"><div className="hdot on"></div></div>
                  </div>
                ))}
              </div>
            </div>
            <div className="col-lg-3" data-aos="zoom-in">
              <div className="hrscta">
                <i className="fas fa-user-plus fa-2x mb-3" style={{ color: "rgba(255,255,255,.8)" }}></i>
                <h4>Become a Chef</h4>
                <p>Apply in minutes. Once we&apos;ve checked your documents, you can start taking bookings.</p>
                <a href="#chefForm" className="btnw">Join Now &rarr;</a>
              </div>
            </div>
            <div className="col-lg-4" data-aos="fade-left">
              <div className="hrscard">
                <h5 style={hoursHeading}><i className="fas fa-clipboard-check me-2" style={gold}></i>What You Need</h5>
                {[
                  ["fa-id-card", "National ID", "Required"],
                  ["fa-file-medical", "Food Handler's Certificate", "Required"],
                  ["fa-mobile-alt", "M-Pesa Number", "For payouts"],
                  ["fa-camera", "Photos of Your Dishes", "3 - 5 photos"],
                ].map(([icon, text, note]) => (
                  <div key={text} className="hrsrow"><span className="hrsday"><i className={`fas ${icon} me-2`} style={gold}></i>{text}</span><span className="hrstime" style={{ fontSize: ".8rem" }}>{note}</span></div>
                ))}
              </div>
            </div>
          </div>
          <div className="row justify-content-center mt-5" id="chefForm">
            <div className="col-lg-10" data-aos="fade-up">
              <div className="fcard">
                <h4 style={{ fontSize: "1.3rem", marginBottom: 6 }}>Apply to Become a Chef</h4>
                <p style={{ color: "#888", fontSize: ".85rem", marginBottom: 22 }}>Fill in your details below. Our team reviews every application before your profile goes live.</p>
                <ChefApplicationForm fields={chefForm.fields} idPrefix="apply_" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* TESTIMONIALS */}
      {reviews.length > 0 && (
        <section id="testimonials">
          <div className="container">
            <div className="text-center mb-5" data-aos="fade-up">
              <span className="slbl">What People Say</span>
              <h2 className="stitle">Loved by Our <span>Customers</span></h2>
              <div className="sline"></div>
            </div>
            <Testimonials reviews={reviews} />
          </div>
        </section>
      )}

      {/* BOOK A CHEF */}
      <section id="reservation">
        <div className="container">
          <div className="text-center mb-5" data-aos="fade-up">
            <span className="slbl">Private Chef Service</span>
            <h2 className="stitle">Book a <span>Private Chef</span></h2>
            <div className="sline"></div>
            <p className="sdesc mx-auto" style={{ maxWidth: 480 }}>Tell us about your occasion and we&apos;ll match you with the right chef. For events and weekend bookings, we recommend booking at least 48 hours in advance.</p>
          </div>
          <div className="row g-4 align-items-start">
            <div className="col-lg-4" data-aos="fade-right">
              <div style={{ background: "var(--dark)", borderRadius: 18, padding: 36 }}>
                <h4 style={{ color: "#fff", fontSize: "1.3rem", marginBottom: 8 }}>What We Offer</h4>
                <p style={{ color: "rgba(255,255,255,.55)", fontSize: ".85rem", marginBottom: 26 }}>One chef, many occasions. We cook wherever you are in Nairobi and nearby areas.</p>
                <div className="d-flex flex-column gap-3">
                  {OFFERS.map((offer) => (
                    <div key={offer.title} className="d-flex align-items-center gap-3">
                      <div style={offerIcon}><i className={offer.icon}></i></div>
                      <div><strong style={offerLabel}>{offer.title}</strong><span style={{ color: "#fff", fontSize: ".87rem" }}>{offer.text}</span></div>
                    </div>
                  ))}
                  <div className="d-flex align-items-center gap-3">
                    <div style={offerIcon}><i className="fab fa-whatsapp"></i></div>
                    <div><strong style={offerLabel}>Call or WhatsApp</strong><a href={site.whatsapp_url} target="_blank" rel="noopener" style={{ color: "#fff", fontSize: ".87rem" }}>{site.whatsapp_display}</a></div>
                  </div>
                </div>
              </div>
            </div>
            <div className="col-lg-8" data-aos="fade-left">
              <div className="fcard">
                <DjangoForm action="/api/match-requests/" fields={matchForm.fields} idPrefix="match_" wide={["location", "notes"]} icon="fa-calendar-check" button="Request a Chef" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* NEWSLETTER */}
      <section id="newsletter">
        <div className="nlbg"></div>
        <div className="container">
          <div className="nlw text-center" data-aos="zoom-in">
            <span className="slbl" style={{ color: "rgba(255,255,255,.7)" }}>Stay Connected</span>
            <h2 className="mb-3" style={{ color: "#fff" }}>New Chefs &amp; <span style={gold}>Weekly Specials</span></h2>
            <p className="mb-4" style={{ color: "rgba(255,255,255,.78)" }}>Be the first to hear about new chefs, menus and specials near you.</p>
            <SubscribeForm email={subscribeForm.fields[0]} />
            <p style={{ color: "rgba(255,255,255,.45)", fontSize: ".76rem", marginTop: 11 }}><i className="fas fa-lock me-1"></i>No spam, unsubscribe anytime. See our <a href="/privacy/" style={{ color: "inherit", textDecoration: "underline" }}>privacy policy</a>.</p>
          </div>
        </div>
      </section>

      {/* CONTACT */}
      <section id="contact-section">
        <div className="container">
          <div className="text-center mb-5" data-aos="fade-up">
            <span className="slbl">Get In Touch</span>
            <h2 className="stitle">Contact <span>Us</span></h2>
            <div className="sline"></div>
            <p className="sdesc mx-auto" style={{ maxWidth: 480 }}>Have a question, planning an event, or want to join as a chef? We&apos;d love to hear from you.</p>
          </div>
          <div className="row g-4">
            <div className="col-lg-4" data-aos="fade-right">
              <div className="ctdark">
                <h4>Let&apos;s Talk</h4>
                <p className="ctsub">We reply as soon as we can, usually the same day.</p>
                <div className="ctitem">
                  <div className="cticon"><i className="fas fa-map-marker-alt"></i></div>
                  <div className="ctinfo"><strong>Location</strong><span>Nairobi, Kenya</span></div>
                </div>
                <div className="ctitem">
                  <div className="cticon"><i className="fas fa-phone-alt"></i></div>
                  <div className="ctinfo"><strong>Phone / WhatsApp</strong><span><a href={site.whatsapp_url} target="_blank" rel="noopener" style={{ color: "inherit" }}>{site.whatsapp_display}</a></span></div>
                </div>
                <div className="ctitem">
                  <div className="cticon"><i className="fas fa-envelope"></i></div>
                  <div className="ctinfo"><strong>Email</strong><span>hello@simplychefke.com</span></div>
                </div>
                <div className="ctitem">
                  <div className="cticon"><i className="fas fa-clock"></i></div>
                  <div className="ctinfo"><strong>Support Hours</strong><span>Mon - Sun: 7 AM - 10 PM</span></div>
                </div>
                {site.social_links.length > 0 && <div className="ctsocrow"><SocialLinks links={site.social_links} /></div>}
              </div>
            </div>
            <div className="col-lg-8" data-aos="fade-left">
              <div className="fcard">
                <DjangoForm action="/api/contact/" fields={contactForm.fields} idPrefix="contact_" wide={["message"]} icon="fa-paper-plane" button="Send Message" />
              </div>
            </div>
          </div>
        </div>
      </section>

      <WhatsAppFloat />
      <Aos />
    </>
  );
}
