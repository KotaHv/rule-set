import { isRouteErrorResponse, useRouteError } from "react-router";

import { ErrorScreen } from "./error-screen";
import { NotFoundPage } from "./not-found-page";

export function AppErrorBoundary() {
  const error = useRouteError();

  if (isRouteErrorResponse(error) && error.status === 404) {
    return <NotFoundPage />;
  }

  return <ErrorScreen />;
}
