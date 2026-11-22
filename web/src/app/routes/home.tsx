import { Shell } from "@/app/components/shell";
import { ClientList } from "@/features/rules/components/client/client-list";
import { useManifest } from "@/features/rules/hooks/use-manifest";

export function HomePage() {
  const manifest = useManifest();

  return (
    <>
      <title>Rule Set - 规则集</title>
      <Shell title="Rule Set" updatedAt={manifest.latestUpdate}>
        <ClientList clients={manifest.clients} />
      </Shell>
    </>
  );
}
