import type { ManifestFile, ManifestNode } from "@/types/manifest";
import type { FilePreview, FilePreviewKind } from "@/types/preview";
import { fileExtension } from "@/utils/format";
import { fileHref } from "../utils/tree";

export const MAX_PREVIEW_BYTES = 20 * 1024 * 1024;

const TEXT_EXTENSIONS = new Set([
  "conf",
  "csv",
  "css",
  "html",
  "ini",
  "js",
  "json",
  "list",
  "md",
  "sh",
  "toml",
  "ts",
  "txt",
  "xml",
  "yaml",
  "yml",
]);

export interface FilePageData {
  type: "file";
  trail: ManifestNode[];
  node: ManifestFile;
}

export async function readFilePreview(
  node: ManifestFile,
  signal?: AbortSignal,
): Promise<FilePreview> {
  const extension = fileExtension(node.name)?.toLowerCase();
  let kind: FilePreviewKind = "text";
  if (!extension || !TEXT_EXTENSIONS.has(extension)) {
    kind = "binary";
  } else if (node.size > MAX_PREVIEW_BYTES) {
    kind = "too-large";
  }

  if (kind !== "text") {
    return { kind, content: null };
  }

  try {
    const response = await fetch(fileHref(node.path), {
      cache: "no-cache",
      signal,
    });

    if (!response.ok) {
      throw new Error(`请求失败（HTTP ${response.status}）`);
    }

    const content = (await response.text()).replace(/^\uFEFF/, "");
    return { kind: "text", content };
  } catch (error) {
    if (signal?.aborted) {
      throw error;
    }

    return {
      kind: "error",
      content: null,
      error: error instanceof Error ? error.message : "未知错误",
    };
  }
}
