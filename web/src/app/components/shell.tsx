import type { ReactNode } from "react";
import { Link } from "react-router";

import { Breadcrumbs } from "@/app/components/breadcrumbs";
import type { Crumb } from "@/features/rules/utils/crumbs";

const LOGO_URL = `${import.meta.env.BASE_URL}logo.webp`;

interface ShellProps {
  title: string;
  crumbs?: Crumb[];
  meta?: ReactNode;
  children: ReactNode;
}

function ShellMeta({ children }: { children?: ReactNode }) {
  if (!children) {
    return null;
  }

  return (
    <div className="mt-4 text-sm leading-5 text-stone-500">{children}</div>
  );
}

function ShellRail({ title, crumbs = [], meta }: Omit<ShellProps, "children">) {
  return (
    <header className="py-5 lg:sticky lg:top-0 lg:flex lg:h-dvh lg:w-88 lg:shrink-0 lg:flex-col lg:justify-center lg:py-14">
      <div className="flex items-center gap-3 lg:gap-4">
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

      <ShellMeta>{meta}</ShellMeta>
    </header>
  );
}

/**
 * The shared frame for the rule index. The left rail stays put on large
 * screens while the content scrolls; on small screens it becomes the header.
 */
export function Shell({ title, crumbs, meta, children }: ShellProps) {
  return (
    <div className="min-h-dvh bg-black font-sans text-stone-100">
      <div className="mx-auto max-w-6xl px-5 lg:px-10">
        <div className="lg:flex lg:gap-16">
          <ShellRail title={title} crumbs={crumbs} meta={meta} />

          <div className="min-w-0 flex-1 pb-14 lg:flex lg:min-h-dvh lg:flex-col lg:justify-center lg:py-14">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
