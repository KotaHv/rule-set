import { describe, expect, test } from "bun:test";

import {
  countLines,
  isCommentLine,
  previewDocument,
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

describe("previewDocument", () => {
  test("keeps raw content and formatted display separate", () => {
    const raw = '{"version":2,"rules":[]}';
    const document = previewDocument("config.json", raw);

    expect(document.content).toBe(raw);
    expect(document.display).toBe(`{
  "version": 2,
  "rules": []
}`);
    expect(document.lineCount).toBe(4);
  });

  test("leaves malformed JSON unchanged", () => {
    const raw = '{"rules":[}';
    const document = previewDocument("config.json", raw);

    expect(document.content).toBe(raw);
    expect(document.display).toBe(raw);
    expect(document.lineCount).toBe(1);
  });

  test("uses raw content when no formatting applies", () => {
    const raw = "payload:\n  - rule\n";
    const document = previewDocument("rules.yaml", raw);

    expect(document.content).toBe(raw);
    expect(document.display).toBe(raw);
    expect(document.lineCount).toBe(2);
  });
});

describe("isCommentLine", () => {
  test("recognizes hash and slash comments after indentation", () => {
    expect(isCommentLine("# Total: 58 rules")).toBe(true);
    expect(isCommentLine("  // temporary")).toBe(true);
  });

  test("does not treat a rule containing a hash or URL as a comment", () => {
    expect(isCommentLine("DOMAIN-SUFFIX,example.com # note")).toBe(false);
    expect(isCommentLine("https://example.com")).toBe(false);
  });
});
