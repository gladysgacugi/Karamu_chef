// Reads from the Django API (/api/). Every request is fresh, like the Django pages, so the two sites match while we compare.
// Forms are sent from the browser instead, see lib/client.ts.
import { headers } from "next/headers";
import { notFound, redirect } from "next/navigation";

export const DJANGO_URL = process.env.DJANGO_URL ?? "http://127.0.0.1:8000";

export type Service = {
  slug: string;
  name: string;
  description: string;
  icon: string;
  starting_price: number;
  price_unit: string;
};

export type City = { slug: string; name: string };

export type ChefCard = {
  slug: string;
  name: string;
  headline: string;
  photo: string;
  cuisine: string;
  city: City;
  area: string;
  services: Service[];
  years_experience: number;
  starting_price: number;
  price_unit: string;
  is_verified: boolean;
  is_featured: boolean;
  is_accepting_bookings: boolean;
  avg_rating: number | null;
  review_count: number;
};

export type Package = {
  id: number;
  name: string;
  description: string;
  price: number;
  price_unit: string;
  service: Service | null;
};

export type PackageWithChef = Package & {
  chef: { slug: string; name: string; city: string; photo: string; is_verified: boolean };
};

export type ChefDetail = ChefCard & {
  bio: string;
  cover: string;
  packages: Package[];
  photos: { image: string; caption: string }[];
  time_off: { start_date: string; end_date: string }[];
  is_active: boolean;
};

export type Review = {
  id: number;
  customer_name: string;
  rating: number;
  comment: string;
  created_at: string;
  chef: { slug: string; name: string };
};

export type Page<T> = { count: number; next: string | null; previous: string | null; results: T[] };

export type Stats = { chefs: number; verified: number; packages: number; cities: number };

export type Site = {
  whatsapp_url: string;
  whatsapp_display: string;
  mpesa_paybill: string;
  social_links: { icon: string; url: string }[];
};

/** A Django form field, as api_forms.form_fields describes it. */
export type Field = {
  name: string;
  label: string;
  type: string; // an <input> type (including "hidden"), "select", "textarea" or "checkboxes" (several choices)
  required: boolean;
  help_text: string;
  attrs: Record<string, string | number | boolean>;
  choices: [string, string][];
  value: string | boolean | string[]; // a list for "checkboxes"
  /** File fields: the file already saved ("" if none), and whether it can be removed */
  url?: string;
  clearable?: boolean;
};

/** A Django formset (api_forms.formset_json): its management fields and each form's fields. */
export type Formset = { management: Field[]; forms: Field[][] };

export type FormInfo = { fields: Field[] };

export type User = { first_name: string; email: string; is_staff: boolean; is_chef: boolean; home: string };

/** A booking as its customer sees it (CustomerBookingSerializer). */
export type Booking = {
  id: number;
  chef: { slug: string; name: string; photo: string };
  package: { name: string; price: number; price_unit: string } | null;
  full_name: string;
  phone: string;
  email: string;
  event_date: string;
  time_slot_display: string;
  guests: number;
  location: string;
  notes: string;
  status: "new" | "confirmed" | "completed" | "cancelled";
  status_display: string;
  price: number | null;
  payment_status: "unpaid" | "submitted" | "paid" | "refunded";
  payment_status_display: string;
  payment_reference: string;
  mpesa_code: string;
  paid_at: string | null;
  customer_can_cancel: boolean;
  customer_can_pay: boolean;
  can_be_reviewed: boolean;
  review_status: "pending" | "published" | "rejected" | null;
  messages: BookingMessage[];
};

export type BookingMessage = { id: number; from_chef: boolean; body: string; created_at: string };

export const PAGE_SIZE = 12; // MarketplacePagination.page_size

export class ApiNotFound extends Error {}
export class ApiForbidden extends Error {}

type Params = Record<string, string | string[] | undefined>;

/**
 * GET from the API. With `asVisitor`, the visitor's cookies are sent along, so Django sees who is logged in and which
 * bookings this browser made. Only for answers about the visitor themselves.
 */
