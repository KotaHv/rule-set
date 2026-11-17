import { describe, expect, test } from "bun:test";

import {
  fileExtension,
  formatFileSize,
  formatName,
} from "@/utils/format";

describe("formatName", () => {
  test.each<[string, string]>([
    ["geoip", "GeoIP"],
    ["cn-ip", "CN-IP"],
    ["CN-IP", "CN-IP"],
    ["ipcidr", "IPCIDR"],
    ["sing-box", "Sing-Box"],
    ["CLASH", "Clash"],
    ["cn-域名", "Cn-域名"],
  ])("formats %s as %s", (name, expected) => {
    expect(formatName(name)).toBe(expected);
  });
});

describe("fileExtension", () => {
  test.each<[string, string | undefined]>([
    ["ai.yaml", "yaml"],
    ["archive.tar.gz", "gz"],
    ["Makefile", undefined],
    [".env", undefined],
  ])("extracts the extension from %s", (name, expected) => {
    expect(fileExtension(name)).toBe(expected);
  });
});

describe("formatFileSize", () => {
  test.each<[number, string]>([
    [0, "0 B"],
    [1023, "1023 B"],
    [1024, "1.0 KB"],
    [1024 * 1024, "1.0 MB"],
  ])("formats %i bytes as %s", (size, expected) => {
    expect(formatFileSize(size)).toBe(expected);
  });
});
