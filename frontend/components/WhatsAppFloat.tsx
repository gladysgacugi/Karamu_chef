import { getSite } from "@/lib/api";

export default async function WhatsAppFloat({ text = "Hi Karamu, I'd like to know more about your chefs." }: { text?: string }) {
  const site = await getSite();
  return (
    <a className="wafl" href={`${site.whatsapp_url}?text=${encodeURIComponent(text)}`} target="_blank" rel="noopener" aria-label="Chat with us on WhatsApp">
      <i className="fab fa-whatsapp"></i>
    </a>
  );
}