async function get<T>(path: string, params: Params = {}, { asVisitor = false } = {}): Promise<T> {
  const url = new URL(`/api/${path}`, DJANGO_URL);
  for (const [key, value] of Object.entries(params)) {
    const first = Array.isArray(value) ? value[0] : value;
    if (first) url.searchParams.set(key, first);
  }
  const cookie = asVisitor ? (await headers()).get("cookie") : null;
  const res = await fetch(url, cookie ? { headers: { cookie } } : {});
  if (res.status === 404) throw new ApiNotFound(url.toString());
  if (res.status === 403) throw new ApiForbidden(url.toString());
  if (!res.ok) throw new Error(`${res.status} from ${url}`);
  return res.json();
}

/** A missing chef or booking shows the 404 page. */
async function orNotFound<T>(request: Promise<T>) {
  try {
    return await request;
  } catch (e) {
    if (e instanceof ApiNotFound) notFound();
    throw e;
  }
}

export const getSite = () => get<Site>("site/");
export const getStats = () => get<Stats>("stats/");
export const getServices = () => get<Service[]>("services/");
export const getCities = () => get<City[]>("cities/");
export const getPackages = () => get<Page<PackageWithChef>>("packages/");
export const getReviews = (params: { min_rating?: string } = {}) => get<Page<Review>>("reviews/", params);

export type ChefFilters = { service?: string; city?: string; q?: string; sort?: string; page?: string; featured?: string };

export function getChefs(filters: ChefFilters = {}) {
  return get<Page<ChefCard>>("chefs/", filters);
}

// Sent as the visitor, so chefs can preview their own profile before it goes live
export const getChef = (slug: string) =>
  orNotFound(get<ChefDetail>(`chefs/${encodeURIComponent(slug)}/`, {}, { asVisitor: true }));

export const getChefReviews = (slug: string, page = 1) =>
  get<Page<Review>>(`chefs/${encodeURIComponent(slug)}/reviews/`, { page: String(page) });

/** A page of the marketplace. Like Django's Paginator.get_page, a bad page number shows page 1 and one past the end shows the last page. */
export async function getChefsPage(filters: ChefFilters) {
  const number = Math.max(1, parseInt(filters.page ?? "", 10) || 1);
  try {
    return { page: await getChefs({ ...filters, page: String(number) }), number };
  } catch (e) {
    if (!(e instanceof ApiNotFound) || number === 1) throw e;
    const first = await getChefs({ ...filters, page: "1" });
    const last = Math.max(1, Math.ceil(first.count / PAGE_SIZE));
    return { page: last === 1 ? first : await getChefs({ ...filters, page: String(last) }), number: last };
  }
}

// The visitor: their login, bookings and forms

export const getMe = () => get<{ user: User | null }>("auth/me/", {}, { asVisitor: true }).then((r) => r.user);

/** A form to show (api_forms.py), e.g. getForm("contact/"). Its starting values can depend on who is logged in. */
export const getForm = <T extends object = object>(path: string, params: Params = {}) =>
  orNotFound(get<FormInfo & T>(path, params, { asVisitor: true }));

export type BookingFormInfo = {
  logged_in: boolean;
  is_own_profile: boolean;
  booking_to_review: { id: number; event_date: string } | null;
};

export const getBookingForm = (slug: string, chosenPackage?: string | string[]) =>
  getForm<BookingFormInfo>(`chefs/${encodeURIComponent(slug)}/booking/`, { package: chosenPackage });

/** One of the visitor's bookings. `key` comes from the links in our emails, for customers who aren't logged in. */
export const getBooking = (id: string, key?: string | string[]) =>
  orNotFound(get<Booking & { is_owner: boolean }>(`bookings/${encodeURIComponent(id)}/`, { key }, { asVisitor: true }));

/** The logged-in customer's bookings, or null when nobody is logged in. */
export async function getAccount() {
  try {
    return await get<{ user: User; bookings: Booking[] }>("account/", {}, { asVisitor: true });
  } catch (e) {
    if (e instanceof ApiForbidden) return null;
    throw e;
  }
}

// The chef dashboard (api_chef.py) and the team pages (api_team.py)

/**
 * A chef or team page's data. Its API path is the page's own path (/api/chef/availability/ for /chef/availability/).
 * Visitors who aren't logged in go to the login page and come back; anyone else who isn't allowed goes to their own home.
 */
async function getMemberPage<T>(path: string, params: Params) {
  try {
    return await orNotFound(get<T>(path, params, { asVisitor: true }));
  } catch (e) {
    if (!(e instanceof ApiForbidden)) throw e;
    const user = await getMe();
    redirect(user ? user.home : `/account/login/?next=${encodeURIComponent(`/${path}`)}`);
  }
}

