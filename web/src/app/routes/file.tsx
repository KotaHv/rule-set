import type { FilePageData } from "@/features/rules/api/file";
import { FilePreviewView } from "@/features/rules/components/file-preview";
import { useFilePreview } from "@/features/rules/hooks/use-file-preview";

export function FilePage({ data }: { data: FilePageData }) {
  const { node } = data;
  const { preview, retry } = useFilePreview(node);

  return (
    <>
      <title>{`${node.name} - Rule Set`}</title>
      <div className="mx-auto max-w-6xl px-6 py-6 lg:px-8">
        <FilePreviewView node={node} preview={preview} onRetry={retry} />
      </div>
    </>
  );
}
