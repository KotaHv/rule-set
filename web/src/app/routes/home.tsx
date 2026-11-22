import { FilesIcon } from "lucide-react";

import { Shell } from "@/app/components/shell";
import { GitHubIcon } from "@/components/shared/github-icon";
import { MetaItem } from "@/components/shared/meta-item";
import { ClientList } from "@/features/rules/components/client/client-list";
import { useManifest } from "@/features/rules/hooks/use-manifest";
import { manifestStats } from "@/features/rules/utils/stats";
import { formatFileSize } from "@/utils/format";

export function HomePage() {
  const manifest = useManifest();
  const stats = manifestStats(manifest.clients);

  return (
    <>
      <title>Rule Set - 规则集</title>
      <Shell
        title="Rule Set"
        updatedAt={manifest.latestUpdate}
        meta={
          <div className="flex flex-col gap-4">
            <MetaItem icon={FilesIcon}>
              {stats.files.toLocaleString()} 个文件 ·{" "}
              {formatFileSize(stats.size)}
            </MetaItem>
            <MetaItem icon={GitHubIcon} asChild>
              <a
                href="https://github.com/KotaHv/rule-set"
                target="_blank"
                rel="noreferrer"
                aria-label="在 GitHub 上查看项目"
              >
                GitHub
              </a>
            </MetaItem>
          </div>
        }
      >
        <ClientList clients={manifest.clients} />
      </Shell>
    </>
  );
}
