import { describe, expect, test } from "bun:test";

import {
  manifestStats,
  treeStats,
} from "@/features/rules/utils/stats";
import type {
  ManifestClient,
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

function file(name: string, path: string, size: number): ManifestFile {
  return { type: "file", name, path, mtime: 0, size };
}

const yaml = file("ai.yaml", "clash/domain/ai.yaml", 1024);
const nested = directory("deep", "clash/domain/deep", [
  file("large.yaml", "clash/domain/deep/large.yaml", 2 * 1024 * 1024),
]);
const root = directory("clash", "clash", [
  directory("domain", "clash/domain", [yaml, nested]),
]);

describe("treeStats", () => {
  test("counts files and sizes recursively", () => {
    expect(treeStats(root)).toEqual({
      files: 2,
      size: 1024 + 2 * 1024 * 1024,
    });
  });

  test("ignores directories without files", () => {
    expect(treeStats(directory("empty", "empty"))).toEqual({
      files: 0,
      size: 0,
    });
  });
});

describe("manifestStats", () => {
  test("aggregates clients", () => {
    const clients: ManifestClient[] = [
      { slug: "clash", root },
      { slug: "surge", root: directory("surge", "surge", [yaml]) },
    ];

    expect(manifestStats(clients)).toEqual({
      files: 3,
      size: 1024 * 2 + 2 * 1024 * 1024,
    });
  });
});
