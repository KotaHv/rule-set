import { Shell } from "@/app/components/shell";
import { LocalTime } from "@/components/shared/local-time";
import { ClientList } from "@/features/rules/components/client-list";
import { useManifest } from "@/features/rules/hooks/use-manifest";

export function HomePage() {
  const manifest = useManifest();

  return (
    <>
      <title>Rule Set - 规则集</title>
      <Shell
        title="Rule Set"
        meta={
          <>
            <p className="text-xs tracking-[0.12em] text-stone-500">
              最近更新
            </p>
            <LocalTime
              timestamp={manifest.latestUpdate}
              className="mt-1.5 block font-mono text-[15px] leading-6 tracking-tight text-stone-400"
            />
          </>
        }
      >
        <ClientList clients={manifest.clients} />
      </Shell>
    </>
  );
}
