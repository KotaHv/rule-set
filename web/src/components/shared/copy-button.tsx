import { CheckIcon, CircleAlertIcon, type LucideIcon } from "lucide-react";
import type { VariantProps } from "class-variance-authority";

import { Button, type buttonVariants } from "@/components/ui/button";
import { COPY_STATUS_LABELS, useCopy } from "@/hooks/use-copy";
import { cn } from "cn";

interface CopyButtonProps {
  /** null = nothing to copy yet; the button disables itself. */
  value: string | null;
  icon: LucideIcon;
  label: string;
  variant?: VariantProps<typeof buttonVariants>["variant"];
  /** Render the label next to the icon; omit for icon-only buttons. */
  showLabel?: boolean;
  disabled?: boolean;
  className?: string;
  /** Label visibility, e.g. "hidden lg:inline"; only applies when showLabel is set. */
  labelClassName?: string;
}

export function CopyButton({
  value,
  icon: Icon,
  label,
  variant,
  showLabel = false,
  disabled,
  className,
  labelClassName,
}: CopyButtonProps) {
  const { status, copy } = useCopy();
  const Glyph =
    status === "copied"
      ? CheckIcon
      : status === "error"
        ? CircleAlertIcon
        : Icon;

  return (
    <>
      <Button
        type="button"
        variant={variant}
        size={showLabel ? "default" : "icon"}
        disabled={disabled ?? value === null}
        aria-label={label}
        className={cn(showLabel && "gap-2.5", className)}
        onClick={() => value !== null && void copy(value)}
      >
        <Glyph
          aria-hidden="true"
          className={status === "error" ? "text-red-400" : undefined}
        />
        {showLabel && (
          <span aria-hidden="true" className={labelClassName}>
            {status === "idle" ? label : COPY_STATUS_LABELS[status]}
          </span>
        )}
      </Button>
      <span className="sr-only" role="status">
        {status === "idle" ? "" : COPY_STATUS_LABELS[status]}
      </span>
    </>
  );
}
