import type { ReactNode } from "react";
import { ClockIcon } from "lucide-react";
import { cn } from "cn";
import { Link } from "react-router";

import { Breadcrumbs } from "@/app/components/breadcrumbs";
import { LocalTime } from "@/components/shared/local-time";
import { MetaItem } from "@/components/shared/meta-item";
import type { Crumb } from "@/features/rules/utils/crumbs";

const LOGO_URL = `${import.meta.env.BASE_URL}logo.webp`;

interface ShellProps {
  title: string;
  crumbs?: Crumb[];
  updatedAt: number;
  meta?: ReactNode;
  /**
   * Page actions. When present, the phone action-bar layout is also enabled:
   * the bar is fixed to the bottom edge and main reserves its height.
   */
  actions?: ReactNode;
  /**
   * Let the page own the phone viewport; its content must scroll internally.
   * The 30rem minimum reserves room for the page's 10rem preview floor, the
   * rail, and the fixed action bar in phone landscape.
   */
  fillViewport?: boolean;
  children: ReactNode;
}

function ShellMeta({
  updatedAt,
  meta,
}: {
  updatedAt: number;
  meta?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-4 text-sm leading-5">
      {meta && <div className="flex flex-wrap gap-x-4 gap-y-1">{meta}</div>}
      <MetaItem icon={ClockIcon}>
        更新于 <LocalTime timestamp={updatedAt} />
      </MetaItem>
    </div>
  );
}

function ShellRail({
  title,
  crumbs = [],
  updatedAt,
  meta,
  actions,
}: Omit<ShellProps, "children" | "fillViewport">) {
  return (
    <header className="flex flex-col gap-4 py-5 lg:sticky lg:top-0 lg:h-dvh lg:w-88 lg:shrink-0 lg:justify-center lg:py-14">
      <div className="flex items-center gap-4">
        <Link
          to="/"
          aria-label="Rule Set 首页"
          className="block w-12 shrink-0 rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-stone-100/40 focus-visible:ring-offset-4 focus-visible:ring-offset-black lg:w-16"
        >
          <img
            src={LOGO_URL}
            alt=""
            width={48}
            height={48}
            className="block size-12 rounded-xl lg:size-16"
          />
        </Link>
        <h1 className="min-w-0 text-[clamp(2.5rem,11vw,3.5rem)] leading-none font-bold tracking-tight wrap-anywhere">
          {title}
        </h1>
      </div>

      <Breadcrumbs crumbs={crumbs} />

      <ShellMeta updatedAt={updatedAt} meta={meta} />

      {actions && (
        <div className="fixed inset-x-0 bottom-0 z-20 flex items-center gap-2 border-t border-white/10 bg-black/95 px-4 pt-3 pb-[calc(0.75rem+env(safe-area-inset-bottom))] backdrop-blur-xl lg:static lg:inset-auto lg:z-auto lg:flex lg:flex-col lg:items-stretch lg:gap-4 lg:border-0 lg:bg-transparent lg:p-0 lg:backdrop-blur-none">
          {actions}
        </div>
      )}
    </header>
  );
}

/**
 * Shared frame for the rule index. On desktop the left rail stays fixed while
 * the content scrolls; on small screens the rail becomes the header.
 */
export function Shell({
  title,
  crumbs,
  updatedAt,
  meta,
  actions,
  fillViewport = false,
  children,
}: ShellProps) {
  const hasActions = actions != null;

  return (
    <div
      className={cn(
        "flex min-h-dvh flex-col bg-black font-sans text-stone-100",
        fillViewport &&
          "h-[max(100dvh,30rem)] overflow-x-clip lg:block lg:h-auto",
      )}
    >
      <div className="mx-auto flex w-full max-w-6xl min-h-0 flex-1 flex-col px-5 lg:block lg:px-10">
        <div className="flex min-w-0 min-h-0 flex-1 flex-col lg:flex-row lg:gap-16">
          <ShellRail
            title={title}
            crumbs={crumbs}
            updatedAt={updatedAt}
            meta={meta}
            actions={actions}
          />

          <main
            className={cn(
              "flex min-w-0 min-h-0 flex-1 flex-col lg:min-h-dvh lg:justify-center lg:py-14",
              hasActions
                ? "pb-[calc(4.5rem+env(safe-area-inset-bottom))] lg:pb-14"
                : "pb-14",
            )}
          >
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}
