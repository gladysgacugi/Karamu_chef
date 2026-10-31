import { getSite } from "@/lib/api";
import SocialLinks from "./SocialLinks";

export default async function Topbar() {
  const site = await getSite();
  return (
    <div id="topbar">
      <div className="container">
        <div className="d-flex justify-content-between align-items-center flex-wrap gap-2">
          <div className="top-contact d-flex flex-wrap">
            <span><a href={site.whatsapp_url} target="_blank" rel="noopener" className="tcwa"><i className="fab fa-whatsapp"></i>{site.whatsapp_display}</a></span>
            <span><i className="fas fa-envelope"></i>hello@simplychefke.com</span>
            <span><i className="fas fa-map-marker-alt"></i>Nairobi, Kenya</span>
          </div>
          <div className="d-flex align-items-center gap-3">
            <span className="ttag"><i className="fas fa-mobile-alt me-1"></i>Pay easily with M-Pesa</span>
            {site.social_links.length > 0 && <div className="tsoc"><SocialLinks links={site.social_links} /></div>}
          </div>
        </div>
      </div>
    </div>
  );
}
