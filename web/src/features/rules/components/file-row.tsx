import { DownloadIcon } from "lucide-react";

import { LocalTime } from "@/components/shared/local-time";
import { FileGlyph } from "@/features/rules/components/entity-icon";
import { fileHref } from "@/features/rules/utils/tree";
import { formatFileSize } from "@/utils/format";
import type { ManifestFile } from "@/types/manifest";

interface FileRowProps {
  node: ManifestFile;
}

function extensionOf(name: string): string | undefined {
  const index = name.lastIndexOf(".");
  return index > 0 && index < name.length - 1
    ? name.slice(index + 1)
    : undefined;
}

export function FileRow({ node }: FileRowProps) {
  return (
    <a
      href={fileHref(node.path)}
      aria-label={`获取 ${node.name}`}
      className="group block rounded-lg outline-none focus-visible:ring-2 focus-visible:ring-stone-900/20"
    >
      <div className="flex items-center gap-3 rounded-lg border border-stone-200/60 bg-white/60 p-3 backdrop-blur-sm transition-all duration-200 group-hover:border-stone-300/80 group-hover:bg-white/80 sm:gap-4">
        <FileGlyph extension={extensionOf(node.name)} />

        <div className="min-w-0 flex-1">
          <h2 className="truncate text-stone-700 transition-colors duration-200 group-hover:text-stone-900">
            {node.name}
          </h2>
          <LocalTime
            timestamp={node.mtime}
            aria-hidden="true"
            className="mt-0.5 block font-mono text-xs text-stone-400 sm:hidden"
          />
        </div>

        <div className="flex shrink-0 items-center gap-6 text-sm text-stone-500">
          <span className="font-mono tabular-nums sm:w-20 sm:text-right">
            {formatFileSize(node.size)}
          </span>
          {/* Mobile: sr-only for screen readers, while the title copy above is
              visual-only. sm+: this copy becomes the visible right column. */}
          <LocalTime
            timestamp={node.mtime}
            className="sr-only font-mono sm:not-sr-only sm:block sm:w-48 sm:text-right"
          />
        </div>

        <DownloadIcon
          className="size-4 shrink-0 text-stone-300 transition-colors duration-200 group-hover:text-stone-700"
          aria-hidden="true"
        />
      </div>
    </a>
  );
}
