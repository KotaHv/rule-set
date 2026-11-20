import { useEffect, useMemo, useState } from "react";
import {
  CheckIcon,
  CopyIcon,
  DownloadIcon,
  ExternalLinkIcon,
  FileIcon,
  LinkIcon,
  RotateCwIcon,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { MAX_PREVIEW_BYTES } from "@/features/rules/api/file";
import {
  countLines,
  prettyPrintJson,
  splitLines,
} from "@/features/rules/utils/file-content";
import { fileHref } from "@/features/rules/utils/tree";
import { fileExtension, formatFileSize } from "@/utils/format";

type CopyStatus = "copied" | "error";

const LARGE_FILE_LINES = 10000;

const SKELETON_WIDTHS = [
  "w-11/12",
  "w-7/12",
  "w-10/12",
  "w-5/12",
  "w-9/12",
  "w-6/12",
] as const;

function useCopyStatus() {
  const [status, setStatus] = useState<CopyStatus | null>(null);

  useEffect(() => {
    if (!status) {
      return;
    }

    const timer = window.setTimeout(() => setStatus(null), 2000);
    return () => window.clearTimeout(timer);
  }, [status]);

  return [status, setStatus] as const;
}

interface TextPreviewProps {
  name: string;
  path: string;
  size: number;
  content: string;
}

export function TextPreview({ name, path, size, content }: TextPreviewProps) {
  const extension = fileExtension(name);
  const displayContent = useMemo(
    () =>
      extension?.toLowerCase() === "json" ? prettyPrintJson(content) : content,
    [content, extension],
  );
  const lineCount = useMemo(() => countLines(displayContent), [displayContent]);
  const large = lineCount > LARGE_FILE_LINES;
  const lines = useMemo(
    () => (large ? [] : splitLines(displayContent)),
    [displayContent, large],
  );

  return (
    <section className="overflow-hidden rounded-xl border border-white/10 bg-white/3.5 shadow-xl shadow-black/20 backdrop-blur-sm">
      <PreviewToolbar
        content={content}
        extension={extension}
        path={path}
        size={size}
        lineCount={lineCount}
      />

      <TextPreviewContent
        content={displayContent}
        large={large}
        lineCount={lineCount}
        lines={lines}
        name={name}
      />
    </section>
  );
}

interface TextPreviewContentProps {
  name: string;
  content: string;
  lines: string[];
  large: boolean;
  lineCount: number;
}

function TextPreviewContent({
  name,
  content,
  lines,
  large,
  lineCount,
}: TextPreviewContentProps) {
  if (lineCount === 0) {
    return (
      <p className="px-4 py-16 text-center text-sm text-stone-400">
        这是一个空文件
      </p>
    );
  }

  return (
    <div
      className="max-h-[calc(100dvh-12rem)] overflow-x-hidden overflow-y-auto overscroll-contain md:overflow-auto"
      role="region"
      aria-label={`${name} 文件内容`}
      tabIndex={0}
    >
      {large ? (
        <pre className="min-w-full px-4 py-3 font-mono text-[13px] leading-6 text-stone-300 tab-4 whitespace-pre-wrap break-all md:w-max md:whitespace-pre">
          {content}
        </pre>
      ) : (
        <pre className="min-w-full py-3 font-mono text-[13px] leading-6 text-stone-300 tab-4 whitespace-pre-wrap break-all md:w-max md:whitespace-pre">
          <code className="block">
            {lines.map((line, index) => (
              <span key={index} className="group/line flex">
                <span
                  aria-hidden="true"
                  className="sticky left-0 z-10 w-14 shrink-0 select-none border-r border-white/10 bg-stone-950/95 pr-3 text-right text-stone-400 group-hover/line:text-stone-200"
                >
                  {index + 1}
                </span>
                <span className="min-w-0 flex-1 whitespace-pre-wrap break-all px-4 text-stone-300 group-hover/line:bg-white/3.5 md:flex-none md:whitespace-pre">
                  {line || " "}
                </span>
              </span>
            ))}
          </code>
        </pre>
      )}
    </div>
  );
}

export function PreviewLoading({ name, size }: { name: string; size: number }) {
  const extension = fileExtension(name);

  return (
    <section
      aria-busy="true"
      aria-label={`${name} 正在加载`}
      className="overflow-hidden rounded-xl border border-white/10 bg-white/3.5 shadow-xl shadow-black/20 backdrop-blur-sm"
    >
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-white/10 px-4 py-2.5">
        <span className="font-mono text-xs font-medium tracking-wider text-stone-400 uppercase">
          {extension ?? "FILE"}
        </span>
        <span className="text-xs text-stone-400">{formatFileSize(size)}</span>
        <span
          role="status"
          className="ml-auto flex items-center gap-2 text-xs text-stone-400"
        >
          <span
            aria-hidden="true"
            className="size-3.5 animate-spin rounded-full border-2 border-white/15 border-t-stone-300"
          />
          正在加载
        </span>
      </div>
      <div
        aria-hidden="true"
        className="space-y-3 px-4 py-5 motion-safe:animate-pulse"
      >
        {SKELETON_WIDTHS.map((width) => (
          <div key={width} className="flex items-center gap-4">
            <span className="h-2.5 w-6 shrink-0 rounded-full bg-white/6" />
            <span className={`h-2.5 rounded-full bg-white/6 ${width}`} />
          </div>
        ))}
      </div>
    </section>
  );
}

interface PreviewToolbarProps {
  content: string;
  extension: string | undefined;
  path: string;
  size: number;
  lineCount: number;
}

function PreviewToolbar({
  content,
  extension,
  path,
  size,
  lineCount,
}: PreviewToolbarProps) {
  const [contentStatus, setContentStatus] = useCopyStatus();

  async function copyContent() {
    try {
      await navigator.clipboard.writeText(content);
      setContentStatus("copied");
    } catch {
      setContentStatus("error");
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-white/10 px-4 py-2.5">
      <span className="font-mono text-xs font-medium tracking-wider text-stone-400 uppercase">
        {extension ?? "FILE"}
      </span>
      <span className="text-xs text-stone-400">
        {lineCount.toLocaleString()} 行
      </span>
      <span className="text-xs text-stone-400">{formatFileSize(size)}</span>

      <div className="ml-auto flex items-center gap-1">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => void copyContent()}
          title="复制原始内容"
          className="text-stone-400 hover:text-stone-100"
        >
          {contentStatus === "copied" ? (
            <CheckIcon aria-hidden="true" />
          ) : (
            <CopyIcon aria-hidden="true" />
          )}
          {contentStatus === "copied"
            ? "已复制"
            : contentStatus === "error"
              ? "复制失败"
              : "复制"}
        </Button>
        <Button
          asChild
          variant="ghost"
          size="sm"
          title="打开原始文件"
          className="text-stone-400 hover:text-stone-100"
        >
          <a
            href={fileHref(path)}
            target="_blank"
            rel="noreferrer"
            aria-label="打开原始文件"
          >
            <ExternalLinkIcon aria-hidden="true" />
            Raw
          </a>
        </Button>
        <CopyLinkButton
          path={path}
          label="链接"
          className="text-stone-400 hover:text-stone-100"
        />
      </div>
    </div>
  );
}

interface CopyLinkButtonProps {
  path: string;
  label: string;
  variant?: "ghost" | "outline";
  size?: "sm" | "default";
  className?: string;
}

function CopyLinkButton({
  path,
  label,
  variant = "ghost",
  size = "sm",
  className,
}: CopyLinkButtonProps) {
  const [status, setStatus] = useCopyStatus();

  async function copyLink() {
    const rawUrl = new URL(fileHref(path), window.location.href).href;

    try {
      await navigator.clipboard.writeText(rawUrl);
      setStatus("copied");
    } catch {
      setStatus("error");
    }
  }

  return (
    <Button
      type="button"
      variant={variant}
      size={size}
      onClick={() => void copyLink()}
      title="复制原始文件链接"
      aria-label="复制原始文件链接"
      className={className}
    >
      {status === "copied" ? (
        <CheckIcon aria-hidden="true" />
      ) : (
        <LinkIcon aria-hidden="true" />
      )}
      {status === "copied" ? "已复制" : status === "error" ? "复制失败" : label}
    </Button>
  );
}

interface PreviewUnavailableProps {
  name: string;
  path: string;
  size: number;
  kind: "binary" | "too-large" | "error";
  error?: string;
  onRetry?: () => void;
}

export function PreviewUnavailable({
  name,
  path,
  size,
  kind,
  error,
  onRetry,
}: PreviewUnavailableProps) {
  const title =
    kind === "binary"
      ? "无法预览此文件"
      : kind === "too-large"
        ? "文件过大，暂不预览"
        : "读取文件失败";
  const description =
    kind === "binary"
      ? "该文件为二进制格式或暂不支持在线预览，请下载后查看。"
      : kind === "too-large"
        ? `文件大小 ${formatFileSize(size)}，超过 ${formatFileSize(MAX_PREVIEW_BYTES)} 的在线预览限制。`
        : (error ?? "请稍后重试，或下载文件后查看。");

  return (
    <section className="rounded-xl border border-white/10 bg-white/3.5 px-6 py-16 text-center shadow-xl shadow-black/20 backdrop-blur-sm">
      <div className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-white/6 text-stone-400">
        <FileIcon className="size-6" strokeWidth={1.75} aria-hidden="true" />
      </div>
      <h2 className="mt-4 text-lg font-medium text-stone-100">{title}</h2>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-stone-400">
        {description}
      </p>
      <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
        {kind === "error" && onRetry ? (
          <Button type="button" onClick={onRetry}>
            <RotateCwIcon aria-hidden="true" />
            重试
          </Button>
        ) : null}
        <Button asChild>
          <a href={fileHref(path)} download={name}>
            <DownloadIcon aria-hidden="true" />
            下载文件
          </a>
        </Button>
        <CopyLinkButton
          path={path}
          label="复制链接"
          variant="outline"
          size="default"
        />
      </div>
    </section>
  );
}
