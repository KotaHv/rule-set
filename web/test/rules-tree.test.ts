import { describe, expect, test } from "bun:test";

import { directoryTrail, splitChildren } from "@/features/rules/utils/tree";
import type {
  ManifestDirectory,
  ManifestFile,
  ManifestNode,
} from "@/types/manifest";

function directory(
  name: string,
  path: string,
  children: ManifestNode[] = [],
): ManifestDirectory {
  return { type: "dir", name, path, mtime: 0, children };
}

function file(name: string, path: string): ManifestFile {
  return { type: "file", name, path, mtime: 0, size: 0 };
}

const apple = directory("apple", "clash/domain/apple", [
  file("apple-cn.yaml", "clash/domain/apple/apple-cn.yaml"),
]);
const microsoft = directory("microsoft", "clash/domain/microsoft");
const domain = directory("domain", "clash/domain", [apple, microsoft]);
const ipcidr = directory("ipcidr", "clash/ipcidr");
const domainYaml = file("domain.yaml", "clash/domain.yaml");
const root = directory("clash", "clash", [domain, ipcidr, domainYaml]);

describe("directoryTrail", () => {
  test("returns the root for an empty path", () => {
    expect(directoryTrail(root, "")).toEqual([root]);
    expect(directoryTrail(root, "/")).toEqual([root]);
  });

  test("resolves nested directories", () => {
    expect(directoryTrail(root, "domain/apple")).toEqual([root, domain, apple]);
  });

  test("ignores empty and trailing segments", () => {
    expect(directoryTrail(root, "/domain//apple/")).toEqual([
      root,
      domain,
      apple,
    ]);
  });

  test("returns undefined for unknown directories", () => {
    expect(directoryTrail(root, "domain/unknown")).toBeUndefined();
  });

  test("does not resolve files", () => {
    expect(directoryTrail(root, "domain.yaml")).toBeUndefined();
  });
});

describe("splitChildren", () => {
  test("separates directories and files", () => {
    expect(splitChildren(root)).toEqual({
      directories: [domain, ipcidr],
      files: [domainYaml],
    });
  });

  test("preserves the order of each group", () => {
    expect(splitChildren(domain).directories).toEqual([apple, microsoft]);
  });

  test("returns empty arrays for an empty directory", () => {
    const empty = directory("empty", "empty");

    expect(splitChildren(empty)).toEqual({ directories: [], files: [] });
  });
});
