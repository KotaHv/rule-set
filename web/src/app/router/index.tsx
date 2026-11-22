import { createHashRouter } from "react-router";

import { RootLayout } from "@/app/layouts/root-layout";
import { BrowserPage } from "@/app/routes/browser";
import { HomePage } from "@/app/routes/home";
import {
  BROWSER_ROUTE_ID,
  loadBrowserPage,
} from "@/features/rules/api/browser";
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
        children: [
          { index: true, Component: HomePage },
          {
            id: BROWSER_ROUTE_ID,
            path: ":clientSlug/*",
            loader: loadBrowserPage,
            Component: BrowserPage,
          },
        ],
      },
    ],
  },
]);
