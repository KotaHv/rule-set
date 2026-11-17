import { ChevronRightIcon } from "lucide-react";
import { Link } from "react-router";

import { Card, CardContent } from "@/components/ui/card";
import { CLIENT_LABELS } from "@/features/rules/constants";
import { directoryRoute } from "@/features/rules/utils/tree";
import type { ManifestClient } from "@/types/manifest";
import { ClientIcon } from "./client-icon";
import { LocalTime } from "@/components/shared/local-time";

interface DirectoryCardProps {
  client: ManifestClient;
}

export function DirectoryCard({ client }: DirectoryCardProps) {
  return (
    <Link to={directoryRoute(client.root.path)} className="group block h-full">
      <Card variant="glass" className="h-full">
        <CardContent className="flex h-full flex-col">
          <div className="mb-6 flex justify-center">
            <div className="flex size-16 items-center justify-center rounded-2xl bg-linear-to-br from-stone-50 to-stone-100">
              <div className="text-stone-500 transition-colors duration-300 group-hover:text-stone-900">
                <ClientIcon name={client.slug} />
              </div>
            </div>
          </div>

          <div className="mb-4 flex-1 text-center">
            <h2 className="mb-3 text-xl font-medium text-stone-900">
              {CLIENT_LABELS[client.slug]}
            </h2>
          </div>

          <div className="mt-auto text-center">
            <div className="rounded-lg bg-stone-50/50 px-3 py-2 text-sm font-mono text-stone-500">
              <LocalTime timestamp={client.root.mtime} />
            </div>
          </div>
        </CardContent>

        <div className="absolute top-4 right-4 opacity-0 transition-all duration-300 group-hover:opacity-100">
          <ChevronRightIcon className="size-5 text-stone-900" />
        </div>
      </Card>
    </Link>
  );
}
