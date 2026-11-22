import type { ReactNode } from "react";

import { FileIcon, FolderIcon } from "lucide-react";

import { Shell } from "@/app/components/shell";
import { MetaItem } from "@/components/shared/meta-item";
import { DirectoryCard } from "@/features/rules/components/listing/directory-card";
import { FileCard } from "@/features/rules/components/listing/file-card";
import { EmptyState } from "@/features/rules/components/shared/empty-state";
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
}: {
  directoryCount: number;
  fileCount: number;
}) {
  return (
    <>
      {directoryCount > 0 && (
        <MetaItem icon={FolderIcon}>{directoryCount} 个目录</MetaItem>
      )}
      {fileCount > 0 && (
        <MetaItem icon={FileIcon}>{fileCount} 个文件</MetaItem>
      )}
    </>
  );
}

function DirectoryContents({
  directories,
  files,
}: {
  directories: ManifestDirectory[];
  files: ManifestFile[];
}) {
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
  const { client, node, trail } = data;
  const { directories, files } = splitChildren(node);
  const clientName = formatName(client.root.name);
  const isEmpty = directories.length === 0 && files.length === 0;
  const content = isEmpty ? (
    <EmptyState />
  ) : (
    <DirectoryContents directories={directories} files={files} />
  );

  return (
    <>
      <title>{`${clientName} - Rule Set`}</title>
      <Shell
        title={clientName}
        crumbs={ancestorCrumbs(trail)}
        updatedAt={node.mtime}
        meta={
          !isEmpty && (
            <DirectoryMeta
              directoryCount={directories.length}
              fileCount={files.length}
            />
          )
        }
      >
        {content}
      </Shell>
    </>
  );
}
