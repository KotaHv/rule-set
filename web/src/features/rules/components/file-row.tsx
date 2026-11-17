import { fileHref } from "@/features/rules/utils/tree";
import { formatFileSize } from "@/utils/format";
import type { ManifestFile } from "@/types/manifest";
import { LocalTime } from "@/components/shared/local-time";

interface FileRowProps {
  node: ManifestFile;
}

export function FileRow({ node }: FileRowProps) {
  return (
    <a href={fileHref(node.path)} className="group block">
      <div className="rounded-lg border border-stone-200/60 bg-white/60 p-4 backdrop-blur-sm transition-all duration-200 hover:border-stone-300/80 hover:bg-white/80">
        <div className="flex items-center justify-between gap-4 sm:gap-6">
          <div className="min-w-0 flex-1">
            <h2 className="truncate font-medium text-stone-900 transition-colors duration-200 group-hover:text-stone-700">
              {node.name}
            </h2>
          </div>
          <div className="flex shrink-0 flex-col items-end gap-1 text-sm sm:flex-row sm:items-center sm:gap-6 sm:text-center sm:text-base">
            <span className="hidden w-12 text-stone-500 sm:block">文件</span>
            <span className="font-mono text-stone-500 sm:w-20">
              {formatFileSize(node.size)}
            </span>
            <LocalTime
              timestamp={node.mtime}
              className="font-mono text-stone-500 sm:w-48"
            />
          </div>
        </div>
      </div>
    </a>
  );
}
