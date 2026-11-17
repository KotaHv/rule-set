import { Link } from "react-router";

import { directoryRoute } from "@/features/rules/utils/tree";
import type { ManifestDirectory } from "@/types/manifest";
import { LocalTime } from "@/components/shared/local-time";

interface DirectoryRowProps {
  node: ManifestDirectory;
}

export function DirectoryRow({ node }: DirectoryRowProps) {
  return (
    <Link to={directoryRoute(node.path)} className="group block">
      <div className="rounded-lg border border-stone-200/60 bg-white/60 p-4 backdrop-blur-sm transition-all duration-200 hover:border-stone-300/80 hover:bg-white/80">
        <div className="flex items-center justify-between gap-4 sm:gap-6">
          <div className="min-w-0 flex-1">
            <h2 className="truncate font-medium text-stone-900 transition-colors duration-200 group-hover:text-stone-700">
              {node.name}
            </h2>
          </div>
          <div className="flex shrink-0 flex-col items-end gap-1 text-sm sm:flex-row sm:items-center sm:gap-6 sm:text-center sm:text-base">
            <span className="text-stone-500 sm:w-12">目录</span>
            <span className="hidden w-20 text-stone-500 sm:block">—</span>
            <LocalTime
              timestamp={node.mtime}
              className="font-mono text-stone-500 sm:w-48"
            />
          </div>
        </div>
      </div>
    </Link>
  );
}
