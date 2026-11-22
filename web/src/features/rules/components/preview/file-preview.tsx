import { CodeView } from "./code-view";
import { PreviewLoading } from "./preview-loading";
import { PreviewUnavailable } from "./preview-unavailable";
import type { ManifestFile } from "@/types/manifest";
import type { FilePreviewState } from "@/types/preview";

interface FilePreviewViewProps {
  node: ManifestFile;
  preview: FilePreviewState;
  onRetry: () => void;
}

export function FilePreviewView({
  node,
  preview,
  onRetry,
}: FilePreviewViewProps) {
  if (preview.kind === "loading") {
    return <PreviewLoading name={node.name} />;
  }

  if (preview.kind === "text") {
    return <CodeView document={preview.document} name={node.name} />;
  }

  return (
    <PreviewUnavailable size={node.size} preview={preview} onRetry={onRetry} />
  );
}
