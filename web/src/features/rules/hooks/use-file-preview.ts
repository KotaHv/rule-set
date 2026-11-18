import { useEffect, useState } from "react";

import { readFilePreview } from "@/features/rules/api/file";
import type { FilePreviewState } from "@/types/preview";
import type { ManifestFile } from "@/types/manifest";

export function useFilePreview(node: ManifestFile) {
  const [preview, setPreview] = useState<FilePreviewState>({
    kind: "loading",
  });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    void readFilePreview(node, controller.signal)
      .then((next) => {
        if (!controller.signal.aborted) {
          setPreview(next);
        }
      })
      .catch((error: unknown) => {
        // readFilePreview returns kind:"error" for normal fetch failures;
        // this path handles aborts and unexpected rejections defensively.
        if (controller.signal.aborted) {
          return;
        }

        setPreview({
          kind: "error",
          content: null,
          error: error instanceof Error ? error.message : "无法读取文件内容",
        });
      });

    return () => controller.abort();
  }, [node, attempt]);

  function retry() {
    setPreview({ kind: "loading" });
    setAttempt((value) => value + 1);
  }

  return { preview, retry };
}
