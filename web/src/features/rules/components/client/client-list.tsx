import type { ManifestClient } from "@/types/manifest";
import { ClientRow } from "./client-row";

interface ClientListProps {
  clients: ManifestClient[];
}

export function ClientList({ clients }: ClientListProps) {
  if (clients.length === 0) {
    return (
      <p className="border border-white/15 px-4 py-10 text-sm text-stone-400">
        规则集目录是空的。
      </p>
    );
  }

  return (
    <ul aria-label="客户端" className="space-y-3">
      {clients.map((client) => (
        <li key={client.slug}>
          <ClientRow client={client} />
        </li>
      ))}
    </ul>
  );
}
