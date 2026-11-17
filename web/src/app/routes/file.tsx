import type { FilePageData } from "@/features/rules/api/file";
import {
  PreviewUnavailable,
  TextPreview,
} from "@/features/rules/components/preview";

export function FilePage({ data }: { data: FilePageData }) {
  const { node, kind, content, error } = data;

  return (
    <>
      <title>{`${node.name} - Rule Set`}</title>
      <div className="mx-auto max-w-6xl px-6 py-6 lg:px-8">
        {/* Remount on navigation so copy status and scroll reset. */}
        {kind === "text" && content !== null ? (
          <TextPreview
            key={node.path}
            name={node.name}
            path={node.path}
            size={node.size}
            content={content}
          />
        ) : (
          <PreviewUnavailable
            name={node.name}
            path={node.path}
            size={node.size}
            kind={kind === "text" ? "error" : kind}
            error={kind === "text" ? "无法读取文件内容" : error}
          />
        )}
      </div>
    </>
  );
}
