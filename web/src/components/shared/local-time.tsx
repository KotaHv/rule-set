import { cn } from "cn";

import { formatLocalTime, utcTimeTitle } from "@/utils/format";

interface LocalTimeProps {
  timestamp: number;
  className?: string;
}

export function LocalTime({ timestamp, className }: LocalTimeProps) {
  return (
    <span
      className={cn("inline-block tabular-nums", className)}
      title={timestamp > 0 ? utcTimeTitle(timestamp) : undefined}
    >
      {formatLocalTime(timestamp)}
    </span>
  );
}
