"use client";

// The newsletter sign-up: one email box with the button beside it (Django: the #newsletter form in index.html).
import { useState } from "react";
import { Widget } from "@/components/DjangoForm";
import type { Field } from "@/lib/api";
import { post, type Answer } from "@/lib/client";

export default function SubscribeForm({ email }: { email: Field }) {
  const [answer, setAnswer] = useState<Answer>({});
  const [sending, setSending] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    setSending(true);
    const result = await post("/api/subscribe/", new FormData(form));
    setSending(false);
    setAnswer(result);
    if (!result.errors) form.reset();
  }

  const errors = Object.values(answer.errors ?? {}).flat();
  return (
    <>
      {answer.message && <p className="nlmsg"><i className="fas fa-check-circle me-1"></i>{answer.message}</p>}
      <form onSubmit={onSubmit} className="nl-form-wrap" noValidate>
        <Widget field={email} invalid={errors.length > 0} idPrefix="newsletter_" />
        <button type="submit" className="nlbtn" disabled={sending}><i className="fas fa-paper-plane me-1"></i>Subscribe</button>
      </form>
      {errors.map((error) => <p key={error} className="nlmsg nlerr">{error}</p>)}
    </>
  );
}
