import { describe, expect, test } from "bun:test";

import { ancestorCrumbs } from "@/features/rules/utils/crumbs";
import type { ManifestDirectory, ManifestNode } from "@/types/manifest";

function directory(
  name: string,
  path: string,
  children: ManifestNode[] = [],
): ManifestDirectory {
  return { type: "dir", name, path, mtime: 0, children };
}

const apple = directory("apple", "clash/domain/apple");
const domain = directory("domain", "clash/domain", [apple]);
const root = directory("clash", "clash", [domain]);

describe("ancestorCrumbs", () => {
  test("links every ancestor except the current node", () => {
    expect(ancestorCrumbs([root, domain, apple])).toEqual([
      { label: "Clash", to: "/clash/" },
      { label: "Domain", to: "/clash/domain/" },
    ]);
  });
});
