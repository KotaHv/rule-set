import type { PreviewDocument } from "@/types/preview";
import { fileExtension } from "@/utils/format";

// Count without materializing an array.
export function countLines(content: string): number {
  if (!content) {
    return 0;
  }

  let count = 1;
  for (let index = 0; index < content.length; index += 1) {
    const code = content.charCodeAt(index);
    if (code === 10) {
      count += 1;
    } else if (code === 13) {
      count += 1;
      if (content.charCodeAt(index + 1) === 10) {
        index += 1;
      }
    }
  }

  return content.endsWith("\n") || content.endsWith("\r") ? count - 1 : count;
}

export function splitLines(content: string): string[] {
  const normalized = content.replace(/\r\n?/g, "\n");
  if (!normalized) {
    return [];
  }
  const withoutTrailingNewline = normalized.endsWith("\n")
    ? normalized.slice(0, -1)
    : normalized;
  return withoutTrailingNewline.split("\n");
}

function prettyPrintJson(content: string): string {
  try {
    return JSON.stringify(JSON.parse(content), null, 2);
  } catch {
    return content;
  }
}

function formatPreviewContent(name: string, content: string): string {
  return fileExtension(name)?.toLowerCase() === "json"
    ? prettyPrintJson(content)
    : content;
}

export function previewDocument(
  name: string,
  content: string,
): PreviewDocument {
  const display = formatPreviewContent(name, content);
  return {
    content,
    display,
    lineCount: countLines(display),
  };
}

export function isCommentLine(line: string): boolean {
  return /^\s*(#|\/\/)/.test(line);
}
