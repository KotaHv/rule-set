import type { ManifestDirectory } from "@/types/manifest";
import { formatName } from "@/utils/format";

import { directoryRoute } from "./tree";

export interface Crumb {
  label: string;
  to?: string;
}

export function ancestorCrumbs(trail: ManifestDirectory[]): Crumb[] {
  return [
    { label: "Home", to: "/" },
    ...trail.map((entry) => ({
      label: formatName(entry.name),
      to: directoryRoute(entry.path),
    })),
  ];
}
