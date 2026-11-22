import type { CSSProperties } from "react";

import { cn } from "cn";

import { CODE_TYPE } from "@/features/rules/constants";
import {
  isCommentLine,
  splitLines,
} from "@/features/rules/utils/file-content";
import type { PreviewDocument } from "@/types/preview";
import { EmptyState } from "../shared/empty-state";
import { PreviewPanel } from "./preview-panel";

const WRAP = "whitespace-pre-wrap wrap-break-word";
const MAX_NUMBERED_LINES = 10_000;
// 7.25rem = Shell's desktop lg:py-14 (7rem) + 0.25rem frame allowance.
const DESKTOP_CODE_MAX_HEIGHT = "lg:max-h-[calc(100dvh-7.25rem)]";

export function CodeView({
  document,
  name,
}: {
  document: PreviewDocument;
  name: string;
}) {
  const { display, lineCount } = document;

  if (lineCount === 0) {
    return (
      <PreviewPanel className="flex h-full flex-col justify-center px-5 lg:h-auto">
        <EmptyState title="这是一个空文件" description="文件内容为空" />
      </PreviewPanel>
    );
  }

  const gutter = { "--gutter": `${String(lineCount).length}ch` } as CSSProperties;

  return (
    <PreviewPanel className="h-full lg:h-auto">
      <div
        role="region"
        aria-label={`${name} 文件内容`}
        tabIndex={0}
        className={cn(
          "h-full overflow-x-hidden overflow-y-auto overscroll-contain focus-visible:ring-2 focus-visible:ring-stone-100/30 focus-visible:ring-inset focus-visible:outline-none lg:h-auto",
          DESKTOP_CODE_MAX_HEIGHT,
        )}
      >
        <pre
          className={cn("py-4 text-stone-300", CODE_TYPE)}
          style={gutter}
        >
          {lineCount > MAX_NUMBERED_LINES ? (
            <code className={cn(WRAP, "block px-3 lg:px-4")}>{display}</code>
          ) : (
            <code>
              {splitLines(display).map((line, index) => (
                <span
                  key={index}
                  className="grid grid-cols-[var(--gutter)_minmax(0,1fr)] gap-x-3 px-3 lg:gap-x-4 lg:px-4"
                >
                  <span
                    aria-hidden="true"
                    className="text-right text-stone-500/70 tabular-nums select-none"
                  >
                    {index + 1}
                  </span>
                  <span
                    className={cn(
                      WRAP,
                      isCommentLine(line) && "text-stone-500",
                    )}
                  >
                    {line || " "}
                  </span>
                </span>
              ))}
            </code>
          )}
        </pre>
      </div>
    </PreviewPanel>
  );
}
