import { useRouteLoaderData } from "react-router";

import {
  MANIFEST_ROUTE_ID,
  type loadManifest,
} from "@/features/rules/api/manifest";
import type { Manifest } from "@/types/manifest";

export function useManifest(): Manifest {
  const manifest = useRouteLoaderData<typeof loadManifest>(MANIFEST_ROUTE_ID);

  // Undefined during the hydration window before the root loader resolves.
  // The static boot screen in index.html covers that frame; this is a guard.
  if (!manifest) {
    throw new Error("manifest 尚未加载");
  }

  return manifest;
}
