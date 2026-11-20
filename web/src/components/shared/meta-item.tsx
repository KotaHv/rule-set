import type { ReactNode } from "react";

import type { LucideIcon } from "lucide-react";

interface MetaItemProps {
  icon: LucideIcon;
  children: ReactNode;
}

/** One fact with its icon, so a row of them can be scanned instead of read. */
export function MetaItem({ icon: Icon, children }: MetaItemProps) {
  return (
    <span className="inline-flex items-center gap-1.5 text-sm text-stone-400 tabular-nums">
      <Icon aria-hidden="true" className="size-4 shrink-0 text-stone-500" />
      {children}
    </span>
  );
}
