import type { ClientSlug } from "@/types/manifest";

export const CLIENT_LABELS: Record<ClientSlug, string> = {
  clash: "Clash",
  egern: "Egern",
  geoip: "GeoIP",
  loon: "Loon",
  "sing-box": "Sing-Box",
  surge: "Surge",
};

export const CLIENT_SLUGS = Object.keys(
  CLIENT_LABELS,
) as readonly ClientSlug[];
