// Sending forms to the Django API from the browser. Requests go to this site's /api/, which Next.js forwards to Django
// (next.config.ts), so the login session and CSRF cookies are the Django site's own.

export type Errors = Record<string, string[]>;

/** What the API answers: 400 {errors}, or 200 with a message to show, a warning to show with it and/or a page to go to. */
export type Answer = { errors?: Errors; message?: string; warning?: string | null; redirect?: string };

const SOMETHING_WRONG: Answer = {
  errors: { __all__: ["Something went wrong. Please try again, or WhatsApp us if it keeps happening."] },
};

function csrfToken() {
  return document.cookie.match(/(?:^|;\s*)csrftoken=([^;]*)/)?.[1];
}

export async function post(path: string, body?: FormData): Promise<Answer> {
  try {
    if (!csrfToken()) await fetch("/api/auth/me/"); // sets the cookie
    const res = await fetch(path, { method: "POST", body, headers: { "X-CSRFToken": csrfToken() ?? "" } });
    if (res.ok || res.status === 400) return await res.json();
    return SOMETHING_WRONG;
  } catch {
    return SOMETHING_WRONG;
  }
}

export type Flash = { message: string; isError: boolean; warning?: string | null };

/** Go to a page after a form, showing its message there (Django's messages.success + redirect). */
export function goTo(url: string, message?: string, isError = false, warning?: string | null) {
  if (message || warning) {
    try {
      sessionStorage.setItem(FLASH_KEY, JSON.stringify({ message: message ?? "", isError, warning } satisfies Flash));
    } catch {
      // the message is lost, the page still loads
    }
  }
  // A full page load, so the navbar and every page show the new login and booking state. The browser only scrolls for
  // a link to this same page with a #section, so that reloads.
  const target = new URL(url, window.location.href);
  if (target.pathname + target.search === window.location.pathname + window.location.search) {
    window.history.replaceState(null, "", target);
    window.location.reload();
  } else {
    window.location.assign(target);
  }
}

/** Reload this page showing the answer's message, or its first error. For buttons that change something and stay. */
export function reloadWith(answer: Answer) {
  const error = answer.errors && Object.values(answer.errors)[0]?.[0];
  goTo(answer.redirect ?? window.location.pathname + window.location.search, error ?? answer.message, !!error, answer.warning);
}

const FLASH_KEY = "flash";

/** The message left by goTo, shown once. */
export function takeFlash(): Flash | null {
  try {
    const flash = sessionStorage.getItem(FLASH_KEY);
    sessionStorage.removeItem(FLASH_KEY);
    return flash ? JSON.parse(flash) : null;
  } catch {
    return null;
  }
}
