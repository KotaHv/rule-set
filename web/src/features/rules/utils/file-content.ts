// Count without materializing an array: splitLines is only affordable
// below the large-file cutoff, but this runs before that decision.
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

export function prettyPrintJson(content: string): string {
  try {
    return JSON.stringify(JSON.parse(content), null, 2);
  } catch {
    return content;
  }
}
