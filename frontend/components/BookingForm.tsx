"use client";

// The booking request form, on the chef's profile and on the booking page (Django: partials/booking_form.html).
// Picking a package elsewhere on the page fills in the form without reloading, so nothing typed is lost.
import { createContext, useContext, useState } from "react";
import DjangoForm from "@/components/DjangoForm";
import type { Field } from "@/lib/api";

const ChosenPackageContext = createContext<[string, (id: string) => void] | null>(null);

/** Wraps the part of the page with package links and the booking form, so they share the chosen package. */
export function ChosenPackage({ initial, children }: { initial: string; children: React.ReactNode }) {
  const state = useState(initial);
  return <ChosenPackageContext.Provider value={state}>{children}</ChosenPackageContext.Provider>;
}

/** A link that picks a package in the booking form. `onClass` is added while it is the one picked. */
export function PackageLink({ id, className, onClass, children }: {
  id: number;
  className: string;
  onClass?: string;
  children: React.ReactNode;
}) {
  const chosen = useContext(ChosenPackageContext);
  const isOn = onClass && chosen?.[0] === String(id);
  return (
    <a
      href={`?package=${id}#book`}
      className={isOn ? `${className} ${onClass}` : className}
      onClick={(e) => {
        const select = document.getElementById("id_package");
        if (!chosen || !select) return; // no form while the chef has paused bookings: just follow the link
        e.preventDefault();
        chosen[1](String(id));
        select.scrollIntoView({ behavior: "smooth", block: "center" });
      }}
    >
      {children}
    </a>
  );
}

export default function BookingForm({ slug, fields }: { slug: string; fields: Field[] }) {
  const chosen = useContext(ChosenPackageContext);
  return (
    <DjangoForm
      action={`/api/chefs/${encodeURIComponent(slug)}/booking/`}
      fields={fields}
      wide={["package", "location", "notes", "full_name"]}
      controlled={chosen ? { package: { value: chosen[0], onChange: chosen[1] } } : {}}
      icon="fa-calendar-check"
      button="Send Booking Request"
    />
  );
}
