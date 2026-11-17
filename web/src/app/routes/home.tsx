import { DirectoryCard } from "@/features/rules/components/directory-card";
import { EmptyState } from "@/features/rules/components/empty-state";
import { useManifest } from "@/features/rules/hooks/use-manifest";

export function HomePage() {
  const manifest = useManifest();

  return (
    <>
      <title>Rule Set - 规则集</title>
      <h1 className="sr-only">Rule Set</h1>
      <div className="mx-auto max-w-6xl px-6 py-12 lg:px-8">
        {manifest.clients.length > 0 ? (
          <ul className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {manifest.clients.map((client) => (
              <li key={client.slug} className="h-full">
                <DirectoryCard client={client} />
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState title="没有规则" description="规则集目录是空的" />
        )}
      </div>
    </>
  );
}
