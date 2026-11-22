import { data, type LoaderFunctionArgs } from "react-router";

import type {
  ManifestClient,
  ManifestDirectory,
  ManifestFile,
} from "@/types/manifest";
import { nodeTrail } from "../utils/tree";
import { loadManifest } from "./manifest";

export const BROWSER_ROUTE_ID = "browser";

export interface DirectoryPageData {
  type: "directory";
  client: ManifestClient;
  trail: ManifestDirectory[];
  node: ManifestDirectory;
}

export interface FilePageData {
  type: "file";
  client: ManifestClient;
  trail: ManifestDirectory[];
  node: ManifestFile;
}

export type BrowserPageData = DirectoryPageData | FilePageData;

export async function loadBrowserPage({
  params,
}: LoaderFunctionArgs): Promise<BrowserPageData> {
  const manifest = await loadManifest();
  const client = manifest.clients.find(
    (entry) => entry.slug === params.clientSlug,
  );

  if (!client) {
    throw data("页面不存在", { status: 404 });
  }

  const result = nodeTrail(client.root, params["*"] ?? "");

  if (!result) {
    throw data("页面不存在", { status: 404 });
  }

  const { trail, node } = result;

  if (node.type === "dir") {
    return {
      type: "directory",
      client,
      trail,
      node,
    };
  }

  return {
    type: "file",
    client,
    trail,
    node,
  };
}
