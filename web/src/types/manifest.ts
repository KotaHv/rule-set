export type ClientSlug =
  | "clash"
  | "egern"
  | "geoip"
  | "loon"
  | "sing-box"
  | "surge";

export interface ManifestFile {
  type: "file";
  name: string;
  path: string;
  mtime: number;
  size: number;
}

export interface ManifestDirectory {
  type: "dir";
  name: string;
  path: string;
  mtime: number;
  children: ManifestNode[];
}

export type ManifestNode = ManifestDirectory | ManifestFile;

export interface ManifestClient {
  slug: ClientSlug;
  root: ManifestDirectory;
}

export interface Manifest {
  version: 1;
  latestUpdate: number;
  clients: ManifestClient[];
}
