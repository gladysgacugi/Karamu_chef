"use client";

// The message a form left for this page, e.g. "Your booking was cancelled." (Django: accounts/_messages.html)
import { useEffect, useState } from "react";
import { takeFlash } from "@/lib/client";

export default function Flash() {
  const [flash, setFlash] = useState<ReturnType<typeof takeFlash>>(null);
  useEffect(() => setFlash(takeFlash()), []);
  if (!flash) return null;
  return (
    <>
      {flash.message && (
        <div className={`acmsg${flash.isError ? " acmsg-err" : ""}`}>
          <i className={`fas ${flash.isError ? "fa-exclamation-circle" : "fa-check-circle"}`}></i>{flash.message}
        </div>
      )}
      {flash.warning && <div className="acmsg acmsg-err"><i className="fas fa-exclamation-circle"></i>{flash.warning}</div>}
    </>
  );
}
