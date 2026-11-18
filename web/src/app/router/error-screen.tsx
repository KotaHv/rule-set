import { AlertTriangleIcon, RotateCwIcon } from "lucide-react";
import { useRevalidator, useRouteError } from "react-router";

import { Button } from "@/components/ui/button";
import { manifestErrorMessage } from "@/features/rules/api/manifest";

export function ErrorScreen() {
  const error = useRouteError();
  const revalidator = useRevalidator();
  const retrying = revalidator.state !== "idle";

  return (
    <>
      <title>加载失败 - Rule Set</title>
      <main className="grid min-h-dvh place-items-center p-6">
        <section className="w-full max-w-sm text-center">
          <div className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-white/[0.04] text-stone-400 ring-1 ring-white/10">
            <AlertTriangleIcon className="size-6" />
          </div>
          <p className="mt-4 text-sm font-semibold tracking-[0.2em] text-stone-400 uppercase">
            Error
          </p>
          <h1 className="mt-3 text-2xl font-semibold tracking-tight text-stone-100">
            无法加载规则列表
          </h1>
          <p className="mt-3 text-sm leading-6 text-stone-400">
            {manifestErrorMessage(error)}
          </p>
          <Button
            type="button"
            onClick={() => revalidator.revalidate()}
            disabled={retrying}
            aria-busy={retrying || undefined}
            className="mt-6"
          >
            <RotateCwIcon
              className={retrying ? "motion-safe:animate-spin" : undefined}
            />
            {retrying ? "重试中" : "重试"}
          </Button>
        </section>
      </main>
    </>
  );
}
