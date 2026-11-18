import { ChevronRightIcon } from "lucide-react";
import { Link } from "react-router";

import { LocalTime } from "@/components/shared/local-time";
import { FolderGlyph } from "@/features/rules/components/entity-icon";
import { directoryRoute } from "@/features/rules/utils/tree";
import type { ManifestDirectory } from "@/types/manifest";

interface DirectoryRowProps {
  node: ManifestDirectory;
}

export function DirectoryRow({ node }: DirectoryRowProps) {
  return (
    <Link
      to={directoryRoute(node.path)}
      aria-label={`打开目录 ${node.name}`}
      className="group block rounded-lg outline-none focus-visible:ring-2 focus-visible:ring-white/20"
    >
      <div className="flex items-center gap-3 rounded-lg border border-white/10 bg-white/[0.03] p-3 backdrop-blur-sm transition-all duration-200 group-hover:border-white/20 group-hover:bg-white/[0.06] sm:gap-4">
        <FolderGlyph />

        <div className="min-w-0 flex-1">
          <h2 className="truncate font-medium text-stone-100">{node.name}</h2>
          <LocalTime
            timestamp={node.mtime}
            aria-hidden="true"
            className="mt-0.5 block font-mono text-xs text-stone-400 sm:hidden"
          />
        </div>

        <div className="flex shrink-0 items-center gap-6 text-sm text-stone-400">
          <span className="tabular-nums sm:w-16 sm:text-right">
            {node.children.length} 项
          </span>
          {/* Mobile: sr-only for screen readers, while the title copy above is
              visual-only. sm+: this copy becomes the visible right column. */}
          <LocalTime
            timestamp={node.mtime}
            className="sr-only font-mono sm:not-sr-only sm:block sm:w-48 sm:text-right"
          />
        </div>

        <ChevronRightIcon
          className="size-4 shrink-0 text-stone-600 transition-all duration-200 group-hover:translate-x-0.5 group-hover:text-stone-200"
          aria-hidden="true"
        />
      </div>
    </Link>
  );
}
