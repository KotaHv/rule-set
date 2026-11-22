import { describe, expect, test } from "bun:test";

import {
  directoryRoute,
  fileRoute,
  nodeTrail,
  parentRoute,
  splitChildren,
} from "@/features/rules/utils/tree";
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

const appleYaml = file(
  "apple-cn.yaml",
  "clash/domain/apple/apple-cn.yaml",
);
const apple = directory("apple", "clash/domain/apple", [appleYaml]);
const microsoft = directory("microsoft", "clash/domain/microsoft");
const domain = directory("domain", "clash/domain", [apple, microsoft]);
const ipcidr = directory("ipcidr", "clash/ipcidr");
const domainYaml = file("domain.yaml", "clash/domain.yaml");
const root = directory("clash", "clash", [domain, ipcidr, domainYaml]);

describe("nodeTrail", () => {
  test("resolves files without including the file in trail", () => {
    expect(nodeTrail(root, "domain/apple/apple-cn.yaml")).toEqual({
      trail: [root, domain, apple],
      node: appleYaml,
    });
    expect(nodeTrail(root, "domain.yaml")).toEqual({
      trail: [root],
      node: domainYaml,
    });
  });

  test("resolves directories with the current directory in trail", () => {
    expect(nodeTrail(root, "")).toEqual({ trail: [root], node: root });
    expect(nodeTrail(root, "/")).toEqual({ trail: [root], node: root });
    expect(nodeTrail(root, "domain/apple")).toEqual({
      trail: [root, domain, apple],
      node: apple,
    });
  });

  test("ignores empty and trailing segments", () => {
    expect(nodeTrail(root, "/domain//apple/")).toEqual({
      trail: [root, domain, apple],
      node: apple,
    });
  });

  test("rejects segments after a file", () => {
    expect(nodeTrail(root, "domain.yaml/child")).toBeUndefined();
  });

  test("returns undefined for unknown paths", () => {
    expect(nodeTrail(root, "domain/unknown")).toBeUndefined();
  });
});

describe("directoryRoute", () => {
  test("encodes special characters in each segment", () => {
    expect(directoryRoute("clash/domain/a b/#?")).toBe(
      "/clash/domain/a%20b/%23%3F/",
    );
    expect(parentRoute("clash/domain/a b/#?/file.yaml")).toBe(
      "/clash/domain/a%20b/%23%3F/",
    );
  });
});

describe("fileRoute", () => {
  test("routes nested files by path", () => {
    expect(fileRoute("clash/domain/apple/apple-cn.yaml")).toBe(
      "/clash/domain/apple/apple-cn.yaml",
    );
  });

  test("routes root files by path", () => {
    expect(fileRoute("clash/domain.yaml")).toBe("/clash/domain.yaml");
  });

  test("encodes special characters in each segment", () => {
    expect(fileRoute("clash/domain/a b/#?.yaml")).toBe(
      "/clash/domain/a%20b/%23%3F.yaml",
    );
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
