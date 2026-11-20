import { useEffect, useState } from "react";

import { CheckIcon, CircleAlertIcon, type LucideIcon } from "lucide-react";
import type { VariantProps } from "class-variance-authority";

import { Button, type buttonVariants } from "@/components/ui/button";

type CopyStatus = "idle" | "copied" | "error";

const STATUS_RESET_MS = 2000;

const STATUS_LABELS = { copied: "已复制", error: "复制失败" } as const;

function useCopy() {
  const [status, setStatus] = useState<CopyStatus>("idle");
  const [copyCount, setCopyCount] = useState(0);

  useEffect(() => {
    if (status === "idle") {
      return;
    }

    const timer = window.setTimeout(() => setStatus("idle"), STATUS_RESET_MS);
    return () => window.clearTimeout(timer);
  }, [status, copyCount]);

  async function copy(text: string) {
    try {
      await navigator.clipboard.writeText(text);
      setStatus("copied");
    } catch {
      setStatus("error");
    }
    setCopyCount((count) => count + 1);
  }

  return { status, copy };
}

interface CopyButtonProps extends VariantProps<typeof buttonVariants> {
  getText: () => string;
  icon: LucideIcon;
  label: string;
}

export function CopyButton({
  getText,
  icon: Icon,
  label,
  ...variants
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
        {...variants}
        size="icon"
        aria-label={label}
        onClick={() => void copy(getText())}
      >
        <Glyph
          aria-hidden="true"
          className={status === "error" ? "text-red-400" : undefined}
        />
      </Button>
      <span className="sr-only" role="status">
        {status === "idle" ? "" : STATUS_LABELS[status]}
      </span>
    </>
  );
}
