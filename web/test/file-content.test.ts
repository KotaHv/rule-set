import { describe, expect, test } from "bun:test";

import {
  countLines,
  prettyPrintJson,
  splitLines,
} from "@/features/rules/utils/file-content";

interface LineFixture {
  name: string;
  content: string;
  count: number;
  lines: string[];
}

const fixtures: LineFixture[] = [
  {
    name: "empty content",
    content: "",
    count: 0,
    lines: [],
  },
  {
    name: "single line without a newline",
    content: "alpha",
    count: 1,
    lines: ["alpha"],
  },
  {
    name: "LF-separated lines",
    content: "alpha\nbeta",
    count: 2,
    lines: ["alpha", "beta"],
  },
  {
    name: "CRLF-separated lines",
    content: "alpha\r\nbeta",
    count: 2,
    lines: ["alpha", "beta"],
  },
  {
    name: "lone CR-separated lines",
    content: "alpha\rbeta",
    count: 2,
    lines: ["alpha", "beta"],
  },
  {
    name: "mixed line endings",
    content: "alpha\r\nbeta\rgamma\ndelta",
    count: 4,
    lines: ["alpha", "beta", "gamma", "delta"],
  },
  {
    name: "trailing LF is not an extra line",
    content: "alpha\n",
    count: 1,
    lines: ["alpha"],
  },
  {
    name: "trailing CRLF is not an extra line",
    content: "alpha\r\n",
    count: 1,
    lines: ["alpha"],
  },
  {
    name: "trailing lone CR is not an extra line",
    content: "alpha\r",
    count: 1,
    lines: ["alpha"],
  },
  {
    name: "blank lines are counted",
    content: "alpha\n\nbeta",
    count: 3,
    lines: ["alpha", "", "beta"],
  },
  {
    name: "only a newline is one empty line",
    content: "\n",
    count: 1,
    lines: [""],
  },
  {
    name: "only CRLF is one empty line",
    content: "\r\n",
    count: 1,
    lines: [""],
  },
  {
    name: "only a lone CR is one empty line",
    content: "\r",
    count: 1,
    lines: [""],
  },
  {
    name: "two newlines are two empty lines",
    content: "\n\n",
    count: 2,
    lines: ["", ""],
  },
];

describe("file content line semantics", () => {
  for (const fixture of fixtures) {
    test(fixture.name, () => {
      expect(countLines(fixture.content)).toBe(fixture.count);
      expect(splitLines(fixture.content)).toEqual(fixture.lines);
      expect(splitLines(fixture.content)).toHaveLength(fixture.count);
    });
  }
});

describe("prettyPrintJson", () => {
  test("pretty-prints valid JSON with two-space indentation", () => {
    expect(prettyPrintJson('{"version":2,"rules":[]}')).toBe(`{
  "version": 2,
  "rules": []
}`);
  });

  test("returns malformed JSON unchanged", () => {
    const malformed = '{"rules":[}';
    expect(prettyPrintJson(malformed)).toBe(malformed);
  });
});
