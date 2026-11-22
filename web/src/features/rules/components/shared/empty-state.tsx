interface EmptyStateProps {
  title?: string;
  description?: string;
}

export function EmptyState({
  title = "目录为空",
  description = "此目录中没有任何文件或子目录",
}: EmptyStateProps) {
  return (
    <div className="py-10">
      <h2 className="text-xl font-semibold text-stone-100">{title}</h2>
      <p className="mt-2 max-w-prose text-stone-400">{description}</p>
    </div>
  );
}
