import { ChevronRightIcon } from "lucide-react";
import { Link } from "react-router";

import type { Crumb } from "@/features/rules/utils/crumbs";

export function Breadcrumbs({ crumbs }: { crumbs: Crumb[] }) {
  if (crumbs.length === 0) {
    return null;
  }

  return (
    <nav aria-label="当前位置" className="mt-4 min-w-0">
      <ol className="flex flex-wrap items-center text-base text-stone-400">
        {crumbs.map((crumb, index) => (
          <li key={crumb.to ?? "current"} className="flex items-center">
            {index > 0 && (
              <ChevronRightIcon
                aria-hidden="true"
                className="mx-0.5 size-4 shrink-0 text-stone-600"
              />
            )}
            {crumb.to ? (
              <Link
                to={crumb.to}
                className="relative flex items-center rounded-lg px-2 transition-colors before:absolute before:-inset-y-2.5 before:inset-x-0 before:content-[''] hover:text-stone-100 focus-visible:ring-2 focus-visible:ring-stone-100/40 focus-visible:outline-none"
              >
                {crumb.label}
              </Link>
            ) : (
              <span
                aria-current="page"
                className="flex items-center px-2 text-stone-300"
              >
                {crumb.label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
