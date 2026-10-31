// Django: pages/terms.html
import type { Metadata } from "next";
import Link from "next/link";
import { getSite } from "@/lib/api";

export const metadata: Metadata = {
  title: "Terms of Use | Karamu",
  description: "The terms for booking a chef and cooking with Karamu.",
};

export default async function Terms() {
  const site = await getSite();
  return (
    <section className="lgwrap">
      <div className="container">
        <div className="lgcard fcard">
          <span className="slbl">Karamu</span>
          <h1 className="actitle">Terms of <span>Use</span></h1>
          <p className="lgupdated">Last updated: 29 October 2026</p>

          <p>These terms apply when you use the Karamu website, whether you are booking a chef or cooking as one. By using the site you agree to them. Please also read our <Link href="/privacy/">Privacy Policy</Link>.</p>

          <h2>What Karamu does</h2>
          <p>Karamu is a marketplace. We help customers find and book independent chefs and home cooks. Chefs are not our employees. Each chef is responsible for the food and service they provide.</p>

          <h2>Booking a chef</h2>
          <ul>
            <li>Sending a booking request does not guarantee the booking. It is confirmed only when the chef accepts it.</li>
            <li>You can only book a chef on dates and times they are available. Chefs mark the days they are away, and a time already booked by another customer cannot be booked again.</li>
            <li>Prices on a chef&apos;s profile are starting prices. The final price can depend on your menu, number of guests, location and ingredients. The chef sets the price when they confirm, and we show it to you before you pay.</li>
            <li>Tell the chef about allergies and dietary needs in your request. The chef will do their best to accommodate them, but cannot guarantee a kitchen free of any allergen.</li>
          </ul>

          <h2>Paying for your booking</h2>
          <ul>
            <li>You pay by M-Pesa after the chef confirms, using the Paybill and account number on your booking&apos;s payment page. Then you enter your M-Pesa code so we can match your payment. Your booking is paid once we have checked it, and we email you a confirmation.</li>
            <li>Only pay using the details on your booking page on this website. Never pay anyone who contacts you claiming to be from Karamu without checking with us on our official WhatsApp number first: <a href={site.whatsapp_url} target="_blank" rel="noopener">{site.whatsapp_display}</a>.</li>
            <li>Please pay before the day of your booking. A chef may not be able to buy ingredients for an unpaid booking.</li>
          </ul>

          <h2>Changes, cancellations and refunds</h2>
          <p>You can cancel a request online from <strong>My bookings</strong> while it is still waiting for the chef to confirm. Once it is confirmed, contact us to change or cancel it and we will work it out with the chef. If you have already paid and cancel with enough notice for the chef to avoid costs, we refund you in full. If the chef has already bought ingredients or turned down other work for your date, we will agree a fair partial refund with you.</p>
          <p>A chef may cancel if they are unable to attend. If that happens after you have paid, we refund you in full by M-Pesa to the number on your booking, or help you find another chef if you prefer.</p>

          <h2>Reviews</h2>
          <p>Only customers with a completed booking can leave a review, once per booking. Reviews must be honest and about your own experience. Our team checks every review before it is published, and may decline reviews that are abusive, off-topic, share private information, or appear fake. Chefs cannot pay for, edit or remove reviews.</p>

          <h2>For chefs</h2>
          <ul>
            <li>The information and documents you submit must be true and your own. You must hold a valid food handler&apos;s certificate and follow good food hygiene.</li>
            <li>You set your own menus and prices, and must honour bookings you confirm at the price you set.</li>
            <li>Keep your availability up to date. Add time off for days you can&apos;t cook, and pause new bookings when you are fully booked.</li>
            <li>We may hide or remove a profile that breaks these terms or receives serious complaints.</li>
          </ul>

          <h2>Using the site</h2>
          <p>Do not misuse the site. That includes posting false information, harassing chefs or customers, or trying to take bookings found through Karamu off the platform in order to avoid these terms.</p>

          <h2>Liability</h2>
          <p>We work hard to check chefs before they go live, but we cannot guarantee every meal or event. To the extent the law allows, Karamu is not liable for losses caused by a chef&apos;s or customer&apos;s actions. Nothing in these terms limits rights you have under Kenyan consumer protection law.</p>

          <h2>Changes and contact</h2>
          <p>We may update these terms and will change the date above when we do. These terms are governed by the laws of Kenya. Questions? Email <a href="mailto:hello@simplychefke.com">hello@simplychefke.com</a>.</p>
        </div>
      </div>
    </section>
  );
}