export const getChefPage = <T>(path: string, params: Params = {}) => getMemberPage<T>(`chef/${path}`, params);
export const getTeamPage = <T>(path: string, params: Params = {}) => getMemberPage<T>(`team/${path}`, params);

/** The counts for the team menu's badges, or null for anyone who isn't on the team (the page sends them away). */
export async function getTeamWaiting() {
  try {
    return await get<Waiting>("team/waiting/", {}, { asVisitor: true });
  } catch (e) {
    if (e instanceof ApiForbidden) return null;
    throw e;
  }
}

/** The logged-in chef (OwnChefSerializer). */
export type OwnChef = {
  name: string;
  slug: string;
  photo: string;
  is_active: boolean;
  is_accepting_bookings: boolean;
  is_verified: boolean;
  documents_updated_at: string | null;
};

type BookingStatus = Booking["status"];

/** A booking as its chef sees it (ChefBookingSerializer). `phone` is "" until the chef confirms. */
export type ChefBooking = {
  id: number;
  full_name: string;
  phone: string;
  has_email: boolean;
  event_date: string;
  time_slot_display: string;
  guests: number;
  location: string;
  notes: string;
  package: Booking["package"];
  price: number | null;
  suggested_price: number | null;
  status: BookingStatus;
  status_display: string;
  payment_status: Booking["payment_status"];
  payment_status_display: string;
  next_statuses: BookingStatus[];
  created_at: string;
  message_count?: number;
};

/** [value, label, count] for each status tab */
export type StatusTabs = { status: string; status_tabs: [string, string, number][]; total: number };

export type ChefPage = { chef: OwnChef };
export type ChefFormPage = ChefPage & FormInfo;

export type TimeOff = { id: number; start_date: string; end_date: string; note: string };

/** A booking with everything the team sees (TeamBookingSerializer). */
export type TeamBooking = ChefBooking & {
  chef: { name: string; slug: string };
  email: string;
  customer_email: string | null;
  payment_reference: string;
  mpesa_code: string;
  paid_at: string | null;
  team_notes: string;
  reminder_sent_at: string | null;
  team_payment_actions: Booking["payment_status"][];
};

export type Waiting = { applications: number; bookings: number; payments: number; reviews: number; requests: number; inbox: number };

export type Application = {
  id: number;
  full_name: string;
  phone: string;
  email: string;
  location: string;
  chef_type_display: string;
  services_display: string;
  cuisine_display: string;
  years_experience: number;
  bio: string;
  status: "pending" | "approved" | "rejected";
  status_display: string;
  admin_notes: string;
  decision_message: string;
  created_at: string;
};

export type ApplicationDetail = Application & {
  national_id: string;
  food_handler_certificate: string;
  dish_photos: string[];
  chef: { id: number; name: string; slug: string; email: string; is_active: boolean; has_login: boolean } | null;
};

export type TeamChef = {
  id: number;
  slug: string;
  name: string;
  city: string;
  area: string;
  cuisine: string;
  phone: string;
  is_active: boolean;
  is_accepting_bookings: boolean;
  is_featured: boolean;
  is_verified: boolean;
  documents_updated_at: string | null;
  avg_rating: number | null;
  review_count: number;
  has_login: boolean;
  application_id: number | null;
  national_id: string;
  food_handler_certificate: string;
};

export type TeamReview = {
  id: number;
  customer_name: string;
  rating: number;
  comment: string;
  status: "pending" | "published" | "rejected";
  status_display: string;
  created_at: string;
  chef: string;
  booking: { id: number; payment_reference: string; event_date: string } | null;
};

export type MatchRequest = {
  id: number;
  full_name: string;
  phone: string;
  email: string;
  status: "new" | "matched" | "closed";
  status_display: string;
  occasion_display: string;
  guests_display: string;
  cuisine_display: string;
  event_date: string;
  time_slot_display: string;
  location: string;
  notes: string;
  created_at: string;
};

export type ContactMessage = {
  id: number;
  name: string;
  email: string;
  phone: string;
  subject_display: string;
  message: string;
  is_handled: boolean;
  created_at: string;
};

/** A team list with status tabs */
export type TeamList<T> = StatusTabs & { items: T[] };
