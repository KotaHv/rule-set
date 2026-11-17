import { useLoaderData } from "react-router";

import type { loadDirectoryPage } from "@/features/rules/api/directory";
import { DirectoryRow } from "@/features/rules/components/directory-row";
import { EmptyState } from "@/features/rules/components/empty-state";
import { FileRow } from "@/features/rules/components/file-row";
import { splitChildren } from "@/features/rules/utils/tree";
import { formatName } from "@/utils/format";

export function DirectoryPage() {
  const { node } = useLoaderData<typeof loadDirectoryPage>();
  const { directories, files } = splitChildren(node);
  const total = directories.length + files.length;

  let summary = `共 ${total} 项`;
  if (directories.length > 0 && files.length > 0) {
    summary = `共 ${total} 项：${directories.length} 个目录，${files.length} 个文件`;
  } else if (directories.length > 0) {
    summary = `共 ${directories.length} 个目录`;
  } else if (files.length > 0) {
    summary = `共 ${files.length} 个文件`;
  }

  return (
    <>
      <title>{`${formatName(node.name)} - Rule Set`}</title>
      <div className="mx-auto max-w-6xl px-6 py-6 lg:px-8">
        {total > 0 ? (
          <>
            <div className="mb-6">
              <p className="text-sm text-stone-600">{summary}</p>
            </div>
            <ul className="space-y-1.5">
              {directories.map((child) => (
                <li key={child.path}>
                  <DirectoryRow node={child} />
                </li>
              ))}
              {files.map((child) => (
                <li key={child.path}>
                  <FileRow node={child} />
                </li>
              ))}
            </ul>
          </>
        ) : (
          <EmptyState />
        )}
      </div>
    </>
  );
}
