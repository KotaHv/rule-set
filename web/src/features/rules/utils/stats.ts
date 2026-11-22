import type {
  ManifestClient,
  ManifestDirectory,
  ManifestNode,
} from "@/types/manifest";

export interface TreeStats {
  files: number;
  size: number;
}

function walk(node: ManifestNode, stats: TreeStats): void {
  if (node.type === "file") {
    stats.files += 1;
    stats.size += node.size;
    return;
  }

  for (const child of node.children) {
    walk(child, stats);
  }
}

export function treeStats(root: ManifestDirectory): TreeStats {
  const stats: TreeStats = { files: 0, size: 0 };
  walk(root, stats);
  return stats;
}

export function manifestStats(clients: ManifestClient[]): TreeStats {
  const stats: TreeStats = { files: 0, size: 0 };

  for (const client of clients) {
    const clientStats = treeStats(client.root);
    stats.files += clientStats.files;
    stats.size += clientStats.size;
  }

  return stats;
}
