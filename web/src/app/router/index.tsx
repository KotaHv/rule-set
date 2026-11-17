import { createHashRouter } from "react-router";

import { AppLayout } from "@/app/layouts/app-layout";
import { RootLayout } from "@/app/layouts/root-layout";
import { DirectoryPage } from "@/app/routes/directory";
import { HomePage } from "@/app/routes/home";
import {
  DIRECTORY_ROUTE_ID,
  loadDirectoryPage,
} from "@/features/rules/api/directory";
import { loadManifest, MANIFEST_ROUTE_ID } from "@/features/rules/api/manifest";
import { AppErrorBoundary } from "./app-error-boundary";

/**
 * The static boot screen in index.html covers the app while the manifest
 * loader runs, so the router's hydration fallback stays empty.
 */
export const router = createHashRouter([
  {
    Component: RootLayout,
    hydrateFallbackElement: <></>,
    children: [
      {
        id: MANIFEST_ROUTE_ID,
        path: "/",
        loader: loadManifest,
        ErrorBoundary: AppErrorBoundary,
        Component: AppLayout,
        children: [
          { index: true, Component: HomePage },
          {
            id: DIRECTORY_ROUTE_ID,
            path: ":clientSlug/*",
            loader: loadDirectoryPage,
            Component: DirectoryPage,
          },
        ],
      },
    ],
  },
]);
