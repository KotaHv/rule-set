import { ClockIcon, FileIcon, HardDriveIcon, LinkIcon } from "lucide-react";

import { CopyButton } from "@/components/shared/copy-button";
import { LocalTime } from "@/components/shared/local-time";
import { MetaItem } from "@/components/shared/meta-item";
import { fileRoute, fileUrl } from "@/features/rules/utils/tree";
import { formatFileSize } from "@/utils/format";
import type { ManifestFile } from "@/types/manifest";
import { ItemCard } from "./item-card";

export function FileCard({ node }: { node: ManifestFile }) {
  return (
    <ItemCard
      to={fileRoute(node.path)}
      tile={
        <FileIcon
          className="size-5 text-stone-300"
          strokeWidth={1.75}
          aria-hidden="true"
        />
      }
      title={node.name}
      meta={[
        <MetaItem key="size" icon={HardDriveIcon}>
          {formatFileSize(node.size)}
        </MetaItem>,
        <MetaItem key="mtime" icon={ClockIcon}>
          <LocalTime timestamp={node.mtime} />
        </MetaItem>,
      ]}
      action={
        <CopyButton
          variant="ghost"
          icon={LinkIcon}
          label={`复制 ${node.name} 的链接`}
          value={fileUrl(node.path)}
        />
      }
    />
  );
}
