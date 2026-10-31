# Karamu - Next.js frontend

Next.js is the whole website; Django is the backend behind it (the API, admin, uploads and emails).

- Phase 2: the homepage, marketplace and chef profiles, built on the Django API (`/api/`).
- Phase 3: the customer forms and accounts: booking, payment, reviews, sign-up, login, password reset, my bookings,
  the chef application and the homepage forms (find me a chef, contact, newsletter).
- Phase 4: the chef dashboard (`/chef/`, API `/api/chef/`), the team pages (`/team/`, API `/api/team/`), and the
  privacy and terms pages. The site is no longer an installable app: `/sw.js` now only removes the old app's service
  worker from phones that installed it.

Only Django admin (`/admin/`) is still a Django page. Next.js forwards it to Django, so it opens on the same address
and uses the same login.

## Run it next to Django

```sh
# Terminal 1, project root
python manage.py runserver 8000

# Terminal 2, this folder
npm install
npm run dev        # http://localhost:3000
```

Use the whole site from http://localhost:3000. The URLs are the Django ones (`/marketplace/`, `/account/login/`,
`/bookings/12/?key=...`), so links in emails work on both sites.

Set `DJANGO_URL` if Django runs somewhere else (default `http://127.0.0.1:8000`). Emails link to the website at
Django's `SITE_URL` (default `http://127.0.0.1:3000`); set it to the real address when the site goes live. Password
reset emails use the address the reset was asked from.

## How it fits together

- **One address**: `next.config.ts` serves the pages Next.js has and forwards everything else to Django (`fallback`
  rewrites): `/api/`, `/admin/`, `/static/`, `/media/`. The browser only ever talks to Next.js, so
  Django's session and CSRF cookies work for both. Django trusts the forwarded address (`USE_X_FORWARDED_HOST`) for its
  CSRF check and email links.
- **Reading data**: `lib/api.ts` fetches the API on the server, fresh on every request. Requests about the visitor
  (who is logged in, their bookings, form starting values) send the visitor's cookies along.
- **Forms**: Django still does the checking and saving. `SimplyChefKe/api_forms.py` wraps the same Django forms:
  `GET` describes the fields, `POST` saves or returns the errors. `components/DjangoForm.tsx` renders the fields the way
  the templates do and posts them from the browser with the CSRF token (`lib/client.ts`). After a form, the next page
  shows its message, like Django's messages (`components/Flash.tsx`). One-button actions (confirm a booking, publish a
  review, put a chef live) use `components/ActionForm.tsx`.
- **Layouts**: the website pages are in `app/(site)/` with the top bar, navbar and footer. The team pages
  (`app/team/`) have their own phone-friendly layout with a bottom menu.
- **Look**: the CSS, fonts, scripts and images are the Django ones, so there is one copy.
- **Behaviour**: `main.js` and the inline script in `base.html` became small client components (`components/SiteScripts.tsx`,
  `app/_home/*`). Bootstrap, AOS and Swiper load from Django's `/static/js/`.
