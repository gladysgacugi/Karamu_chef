"use client";

import type { ReactNode } from "react";
import { goTo, post } from "@/lib/client";

export async function logOut() {
  goTo((await post("/api/auth/logout/")).redirect ?? "/");
}

export default function LogoutButton({ className, title, children }: { className: string; title?: string; children: ReactNode }) {
  return <button type="button" className={className} title={title} onClick={logOut}>{children}</button>;
}
