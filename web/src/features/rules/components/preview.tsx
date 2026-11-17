import { useEffect, useMemo, useState } from "react";
import {
  CheckIcon,
  CopyIcon,
  DownloadIcon,
  ExternalLinkIcon,
  LinkIcon,
  RotateCwIcon,
} from "lucide-react";
import { useRevalidator } from "react-router";

import { Button } from "@/components/ui/button";
import { MAX_PREVIEW_BYTES } from "@/features/rules/api/file";
import { FileGlyph } from "@/features/rules/components/entity-icon";
import {
  countLines,
  prettyPrintJson,
  splitLines,
} from "@/features/rules/utils/file-content";
import { fileHref } from "@/features/rules/utils/tree";
import { fileExtension, formatFileSize } from "@/utils/format";

type CopyStatus = "copied" | "error";

const LARGE_FILE_LINES = 10000;

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
    <section className="overflow-hidden rounded-xl border border-stone-200/70 bg-white/70 shadow-sm backdrop-blur-sm">
      <PreviewToolbar
        content={content}
        extension={extension}
        path={path}
        size={size}
        lineCount={lineCount}
      />

      {lineCount > 0 ? (
        <div
          className={
            large
              ? "h-[calc(100dvh-12rem)] overflow-auto overscroll-contain"
              : "max-h-[calc(100dvh-12rem)] overflow-auto overscroll-contain"
          }
          role="region"
          aria-label={`${name} 文件内容`}
          tabIndex={0}
        >
          {large ? (
            <pre className="w-max min-w-full px-4 py-3 font-mono text-[13px] leading-6 tab-4">
              {displayContent}
            </pre>
          ) : (
            <pre className="w-max min-w-full py-3 font-mono text-[13px] leading-6 tab-4">
              <code className="block">
                {lines.map((line, index) => (
                  <span key={index} className="group/line flex">
                    <span
                      aria-hidden="true"
                      className="sticky left-0 z-10 w-14 shrink-0 select-none border-r border-stone-100 bg-white/95 pr-3 text-right text-stone-300 group-hover/line:text-stone-500"
                    >
                      {index + 1}
                    </span>
                    <span className="whitespace-pre px-4 text-stone-700 group-hover/line:bg-stone-100/60">
                      {line || " "}
                    </span>
                  </span>
                ))}
              </code>
            </pre>
          )}
        </div>
      ) : (
        <p className="px-4 py-16 text-center text-sm text-stone-500">
          这是一个空文件
        </p>
      )}
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
    <div className="flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-stone-200/60 px-4 py-2.5">
      <span className="font-mono text-xs font-medium tracking-wider text-stone-500 uppercase">
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
          className="text-stone-500 hover:text-stone-900"
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
          className="text-stone-500 hover:text-stone-900"
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
          className="text-stone-500 hover:text-stone-900"
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
}

export function PreviewUnavailable({
  name,
  path,
  size,
  kind,
  error,
}: PreviewUnavailableProps) {
  const revalidator = useRevalidator();
  const retrying = revalidator.state !== "idle";

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
    <section className="rounded-xl border border-stone-200/70 bg-white/60 px-6 py-16 text-center shadow-sm backdrop-blur-sm">
      <div className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-stone-100 text-stone-500">
        <FileGlyph extension={fileExtension(name)} />
      </div>
      <h2 className="mt-4 text-lg font-medium text-stone-800">{title}</h2>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-stone-500">
        {description}
      </p>
      <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
        {kind === "error" ? (
          <Button
            type="button"
            onClick={() => revalidator.revalidate()}
            disabled={retrying}
            aria-busy={retrying || undefined}
          >
            <RotateCwIcon
              aria-hidden="true"
              className={retrying ? "motion-safe:animate-spin" : undefined}
            />
            {retrying ? "重试中" : "重试"}
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
