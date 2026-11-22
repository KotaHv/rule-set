import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

interface StatusScreenProps {
  icon: LucideIcon;
  eyebrow: string;
  title: string;
  description?: string;
  children?: ReactNode;
}

export function StatusScreen({
  icon: Icon,
  eyebrow,
  title,
  description,
  children,
}: StatusScreenProps) {
  return (
    <main className="grid min-h-dvh place-items-center p-6">
      <section className="w-full max-w-sm space-y-4 text-center">
        <div className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-white/4 text-stone-400 ring-1 ring-white/10">
          <Icon aria-hidden="true" className="size-6" />
        </div>
        <p className="text-sm font-semibold text-stone-400 uppercase">
          {eyebrow}
        </p>
        <h1 className="text-2xl font-semibold text-stone-100">{title}</h1>
        {description && (
          <p className="text-sm leading-6 text-stone-400">{description}</p>
        )}
        {children && (
          <div className="flex flex-wrap justify-center gap-3">
            {children}
          </div>
        )}
      </section>
    </main>
  );
}
