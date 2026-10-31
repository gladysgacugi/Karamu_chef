// The messages between a chef and a customer about a booking (Django: _booking_messages.html). Your own messages are on
// the right; the team sees the customer on the right.
import type { BookingMessage } from "@/lib/api";
import { dayMonthTime } from "@/lib/format";

export default function BookingMessages({ messages, chefName, customerName, viewer }: {
  messages: BookingMessage[];
  chefName: string;
  customerName: string;
  viewer: "chef" | "customer" | "team";
}) {
  const empty = {
    chef: "No messages yet. Ask about allergies, the menu or directions, or let them know you're on your way.",
    customer: `No messages yet. Ask ${chefName} about the menu, allergies or anything else.`,
    team: "No messages.",
  }[viewer];

  return (
    <div className="msgs" id="messages">
      {messages.length ? messages.map((msg) => (
        <div key={msg.id} className={`msg ${(viewer === "chef") === msg.from_chef ? "msg-me" : "msg-them"}`}>
          <span className="msgwho">{msg.from_chef ? chefName : customerName} &middot; {dayMonthTime(msg.created_at)}</span>
          <p style={{ whiteSpace: "pre-line" }}>{msg.body}</p>
        </div>
      )) : (
        <p className="msgempty">{empty}</p>
      )}
    </div>
  );
}
