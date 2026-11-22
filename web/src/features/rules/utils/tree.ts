import type {
  ManifestDirectory,
  ManifestFile,
  ManifestNode,
} from "@/types/manifest";

function encodePath(path: string): string {
  return path.split("/").map(encodeURIComponent).join("/");
}

export function directoryRoute(path: string): string {
  return path ? `/${encodePath(path)}/` : "/";
}

export function parentRoute(path: string): string {
  const parent = path.split("/").slice(0, -1).join("/");
  return directoryRoute(parent);
}

export function fileHref(path: string): string {
  return `${import.meta.env.BASE_URL}${encodePath(path)}`;
}

export function fileUrl(path: string): string {
  return new URL(fileHref(path), window.location.href).href;
}

export function fileRoute(path: string): string {
  return `/${encodePath(path)}`;
}

/**
 * Resolves a manifest path.
 * Directory hits include the current directory as the last trail entry;
 * file hits include only the ancestor directories.
 */
export function nodeTrail(
  root: ManifestDirectory,
  path: string,
): { trail: ManifestDirectory[]; node: ManifestNode } | undefined {
  const trail: ManifestDirectory[] = [root];
  const segments = path.split("/").filter(Boolean);
  let directory = root;

  for (const [index, segment] of segments.entries()) {
    const child = directory.children.find((entry) => entry.name === segment);

    if (!child) {
      return undefined;
    }

    if (child.type === "file") {
      return index === segments.length - 1 ? { trail, node: child } : undefined;
    }

    trail.push(child);
    directory = child;
  }

  return { trail, node: directory };
}

export function splitChildren(node: ManifestDirectory): {
  directories: ManifestDirectory[];
  files: ManifestFile[];
} {
  return {
    directories: node.children.filter(
      (child): child is ManifestDirectory => child.type === "dir",
    ),
    files: node.children.filter(
      (child): child is ManifestFile => child.type === "file",
    ),
  };
}
