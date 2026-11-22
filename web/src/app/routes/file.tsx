import {
  ChevronLeftIcon,
  CopyIcon,
  DownloadIcon,
  HardDriveIcon,
  LinkIcon,
  ListIcon,
} from "lucide-react";
import { Link } from "react-router";

import { Shell } from "@/app/components/shell";
import { CopyButton } from "@/components/shared/copy-button";
import { MetaItem } from "@/components/shared/meta-item";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "cn";
import type { FilePageData } from "@/features/rules/api/browser";
import { FilePreviewView } from "@/features/rules/components/preview/file-preview";
import { useFilePreview } from "@/features/rules/hooks/use-file-preview";
import { ancestorCrumbs } from "@/features/rules/utils/crumbs";
import { fileHref, fileUrl, parentRoute } from "@/features/rules/utils/tree";
import type { ManifestFile } from "@/types/manifest";
import type { FilePreviewState } from "@/types/preview";
import { formatFileSize, formatName } from "@/utils/format";

const RAIL_ICON =
  "size-8 p-0 lg:h-10 lg:w-full lg:justify-start lg:gap-2.5 lg:px-5";
const RAIL_LABEL = "px-3 lg:h-10 lg:justify-start lg:px-5";

function FileMeta({
  node,
  preview,
}: {
  node: ManifestFile;
  preview: FilePreviewState;
}) {
  const lineCount =
    preview.kind === "text"
      ? `${preview.document.lineCount.toLocaleString()} 行`
      : preview.kind === "loading"
        ? "— 行"
        : null;

  return (
    <>
      <MetaItem icon={HardDriveIcon}>{formatFileSize(node.size)}</MetaItem>
      {lineCount !== null && <MetaItem icon={ListIcon}>{lineCount}</MetaItem>}
    </>
  );
}

function FileActions({
  node,
  preview,
}: {
  node: ManifestFile;
  preview: FilePreviewState;
}) {
  const content =
    preview.kind === "text" ? preview.document.content : null;
  const showContentAction =
    preview.kind === "loading" || preview.kind === "text";

  return (
    <>
      <Link
        to={parentRoute(node.path)}
        aria-label="返回上级目录"
        className={cn(
          buttonVariants({ variant: "secondary", size: "icon" }),
          "lg:hidden",
        )}
      >
        <ChevronLeftIcon aria-hidden="true" />
      </Link>
      <CopyButton
        showLabel
        icon={LinkIcon}
        label="复制链接"
        value={fileUrl(node.path)}
        className={cn(RAIL_LABEL, "flex-1 lg:flex-none")}
      />
      {showContentAction && (
        <CopyButton
          showLabel
          variant="secondary"
          icon={CopyIcon}
          label="复制内容"
          value={content}
          className={RAIL_ICON}
          labelClassName="hidden lg:inline"
        />
      )}
      <a
        href={fileHref(node.path)}
        download={node.name}
        aria-label="下载"
        className={cn(buttonVariants({ variant: "secondary" }), RAIL_ICON)}
      >
        <DownloadIcon aria-hidden="true" />
        <span aria-hidden="true" className="hidden lg:inline">
          下载
        </span>
      </a>
    </>
  );
}

export function FilePage({ data }: { data: FilePageData }) {
  const { client, node, trail } = data;
  const { preview, retry } = useFilePreview(node);
  const clientName = formatName(client.root.name);

  return (
    <>
      <title>{`${node.name} - Rule Set`}</title>
      <Shell
        fillViewport
        title={clientName}
        crumbs={[...ancestorCrumbs(trail), { label: node.name }]}
        updatedAt={node.mtime}
        meta={<FileMeta node={node} preview={preview} />}
        actions={<FileActions node={node} preview={preview} />}
      >
        <div className="flex min-h-40 flex-1 flex-col lg:flex-none">
          <FilePreviewView node={node} preview={preview} onRetry={retry} />
        </div>
      </Shell>
    </>
  );
}
