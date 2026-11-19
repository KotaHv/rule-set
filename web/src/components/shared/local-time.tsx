import type { ComponentProps } from "react";

import { cn } from "cn";

import {
  formatLocalTime,
  isoDateTime,
  utcTimeTitle,
} from "@/utils/format";

interface LocalTimeProps extends ComponentProps<"time"> {
  timestamp: number;
}

export function LocalTime({
  timestamp,
  className,
  ...rest
}: LocalTimeProps) {
  return (
    <time
      dateTime={isoDateTime(timestamp)}
      className={cn("inline-block tabular-nums", className)}
      title={timestamp > 0 ? utcTimeTitle(timestamp) : undefined}
      {...rest}
    >
      {formatLocalTime(timestamp)}
    </time>
  );
}
