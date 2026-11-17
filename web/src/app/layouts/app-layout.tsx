import { Outlet } from "react-router";

import { TopBar } from "@/app/components/topbar";

export function AppLayout() {
  return (
    <>
      <TopBar />
      <main>
        <Outlet />
      </main>
    </>
  );
}
