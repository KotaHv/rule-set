import type { Manifest, ManifestClient } from "@/types/manifest";
import { CLIENT_SLUGS } from "../constants";

const MANIFEST_URL = `${import.meta.env.BASE_URL}manifest.json`;

export const MANIFEST_ROUTE_ID = "manifest";

export class ManifestHttpError extends Error {
  readonly status: number;

  constructor(status: number) {
    super(`Manifest request failed: HTTP ${status}`);
    this.name = "ManifestHttpError";
    this.status = status;
  }
}

let manifest: Manifest | undefined;
let manifestRequest: Promise<Manifest> | undefined;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isClient(value: unknown): value is ManifestClient {
  return (
    isRecord(value) &&
    typeof value.slug === "string" &&
    isRecord(value.root) &&
    value.root.type === "dir"
  );
}

function isManifest(value: unknown): value is Manifest {
  if (
    !isRecord(value) ||
    value.version !== 1 ||
    typeof value.latestUpdate !== "number" ||
    !Array.isArray(value.clients)
  ) {
    return false;
  }

  const clients = value.clients.filter(isClient);
  if (clients.length !== value.clients.length) {
    return false;
  }

  const slugs = new Set(clients.map((client) => client.slug));
  return (
    slugs.size === CLIENT_SLUGS.length &&
    CLIENT_SLUGS.every((slug) => slugs.has(slug))
  );
}

async function fetchManifest(): Promise<Manifest> {
  const response = await fetch(MANIFEST_URL, { cache: "no-cache" });
  if (!response.ok) {
    throw new ManifestHttpError(response.status);
  }

  const data: unknown = await response.json();
  if (!isManifest(data)) {
    throw new Error("Invalid manifest payload");
  }

  return data;
}

// The root and directory loaders run together, and the manifest does not
// change until the next full page load.
export function loadManifest(): Promise<Manifest> {
  if (manifest) {
    return Promise.resolve(manifest);
  }

  manifestRequest ??= fetchManifest()
    .then((data) => {
      manifest = data;
      return data;
    })
    .finally(() => {
      manifestRequest = undefined;
    });

  return manifestRequest;
}
