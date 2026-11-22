import { useEffect, useState } from "react";

type CopyStatus = "idle" | "copied" | "error";

const STATUS_RESET_MS = 2000;

export const COPY_STATUS_LABELS = {
  copied: "已复制",
  error: "复制失败",
} as const;

export function useCopy() {
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
