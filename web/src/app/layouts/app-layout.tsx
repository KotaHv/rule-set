import { Outlet, useMatch } from "react-router";

import { TopBar } from "@/app/components/topbar";

export function AppLayout() {
  const isHome = useMatch("/") !== null;

  return (
    <>
      {!isHome && <TopBar />}
      <main>
        <Outlet />
      </main>
    </>
  );
}
