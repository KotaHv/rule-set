import type { ReactNode } from "react";

import { ChevronRightIcon } from "lucide-react";
import { cn } from "cn";
import { Link } from "react-router";

interface ItemCardProps {
  to: string;
  /** Glyph shown inside the leading tile. */
  tile: ReactNode;
  title: ReactNode;
  /** Exactly two facts: the tuple keeps the two columns aligned from `sm` up. */
  meta: [ReactNode, ReactNode];
  /** Independent control that stays clickable on top of the card link. */
  action?: ReactNode;
}

export function ItemCard({
  to,
  tile,
  title,
  meta: [primaryMeta, secondaryMeta],
  action,
}: ItemCardProps) {
  return (
    <li
      className={cn(
        "group relative flex items-center gap-3 rounded-2xl border border-white/15 bg-white/6 px-3 py-2 transition-colors hover:border-stone-100/20 hover:bg-white/10 active:bg-white/12",
        "has-[a:focus-visible]:outline-2 has-[a:focus-visible]:outline-offset-2 has-[a:focus-visible]:outline-white",
      )}
    >
      <span
        aria-hidden="true"
        className="grid size-10 shrink-0 place-items-center rounded-[22%] bg-white/10 sm:size-11"
      >
        {tile}
      </span>

      <div className="min-w-0 flex-1 sm:flex sm:items-center sm:gap-6">
        <div className="min-w-0 text-lg leading-tight font-semibold tracking-tight wrap-anywhere sm:flex-1">
          <Link
            to={to}
            className="after:absolute after:inset-0 after:rounded-2xl focus-visible:outline-none"
          >
            {title}
          </Link>
        </div>

        <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 sm:mt-0 sm:grid sm:shrink-0 sm:grid-cols-[5.5rem_11rem] sm:gap-x-4">
          {primaryMeta}
          {secondaryMeta}
        </div>
      </div>

      {action ? (
        <div className="relative z-10 shrink-0">{action}</div>
      ) : (
        <ChevronRightIcon
          aria-hidden="true"
          className="size-5 shrink-0 text-stone-500 transition-colors group-hover:text-stone-100"
        />
      )}
    </li>
  );
}
