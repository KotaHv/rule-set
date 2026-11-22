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
  test("links the home root and every provided ancestor", () => {
    expect(ancestorCrumbs([root, domain])).toEqual([
      { label: "Home", to: "/" },
      { label: "Clash", to: "/clash/" },
      { label: "Domain", to: "/clash/domain/" },
    ]);
  });
});
