import { Outlet, useLocation, useMatch } from "react-router";

import { TopBar } from "@/app/components/topbar";

export function AppLayout() {
  const { pathname } = useLocation();
  const isHome = useMatch("/") !== null;
  const isClientRoute = useMatch("/:clientSlug/*") !== null;
  // directoryRoute() always ends directory URLs with a slash.
  const isDirectory = isClientRoute && pathname.endsWith("/");

  return (
    <>
      {!isHome && !isDirectory && <TopBar />}
      <main>
        <Outlet />
      </main>
    </>
  );
}
