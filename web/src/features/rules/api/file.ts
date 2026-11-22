import type { ManifestFile } from "@/types/manifest";
import type { FilePreviewPayload } from "@/types/preview";
import { fileExtension } from "@/utils/format";
import { MAX_PREVIEW_BYTES } from "../constants";
import { fileHref } from "../utils/tree";

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

export async function readFilePreview(
  node: ManifestFile,
  signal?: AbortSignal,
): Promise<FilePreviewPayload> {
  const extension = fileExtension(node.name)?.toLowerCase();
  if (!extension || !TEXT_EXTENSIONS.has(extension)) {
    return { kind: "binary" };
  }
  if (node.size > MAX_PREVIEW_BYTES) {
    return { kind: "too-large" };
  }

  try {
    const response = await fetch(`${fileHref(node.path)}?v=${node.mtime}`, {
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
      error: error instanceof Error ? error.message : "未知错误",
    };
  }
}
