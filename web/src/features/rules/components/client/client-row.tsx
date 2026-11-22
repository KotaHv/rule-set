import {
  ChevronRightIcon,
  ClockIcon,
  FilesIcon,
  HardDriveIcon,
} from "lucide-react";
import { Link } from "react-router";

import { LocalTime } from "@/components/shared/local-time";
import { MetaItem } from "@/components/shared/meta-item";
import {
  Card,
  CardAction,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { CLIENT_META } from "@/features/rules/constants";
import { treeStats } from "@/features/rules/utils/stats";
import { directoryRoute } from "@/features/rules/utils/tree";
import type { ClientSlug, ManifestClient } from "@/types/manifest";
import { formatFileSize } from "@/utils/format";
import { ClientIcon } from "./client-icon";

interface ClientRowProps {
  client: ManifestClient;
}

function ClientBadge({ slug }: { slug: ClientSlug }) {
  return (
    <span
      style={{
        backgroundColor: `color-mix(in oklab, ${CLIENT_META[slug].color} 15%, transparent)`,
      }}
      className="grid size-12 shrink-0 place-items-center rounded-[24%] sm:size-14"
    >
      <ClientIcon name={slug} className="size-8 sm:size-9" />
    </span>
  );
}

export function ClientRow({ client }: ClientRowProps) {
  const meta = CLIENT_META[client.slug];
  const stats = treeStats(client.root);

  return (
    <Card className="group relative h-full gap-0 rounded-2xl border border-white/15 bg-white/6 py-0 ring-0 transition-colors hover:border-stone-100/20 hover:bg-white/10">
      <Link
        to={directoryRoute(client.root.path)}
        aria-label={`打开 ${meta.label}`}
        className="absolute inset-0 z-10 rounded-2xl outline-none focus-visible:ring-2 focus-visible:ring-stone-100/30 focus-visible:ring-inset"
      />

      <CardHeader className="flex h-full items-center gap-3 p-3 sm:px-4">
        <ClientBadge slug={client.slug} />

        <div className="flex min-w-0 flex-1 flex-col gap-0.5">
          <CardTitle
            role="heading"
            aria-level={2}
            className="min-w-0 wrap-break-word text-xl leading-tight font-bold tracking-tight text-stone-100 sm:text-2xl"
          >
            {meta.label}
          </CardTitle>

          <CardDescription className="flex min-w-0 flex-col gap-0.5">
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1 xs:flex-nowrap xs:gap-x-3">
              <MetaItem icon={FilesIcon} className="text-xs">
                {stats.files.toLocaleString()} 个文件
              </MetaItem>
              <MetaItem icon={HardDriveIcon} className="text-xs">
                {formatFileSize(stats.size)}
              </MetaItem>
            </div>

            <MetaItem icon={ClockIcon} className="text-xs">
              <LocalTime timestamp={client.root.mtime} />
            </MetaItem>
          </CardDescription>
        </div>

        <CardAction className="ml-auto hidden self-center 2xs:block">
          <ChevronRightIcon
            aria-hidden="true"
            className="size-5 shrink-0 text-stone-500 transition-colors group-hover:text-stone-100"
          />
        </CardAction>
      </CardHeader>
    </Card>
  );
}
