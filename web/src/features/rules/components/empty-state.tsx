import { InboxIcon } from "lucide-react";

interface EmptyStateProps {
  title?: string;
  description?: string;
}

export function EmptyState({
  title = "目录为空",
  description = "此目录中没有任何文件或子目录",
}: EmptyStateProps) {
  return (
    <div className="py-20 text-center">
      <div className="mx-auto mb-6 flex size-20 items-center justify-center rounded-full bg-white/4 ring-1 ring-white/10">
        <InboxIcon className="size-10 text-stone-500" strokeWidth={1.5} />
      </div>
      <h2 className="mb-3 text-2xl font-medium text-stone-200">{title}</h2>
      <p className="text-stone-400">{description}</p>
    </div>
  );
}
