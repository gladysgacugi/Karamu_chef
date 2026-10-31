import type { Site } from "@/lib/api";

export default function SocialLinks({ links }: { links: Site["social_links"] }) {
  return links.map(({ icon, url }) => (
    <a key={icon} href={url} target="_blank" rel="noopener" aria-label={icon.replaceAll("-f", "")}>
      <i className={`fab fa-${icon}`}></i>
    </a>
  ));
}
