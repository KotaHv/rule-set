import { Fragment } from "react";

import { cn } from "cn";

import { CODE_TYPE } from "@/features/rules/constants";
import { PreviewPanel } from "./preview-panel";

const SKELETON_WIDTHS = [
  "w-11/12",
  "w-7/12",
  "w-10/12",
  "w-5/12",
  "w-9/12",
  "w-6/12",
  "w-8/12",
  "w-4/12",
] as const;
const SKELETON_ROWS = Array.from(
  { length: 40 },
  (_, index) => SKELETON_WIDTHS[index % SKELETON_WIDTHS.length],
);
const DESKTOP_SKELETON_ROWS = 8;

export function PreviewLoading({ name }: { name: string }) {
  return (
    <PreviewPanel aria-busy="true" className="h-full lg:h-auto">
      <div role="status" className="sr-only">
        {`正在加载 ${name}`}
      </div>
      <div aria-hidden="true" className="h-full overflow-hidden">
        <div
          className={cn(
            "grid auto-rows-[1lh] grid-cols-[2.5ch_minmax(0,1fr)] items-center gap-x-3 px-3 py-4 motion-safe:animate-pulse lg:gap-x-4 lg:px-4",
            CODE_TYPE,
          )}
        >
          {SKELETON_ROWS.map((width, index) => {
            const desktopHidden =
              index >= DESKTOP_SKELETON_ROWS ? "lg:hidden" : undefined;

            return (
              <Fragment key={index}>
                <span
                  className={cn(
                    "h-[0.75em] w-2 justify-self-end rounded-full bg-white/6",
                    desktopHidden,
                  )}
                />
                <span
                  className={cn(
                    "h-[0.75em] rounded-full bg-white/6",
                    width,
                    desktopHidden,
                  )}
                />
              </Fragment>
            );
          })}
        </div>
      </div>
    </PreviewPanel>
  );
}
