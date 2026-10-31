"use client";

// A small form that changes one thing and reloads the page with the answer's message, like the Django pages' one-button
// forms (confirm a booking, publish a review, put a chef live...). The inputs and button are its children.
import { useState, type ReactNode } from "react";
import { post, reloadWith } from "@/lib/client";

export default function ActionForm({ action, confirm: question, className, children }: {
  /** The API endpoint, e.g. "/api/team/reviews/3/status/" */
  action: string;
  /** Asked first, e.g. "Hide this chef from the marketplace?" */
  confirm?: string;
  className?: string;
  children: ReactNode;
}) {
  const [sending, setSending] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (question && !window.confirm(question)) return;
    setSending(true);
    reloadWith(await post(action, new FormData(e.currentTarget)));
  }

  return (
    <form onSubmit={onSubmit} className={className}>
      <fieldset disabled={sending} style={{ display: "contents" }}>{children}</fieldset>
    </form>
  );
}
