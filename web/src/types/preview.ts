export type FilePreviewKind = "text" | "binary" | "too-large" | "error";

export interface FilePreview {
  kind: FilePreviewKind;
  content: string | null;
  error?: string;
}

export type FilePreviewState = { kind: "loading" } | FilePreview;
