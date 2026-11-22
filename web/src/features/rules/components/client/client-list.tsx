import type { ManifestClient } from "@/types/manifest";
import { ClientRow } from "./client-row";

interface ClientListProps {
  clients: ManifestClient[];
}

export function ClientList({ clients }: ClientListProps) {
  return (
    <ul
      aria-label="客户端"
      className="grid grid-cols-[repeat(auto-fit,minmax(min(19rem,100%),1fr))] gap-3"
    >
      {clients.map((client) => (
        <li key={client.slug} className="h-full">
          <ClientRow client={client} />
        </li>
      ))}
    </ul>
  );
}
