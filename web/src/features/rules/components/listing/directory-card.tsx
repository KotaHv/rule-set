import { ClockIcon, FilesIcon, FolderIcon } from "lucide-react";

import { LocalTime } from "@/components/shared/local-time";
import { MetaItem } from "@/components/shared/meta-item";
import { directoryRoute } from "@/features/rules/utils/tree";
import { formatName } from "@/utils/format";
import type { ManifestDirectory } from "@/types/manifest";
import { ItemCard } from "./item-card";

export function DirectoryCard({ node }: { node: ManifestDirectory }) {
  return (
    <ItemCard
      to={directoryRoute(node.path)}
      tile={
        <FolderIcon
          className="size-6 text-stone-300"
          strokeWidth={1.75}
          aria-hidden="true"
        />
      }
      title={formatName(node.name)}
      meta={[
        <MetaItem key="count" icon={FilesIcon}>
          {node.children.length} 项
        </MetaItem>,
        <MetaItem key="mtime" icon={ClockIcon}>
          <LocalTime timestamp={node.mtime} />
        </MetaItem>,
      ]}
    />
  );
}
