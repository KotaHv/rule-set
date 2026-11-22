export interface PreviewDocument {
  /** Raw file content, used for copying. */
  content: string;
  /** Formatted content, used for rendering. */
  display: string;
  lineCount: number;
}

export type FilePreviewPayload =
  | { kind: "text"; content: string }
  | { kind: "binary" }
  | { kind: "too-large" }
  | { kind: "error"; error: string };

export type FilePreview =
  | { kind: "text"; document: PreviewDocument }
  | { kind: "binary" }
  | { kind: "too-large" }
  | { kind: "error"; error: string };

export type FilePreviewKind = FilePreview["kind"];

export type FilePreviewState = { kind: "loading" } | FilePreview;
