import type { ManifestNode } from "@/types/manifest";
import { formatName } from "@/utils/format";

import { directoryRoute } from "./tree";

export interface Crumb {
  label: string;
  to?: string;
}

export function ancestorCrumbs(trail: ManifestNode[]): Crumb[] {
  return trail.slice(0, -1).map((entry) => ({
    label: formatName(entry.name),
    to: directoryRoute(entry.path),
  }));
}
