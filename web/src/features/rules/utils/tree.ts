import type { ManifestDirectory, ManifestFile } from "@/types/manifest";

export function directoryRoute(path: string): string {
  return path ? `/${path}/` : "/";
}

export function parentRoute(path: string): string {
  const parent = path.split("/").slice(0, -1).join("/");
  return directoryRoute(parent);
}

export function fileHref(path: string): string {
  const encoded = path.split("/").map(encodeURIComponent).join("/");
  return `${import.meta.env.BASE_URL}${encoded}`;
}

export function directoryTrail(
  root: ManifestDirectory,
  path: string,
): ManifestDirectory[] | undefined {
  const trail = [root];
  let node = root;

  for (const segment of path.split("/").filter(Boolean)) {
    const child = node.children.find(
      (entry): entry is ManifestDirectory =>
        entry.type === "dir" && entry.name === segment,
    );

    if (!child) {
      return undefined;
    }

    trail.push(child);
    node = child;
  }

  return trail;
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
