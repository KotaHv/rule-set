import { data, type LoaderFunctionArgs } from "react-router";

import type { ManifestDirectory } from "@/types/manifest";
import { directoryTrail } from "../utils/tree";
import { loadManifest } from "./manifest";

export const DIRECTORY_ROUTE_ID = "directory";

export interface DirectoryPageData {
  trail: ManifestDirectory[];
  node: ManifestDirectory;
}

export async function loadDirectoryPage({
  params,
}: LoaderFunctionArgs): Promise<DirectoryPageData> {
  const manifest = await loadManifest();
  const client = manifest.clients.find(
    (entry) => entry.slug === params.clientSlug,
  );
  const trail = client
    ? directoryTrail(client.root, params["*"] ?? "")
    : undefined;

  if (!trail) {
    throw data("页面不存在", { status: 404 });
  }

  return { trail, node: trail[trail.length - 1] };
}
