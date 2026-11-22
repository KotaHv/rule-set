import { RotateCwIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { MAX_PREVIEW_BYTES } from "@/features/rules/constants";
import type { FilePreview } from "@/types/preview";
import { formatFileSize } from "@/utils/format";
import { PreviewPanel } from "./preview-panel";

type UnavailablePreview = Exclude<FilePreview, { kind: "text" }>;
type UnavailableKind = UnavailablePreview["kind"];

const UNAVAILABLE_COPY: Record<
  UnavailableKind,
  { title: string; description: (size: number, error?: string) => string }
> = {
  binary: {
    title: "无法预览此文件",
    description: () => "该文件为二进制格式，请下载后查看。",
  },
  "too-large": {
    title: "文件过大，暂不预览",
    description: (size) =>
      `文件大小 ${formatFileSize(size)}，超过 ${formatFileSize(MAX_PREVIEW_BYTES)} 的在线预览限制，请下载后查看。`,
  },
  error: {
    title: "读取文件失败",
    description: (_size, error) => error ?? "请稍后重试，或下载文件后查看。",
  },
};

interface PreviewUnavailableProps {
  size: number;
  preview: UnavailablePreview;
  onRetry: () => void;
}

export function PreviewUnavailable({
  size,
  preview,
  onRetry,
}: PreviewUnavailableProps) {
  const copy = UNAVAILABLE_COPY[preview.kind];
  const description = copy.description(
    size,
    preview.kind === "error" ? preview.error : undefined,
  );

  return (
    <PreviewPanel className="flex h-full flex-col items-center justify-center px-5 py-10 text-center lg:h-auto">
      <h2 className="text-xl font-semibold text-stone-100">{copy.title}</h2>
      <p className="mt-2 max-w-prose text-sm leading-6 text-stone-400">
        {description}
      </p>
      {preview.kind === "error" && (
        <Button variant="secondary" className="mt-6" onClick={onRetry}>
          <RotateCwIcon aria-hidden="true" />
          重试
        </Button>
      )}
    </PreviewPanel>
  );
}
