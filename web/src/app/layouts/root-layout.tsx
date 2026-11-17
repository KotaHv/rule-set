import { useEffect } from "react";
import { Outlet, ScrollRestoration } from "react-router";

/**
 * Root layout. Flags the document as ready once real content has been
 * committed; the static boot screen in index.html fades out on that flag, so
 * the handover always happens over fully opaque content.
 */
export function RootLayout() {
  useEffect(() => {
    document.documentElement.dataset.appReady = "true";
  }, []);

  return (
    <div className="min-h-dvh">
      <ScrollRestoration />
      <Outlet />
    </div>
  );
}
