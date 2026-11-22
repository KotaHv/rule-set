import type { ComponentProps } from "react";

import { cn } from "cn";

/** Framed code surface aligned with the rest of the page at every breakpoint. */
export function PreviewPanel({ className, ...props }: ComponentProps<"div">) {
  return (
    <div
      className={cn(
        "overflow-hidden rounded-xl border border-white/10 bg-white/3.5 shadow-xl shadow-black/20",
        className,
      )}
      {...props}
    />
  );
}
