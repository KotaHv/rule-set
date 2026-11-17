import { Database } from "bun:sqlite";
import { existsSync, mkdirSync, readdirSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";

import {
  type Manifest,
  type ManifestDirectory,
  type ManifestNode,
} from "../src/types/manifest.ts";
import { CLIENT_SLUGS } from "../src/features/rules/constants.ts";

const WEB_DIR = path.resolve(import.meta.dirname, "..");
const PROJECT_DIR = path.resolve(WEB_DIR, "..");
const RULE_SET_DIR = path.join(PROJECT_DIR, "rule-set");
const METADATA_PATH = path.join(PROJECT_DIR, ".metadata.db");
const OUTPUT_PATH = path.join(WEB_DIR, "public", "manifest.json");

const EXCLUDED_NAMES = new Set([
  "assets",
  "icons",
  "index.html",
  "manifest.json",
]);

function readMetadata(): Map<string, number> {
  const timestamps = new Map<string, number>();

  if (!existsSync(METADATA_PATH)) {
    throw new Error(
      `Metadata database not found: ${path.relative(PROJECT_DIR, METADATA_PATH)}. Run "uv run rule-set" first.`,
    );
  }

  const database = new Database(METADATA_PATH, { readonly: true });
  try {
    const rows = database
      .query("SELECT path, timestamp FROM metadata")
      .all() as Array<{ path: string; timestamp: number }>;

    for (const row of rows) {
      timestamps.set(row.path, row.timestamp);
    }
  } finally {
    database.close();
  }

  return timestamps;
}

function compareNodes(left: ManifestNode, right: ManifestNode): number {
  if (left.type !== right.type) {
    return left.type === "dir" ? -1 : 1;
  }
  if (left.name < right.name) {
    return -1;
  }
  if (left.name > right.name) {
    return 1;
  }
  return 0;
}

function scanDirectory(
  directory: string,
  relativePath: string,
  timestamps: Map<string, number>,
): ManifestDirectory {
  const children: ManifestNode[] = [];

  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    if (entry.name.startsWith(".") || EXCLUDED_NAMES.has(entry.name)) {
      continue;
    }

    const absolutePath = path.join(directory, entry.name);
    const childPath = path.posix.join(relativePath, entry.name);

    if (entry.isDirectory()) {
      children.push(scanDirectory(absolutePath, childPath, timestamps));
      continue;
    }

    if (!entry.isFile()) {
      continue;
    }

    const mtime = timestamps.get(childPath);
    if (mtime === undefined) {
      throw new Error(
        `Metadata entry not found for ${childPath}. Run "uv run rule-set" first.`,
      );
    }

    const stats = statSync(absolutePath);
    children.push({
      type: "file",
      name: entry.name,
      path: childPath,
      size: stats.size,
      mtime,
    });
  }

  children.sort(compareNodes);

  return {
    type: "dir",
    name: path.basename(directory),
    path: relativePath,
    mtime: children.reduce((latest, child) => {
      return Math.max(latest, child.mtime);
    }, 0),
    children,
  };
}

function countNodes(node: ManifestNode): { directories: number; files: number } {
  if (node.type === "file") {
    return { directories: 0, files: 1 };
  }

  return node.children.reduce(
    (total, child) => {
      const counts = countNodes(child);
      return {
        directories: total.directories + counts.directories,
        files: total.files + counts.files,
      };
    },
    { directories: 1, files: 0 },
  );
}

if (!existsSync(RULE_SET_DIR)) {
  throw new Error(
    `Rule set directory not found: ${RULE_SET_DIR}. Run "uv run rule-set" first.`,
  );
}

const timestamps = readMetadata();
const clientSlugs = new Set<string>(CLIENT_SLUGS);
const ignoredDirectories = readdirSync(RULE_SET_DIR, { withFileTypes: true })
  .filter(
    (entry) =>
      entry.isDirectory() &&
      !entry.name.startsWith(".") &&
      !EXCLUDED_NAMES.has(entry.name) &&
      !clientSlugs.has(entry.name),
  )
  .map((entry) => entry.name);

if (ignoredDirectories.length > 0) {
  console.warn(
    `Warning: ignoring non-client directories: ${ignoredDirectories.join(", ")}`,
  );
}

const clients = CLIENT_SLUGS.map((slug) => {
  const directory = path.join(RULE_SET_DIR, slug);

  if (!existsSync(directory) || !statSync(directory).isDirectory()) {
    throw new Error(`Client directory not found: rule-set/${slug}`);
  }

  return {
    slug,
    root: scanDirectory(directory, slug, timestamps),
  };
});

const manifest: Manifest = {
  version: 1,
  latestUpdate: clients.reduce(
    (latest, client) => Math.max(latest, client.root.mtime),
    0,
  ),
  clients,
};

mkdirSync(path.dirname(OUTPUT_PATH), { recursive: true });
writeFileSync(OUTPUT_PATH, `${JSON.stringify(manifest)}\n`);

const counts = clients.reduce(
  (total, client) => {
    const current = countNodes(client.root);
    return {
      directories: total.directories + current.directories,
      files: total.files + current.files,
    };
  },
  { directories: 0, files: 0 },
);
console.log(
  `Generated ${path.relative(PROJECT_DIR, OUTPUT_PATH)}: ${clients.length} clients, ${counts.directories} directories, ${counts.files} files`,
);
