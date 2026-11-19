import type { ClientSlug } from "@/types/manifest";

export const CLIENT_META: Record<
  ClientSlug,
  { label: string; color: string }
> = {
  clash: { label: "Clash", color: "#3b82d6" },
  egern: { label: "Egern", color: "#4f7dff" },
  geoip: { label: "GeoIP", color: "#d4d4d4" },
  loon: { label: "Loon", color: "#8755ff" },
  "sing-box": { label: "Sing-Box", color: "#78909c" },
  surge: { label: "Surge", color: "#f45bb6" },
};

export const CLIENT_SLUGS = Object.keys(
  CLIENT_META,
) as readonly ClientSlug[];
