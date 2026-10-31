import Link from "next/link";
import { getServices, getSite } from "@/lib/api";
import { serviceUrl } from "@/lib/format";
import SocialLinks from "./SocialLinks";

export default async function Footer() {
  const [site, services] = await Promise.all([getSite(), getServices()]);
  return (
    <footer>
      <div className="container">
        <div className="row g-5">
          <div className="col-lg-4">
            <div className="fnm"><img src="/static/img/brand/karamu-mark.svg" alt="" />Karamu</div>
            <p className="fdesc">Kenya&apos;s marketplace for private chefs, caterers and meal prep. Find a chef, see their menu and book. Your chef is one tap away.</p>
            {site.social_links.length > 0 && <div className="fsoc"><SocialLinks links={site.social_links} /></div>}
          </div>
          <div className="col-sm-6 col-lg-2">
            <div className="ftit">Quick Links</div>
            <ul className="flinks ps-0">
              <li><Link href="/#hero"><i className="fas fa-chevron-right"></i>Home</Link></li>
              <li><Link href="/#about"><i className="fas fa-chevron-right"></i>About Us</Link></li>
              <li><Link href="/marketplace"><i className="fas fa-chevron-right"></i>Find a Chef</Link></li>
              <li><Link href="/#menu"><i className="fas fa-chevron-right"></i>Chef Packages</Link></li>
              <li><Link href="/#hours"><i className="fas fa-chevron-right"></i>Become a Chef</Link></li>
              <li><Link href="/#contact-section"><i className="fas fa-chevron-right"></i>Contact</Link></li>
            </ul>
          </div>
          <div className="col-sm-6 col-lg-2">
            <div className="ftit">Services</div>
            <ul className="flinks ps-0">
              {services.map((service) => (
                <li key={service.slug}><Link href={serviceUrl(service.slug)}><i className="fas fa-chevron-right"></i>{service.name}</Link></li>
              ))}
            </ul>
          </div>
          <div className="col-lg-4">
            <div className="ftit">Get In Touch</div>
            <div className="fci">
              <div className="fciico"><i className="fas fa-map-marker-alt"></i></div>
              <div className="fciinfo"><strong>Location</strong>Nairobi, Kenya</div>
            </div>
            <div className="fci">
              <div className="fciico"><i className="fas fa-phone-alt"></i></div>
              <div className="fciinfo"><strong>Phone / WhatsApp</strong><a href={site.whatsapp_url} target="_blank" rel="noopener">{site.whatsapp_display}</a></div>
            </div>
            <div className="fci">
              <div className="fciico"><i className="fas fa-envelope"></i></div>
              <div className="fciinfo"><strong>Email</strong>hello@simplychefke.com</div>
            </div>
            <div className="fci">
              <div className="fciico"><i className="fas fa-mobile-alt"></i></div>
              <div className="fciinfo"><strong>Payments</strong>M-Pesa accepted</div>
            </div>
          </div>
        </div>
      </div>
      <div className="fbot">
        <div className="container">
          <div className="d-flex justify-content-between align-items-center flex-wrap gap-2">
            <p>&copy; 2026 <span>Karamu</span>. All Rights Reserved.</p>
            <div><Link href="/privacy/">Privacy Policy</Link><Link href="/terms/">Terms</Link><Link href="/privacy/#cookies">Cookies</Link></div>
          </div>
        </div>
      </div>
    </footer>
  );
}
