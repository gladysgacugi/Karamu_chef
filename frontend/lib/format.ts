// The Django template filters the pages use, so both sites print values the same way.

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** {{ n|floatformat:"0g" }}, e.g. 12000 -> "12,000" */
export const price = (n: number) => Math.round(n).toLocaleString("en-US");

/** {{ n|floatformat:1 }} */
export const rating = (n: number | null) => (n ?? 0).toFixed(1);

/** {{ n|pluralize }} or {{ n|pluralize:"y,ies" }} */
export const pluralize = (n: number, plural = "s", singular = "") => (n === 1 ? singular : plural);

/** {{ s|truncatechars:n }} */
export const truncate = (s: string, n: number) => (s.length > n ? `${s.slice(0, n - 1)}…` : s);

// Dates are shown in UTC, Django's TIME_ZONE
const toDate = (value: string) => new Date(value.length === 10 ? `${value}T00:00:00Z` : value);

/** {{ d|date:"j M" }} */
export const dayMonth = (value: string) => {
  const d = toDate(value);
  return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]}`;
};

/** {{ d|date:"j M, H:i" }} */
export const dayMonthTime = (value: string) => {
  const d = toDate(value);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${dayMonth(value)}, ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`;
};

/** {{ d|date:"j M Y" }} */
export const dayMonthYear = (value: string) => `${dayMonth(value)} ${toDate(value).getUTCFullYear()}`;

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

/** {{ d|date:"D j M Y" }}, e.g. "Sat 7 Nov 2026" */
export const weekdayDate = (value: string) => `${WEEKDAYS[toDate(value).getUTCDay()]} ${dayMonthYear(value)}`;

/** {{ d|date:"D j M" }}, e.g. "Sat 7 Nov" */
export const weekdayDayMonth = (value: string) => `${WEEKDAYS[toDate(value).getUTCDay()]} ${dayMonth(value)}`;

/** {{ d|date:"j M Y, H:i" }} */
export const dayMonthYearTime = (value: string) => `${dayMonthYear(value)}, ${dayMonthTime(value).split(", ")[1]}`;

const TIME_UNITS: [string, number][] = [
  ["year", 365 * 86400], ["month", 30 * 86400], ["week", 7 * 86400], ["day", 86400], ["hour", 3600], ["minute", 60],
];

/** {{ d|timesince }}: the biggest unit and the next one down, e.g. "2 days, 3 hours" */
export function timesince(value: string) {
  let seconds = Math.max(0, (Date.now() - toDate(value).getTime()) / 1000);
  const start = TIME_UNITS.findIndex(([, size]) => seconds >= size);
  if (start === -1) return "0 minutes";
  const parts = [];
  for (const [name, size] of TIME_UNITS.slice(start, start + 2)) {
    const n = Math.floor(seconds / size);
    if (n === 0) break;
    parts.push(`${n} ${name}${pluralize(n)}`);
    seconds -= n * size;
  }
  return parts.join(", ");
}

/** A WhatsApp chat with a customer or chef, e.g. waLink("+254712345678", "Hi Grace") */
export const waLink = (phone: string, text: string) => `https://wa.me/${phone.replace("+", "")}?text=${encodeURIComponent(text)}`;

/** {{ d|date:"M Y" }} */
export const monthYear = (value: string) => {
  const d = toDate(value);
  return `${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
};

/** The first value of a query parameter (?a=1&a=2 gives "1"), or "" */
export const first = (value: string | string[] | undefined) => (Array.isArray(value) ? value[0] : value) ?? "";

/** "?key=..." to keep a booking's email key on links between its pages, or "" */
export const keyQuery = (key: string | string[] | undefined) => (first(key) ? `?key=${encodeURIComponent(first(key))}` : "");

// Model URLs (get_absolute_url), with the trailing slash Django's URLs have
export const chefUrl = (slug: string) => `/chefs/${slug}/`;
export const serviceUrl = (slug: string) => `/marketplace/?service=${slug}`;
export const cityUrl = (slug: string) => `/marketplace/?city=${slug}`;
export const bookingUrl = (id: number, page: "" | "pay/" | "review/" = "", key?: string | string[]) => `/bookings/${id}/${page}${keyQuery(key)}`;
