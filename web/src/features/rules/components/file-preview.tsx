import {
  PreviewLoading,
  PreviewUnavailable,
  TextPreview,
} from "@/features/rules/components/preview";
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
    return <PreviewLoading name={node.name} size={node.size} />;
  }

  if (preview.kind === "text" && preview.content !== null) {
    return (
      <TextPreview
        name={node.name}
        path={node.path}
        size={node.size}
        content={preview.content}
      />
    );
  }

  return (
    <PreviewUnavailable
      name={node.name}
      path={node.path}
      size={node.size}
      kind={preview.kind === "text" ? "error" : preview.kind}
      error={preview.kind === "text" ? "无法读取文件内容" : preview.error}
      onRetry={preview.kind === "error" ? onRetry : undefined}
    />
  );
}
