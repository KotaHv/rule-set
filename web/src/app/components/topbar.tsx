import { Fragment } from "react";
import { ChevronLeftIcon, ChevronRightIcon } from "lucide-react";
import { Link, useRouteLoaderData } from "react-router";

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Button } from "@/components/ui/button";
import { LocalTime } from "@/components/shared/local-time";
import {
  BROWSER_ROUTE_ID,
  type BrowserPageData,
  type loadBrowserPage,
} from "@/features/rules/api/browser";
import { useManifest } from "@/features/rules/hooks/use-manifest";
import { directoryRoute, parentRoute } from "@/features/rules/utils/tree";
import { formatName } from "@/utils/format";

const LOGO_URL = `${import.meta.env.BASE_URL}logo.webp`;

export function TopBar() {
  const page = useRouteLoaderData<typeof loadBrowserPage>(BROWSER_ROUTE_ID);
  const { latestUpdate } = useManifest();

  return (
    <header className="sticky top-0 z-30 border-b border-white/10 bg-stone-950/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-3 px-6 lg:px-8">
        <Link
          to={directoryRoute("")}
          aria-label="Rule Set 首页"
          className="block shrink-0 rounded-lg outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
        >
          <img
            src={LOGO_URL}
            alt=""
            width={44}
            height={44}
            className="block size-11 rounded-lg ring-1 ring-white/10"
          />
        </Link>

        {page ? <BrowserBar page={page} /> : null}

        <LocalTime
          timestamp={latestUpdate}
          className="ml-auto hidden shrink-0 text-sm text-stone-400 sm:block"
        />
      </div>
    </header>
  );
}

function BrowserBar({ page }: { page: BrowserPageData }) {
  const ancestors = page.trail.slice(0, -1);
  const currentName =
    page.node.type === "file" ? page.node.name : formatName(page.node.name);

  return (
    <div className="flex min-w-0 items-center gap-2">
      <Button asChild variant="ghost" size="icon-sm" className="sm:hidden">
        <Link to={parentRoute(page.node.path)} aria-label="返回上级目录">
          <ChevronLeftIcon />
        </Link>
      </Button>

      {ancestors.length > 0 ? (
        <Breadcrumb className="hidden min-w-0 sm:block">
          <BreadcrumbList className="flex-nowrap">
            {ancestors.map((entry, index) => (
              <Fragment key={entry.path}>
                {index > 0 ? <BreadcrumbSeparator /> : null}
                <BreadcrumbItem>
                  <BreadcrumbLink asChild>
                    <Link to={directoryRoute(entry.path)}>
                      {formatName(entry.name)}
                    </Link>
                  </BreadcrumbLink>
                </BreadcrumbItem>
              </Fragment>
            ))}
          </BreadcrumbList>
        </Breadcrumb>
      ) : null}

      <ChevronRightIcon
        className="hidden size-3.5 shrink-0 text-stone-600 sm:block"
        aria-hidden="true"
      />
      <h1 className="truncate font-display text-base font-semibold tracking-wide text-stone-100">
        {currentName}
      </h1>
    </div>
  );
}
