import { useLoaderData } from "react-router";

import type { loadBrowserPage } from "@/features/rules/api/browser";
import { DirectoryPage } from "./directory";
import { FilePage } from "./file";

export function BrowserPage() {
  const data = useLoaderData<typeof loadBrowserPage>();

  return data.type === "directory" ? (
    <DirectoryPage data={data} />
  ) : (
    // Remount on navigation so copy status and scroll reset.
    <FilePage key={data.node.path} data={data} />
  );
}
