import { data, type LoaderFunctionArgs } from "react-router";

import type { ManifestDirectory } from "@/types/manifest";
import { nodeTrail } from "../utils/tree";
import type { FilePageData } from "./file";
import { loadManifest } from "./manifest";

export const BROWSER_ROUTE_ID = "browser";

export interface DirectoryPageData {
  type: "directory";
  trail: ManifestDirectory[];
  node: ManifestDirectory;
}

export type BrowserPageData = DirectoryPageData | FilePageData;

export async function loadBrowserPage({
  params,
}: LoaderFunctionArgs): Promise<BrowserPageData> {
  const manifest = await loadManifest();
  const client = manifest.clients.find(
    (entry) => entry.slug === params.clientSlug,
  );
  const trail = client
    ? nodeTrail(client.root, params["*"] ?? "")
    : undefined;

  if (!trail) {
    throw data("页面不存在", { status: 404 });
  }

  const node = trail[trail.length - 1];

  if (node.type === "dir") {
    return { type: "directory", trail: trail as ManifestDirectory[], node };
  }

  return {
    type: "file",
    trail,
    node,
  };
}
