import { ArrowLeftIcon, FileQuestionIcon } from "lucide-react";
import { Link } from "react-router";

import { Button } from "@/components/ui/button";

export function NotFoundPage() {
  return (
    <>
      <title>未找到 - Rule Set</title>
      <main className="grid min-h-dvh place-items-center p-6">
        <section className="w-full max-w-sm text-center">
          <div className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-white/4 text-stone-400 ring-1 ring-white/10">
            <FileQuestionIcon className="size-6" />
          </div>
          <p className="mt-4 text-sm font-semibold tracking-[0.2em] text-stone-400 uppercase">
            404
          </p>
          <h1 className="mt-3 text-2xl font-semibold tracking-tight text-stone-100">
            页面不存在
          </h1>
          <Button asChild className="mt-6">
            <Link to="/">
              <ArrowLeftIcon />
              返回首页
            </Link>
          </Button>
        </section>
      </main>
    </>
  );
}
