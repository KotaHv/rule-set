import type { ReactNode } from "react";

import { ClockIcon, FileIcon, FolderIcon } from "lucide-react";

import { Shell } from "@/app/components/shell";
import { LocalTime } from "@/components/shared/local-time";
import { MetaItem } from "@/components/shared/meta-item";
import { DirectoryCard } from "@/features/rules/components/directory-card";
import { EmptyState } from "@/features/rules/components/empty-state";
import { FileCard } from "@/features/rules/components/file-card";
import type { DirectoryPageData } from "@/features/rules/api/browser";
import { ancestorCrumbs } from "@/features/rules/utils/crumbs";
import { splitChildren } from "@/features/rules/utils/tree";
import type { ManifestDirectory, ManifestFile } from "@/types/manifest";
import { formatName } from "@/utils/format";

function CardGroup({
  title,
  showTitle,
  children,
}: {
  title: string;
  showTitle: boolean;
  children: ReactNode;
}) {
  return (
    <section>
      <h2
        className={
          showTitle ? "mb-3 text-sm font-semibold text-stone-400" : "sr-only"
        }
      >
        {title}
      </h2>
      <ul className="space-y-3">{children}</ul>
    </section>
  );
}

function DirectoryMeta({
  directoryCount,
  fileCount,
  mtime,
}: {
  directoryCount: number;
  fileCount: number;
  mtime: number;
}) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-x-4 gap-y-1">
        {directoryCount > 0 && (
          <MetaItem icon={FolderIcon}>{directoryCount} 个目录</MetaItem>
        )}
        {fileCount > 0 && (
          <MetaItem icon={FileIcon}>{fileCount} 个文件</MetaItem>
        )}
      </div>
      <MetaItem icon={ClockIcon}>
        更新于 <LocalTime timestamp={mtime} />
      </MetaItem>
    </div>
  );
}

function DirectoryContents({
  directories,
  files,
}: {
  directories: ManifestDirectory[];
  files: ManifestFile[];
}) {
  if (directories.length === 0 && files.length === 0) {
    return <EmptyState />;
  }

  return (
    <div className="space-y-8">
      {directories.length > 0 && (
        <CardGroup title="目录" showTitle={files.length > 0}>
          {directories.map((child) => (
            <DirectoryCard key={child.path} node={child} />
          ))}
        </CardGroup>
      )}
      {files.length > 0 && (
        <CardGroup title="文件" showTitle={directories.length > 0}>
          {files.map((child) => (
            <FileCard key={child.path} node={child} />
          ))}
        </CardGroup>
      )}
    </div>
  );
}

export function DirectoryPage({ data }: { data: DirectoryPageData }) {
  const { node, trail } = data;
  const client = trail[0];
  const { directories, files } = splitChildren(node);

  return (
    <>
      <title>{`${formatName(client.name)} - Rule Set`}</title>
      <Shell
        title={formatName(client.name)}
        crumbs={[
          { label: "Home", to: "/" },
          ...ancestorCrumbs(trail),
          { label: formatName(node.name) },
        ]}
        meta={
          <DirectoryMeta
            directoryCount={directories.length}
            fileCount={files.length}
            mtime={node.mtime}
          />
        }
      >
        <DirectoryContents directories={directories} files={files} />
      </Shell>
    </>
  );
}
