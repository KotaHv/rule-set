import type { ComponentProps } from "react";

import { cn } from "cn";

import { formatLocalTime, utcTimeTitle } from "@/utils/format";

interface LocalTimeProps extends ComponentProps<"span"> {
  timestamp: number;
}

export function LocalTime({
  timestamp,
  className,
  ...rest
}: LocalTimeProps) {
  return (
    <span
      className={cn("inline-block tabular-nums", className)}
      title={timestamp > 0 ? utcTimeTitle(timestamp) : undefined}
      {...rest}
    >
      {formatLocalTime(timestamp)}
    </span>
  );
}
