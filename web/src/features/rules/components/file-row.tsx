import { DownloadIcon } from "lucide-react";
import { Link } from "react-router";

import { LocalTime } from "@/components/shared/local-time";
import { FileGlyph } from "@/features/rules/components/entity-icon";
import { fileHref, fileRoute } from "@/features/rules/utils/tree";
import { fileExtension, formatFileSize } from "@/utils/format";
import type { ManifestFile } from "@/types/manifest";

interface FileRowProps {
  node: ManifestFile;
}

export function FileRow({ node }: FileRowProps) {
  return (
    <div className="group relative flex items-center gap-3 rounded-lg border border-white/10 bg-white/[0.025] p-3 backdrop-blur-sm transition-all duration-200 hover:border-white/20 hover:bg-white/[0.06] sm:gap-4">
      <Link
        to={fileRoute(node.path)}
        aria-label={`预览 ${node.name}`}
        className="absolute inset-0 rounded-lg outline-none focus-visible:ring-2 focus-visible:ring-white/20 focus-visible:ring-inset"
      />

      <FileGlyph extension={fileExtension(node.name)} />

      <div className="pointer-events-none relative min-w-0 flex-1">
        <h2 className="truncate text-stone-200 transition-colors duration-200 group-hover:text-stone-50">
          {node.name}
        </h2>
        <LocalTime
          timestamp={node.mtime}
          aria-hidden="true"
          className="mt-0.5 block font-mono text-xs text-stone-400 sm:hidden"
        />
      </div>

      <div className="pointer-events-none relative flex shrink-0 items-center gap-6 text-sm text-stone-400">
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

      <a
        href={fileHref(node.path)}
        download={node.name}
        aria-label={`下载 ${node.name}`}
        className="relative z-10 -m-2 shrink-0 rounded-lg p-2 text-stone-500 transition-colors duration-200 hover:text-stone-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/20"
      >
        <DownloadIcon className="size-4" aria-hidden="true" />
      </a>
    </div>
  );
}
