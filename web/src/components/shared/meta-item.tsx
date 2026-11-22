import type { ComponentProps, ComponentType } from "react";
import { Slot } from "radix-ui";

import { cn } from "cn";

interface MetaItemProps extends ComponentProps<"span"> {
  icon: ComponentType<{ className?: string }>;
  asChild?: boolean;
}

const BASE =
  "inline-flex items-center gap-1.5 text-sm text-stone-400 tabular-nums";
const LINK =
  "rounded transition-colors hover:text-stone-100 focus-visible:ring-2 focus-visible:ring-stone-100/40 focus-visible:outline-none";

/** One fact with its icon. Use `asChild` to render as a link. */
export function MetaItem({
  icon: Icon,
  asChild = false,
  className,
  children,
  ...props
}: MetaItemProps) {
  const Comp = asChild ? Slot.Root : "span";

  return (
    <Comp
      data-slot="meta-item"
      className={cn(BASE, asChild && LINK, className)}
      {...props}
    >
      <Icon aria-hidden="true" className="size-4 shrink-0 text-stone-500" />
      <Slot.Slottable>{children}</Slot.Slottable>
    </Comp>
  );
}
