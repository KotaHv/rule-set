import { AlertTriangleIcon, RotateCwIcon } from "lucide-react";
import { useRevalidator, useRouteError } from "react-router";

import { cn } from "cn";

import { StatusScreen } from "@/app/components/status-screen";
import { Button } from "@/components/ui/button";
import { ManifestHttpError } from "@/features/rules/api/manifest";

function errorDescription(error: unknown): string {
  if (error instanceof TypeError) {
    return "网络连接失败，请检查网络后重试";
  }

  if (error instanceof SyntaxError) {
    return "规则数据格式不正确，请稍后重试";
  }

  if (error instanceof ManifestHttpError) {
    return "服务暂时不可用，请稍后重试";
  }

  return "规则数据加载失败，请稍后重试";
}

export function ErrorScreen() {
  const error = useRouteError();
  const revalidator = useRevalidator();
  const retrying = revalidator.state !== "idle";

  return (
    <>
      <title>加载失败 - Rule Set</title>
      <StatusScreen
        icon={AlertTriangleIcon}
        eyebrow="Error"
        title="无法加载规则列表"
        description={errorDescription(error)}
      >
        <Button
          type="button"
          onClick={() => revalidator.revalidate()}
          disabled={retrying}
          aria-busy={retrying || undefined}
          size="lg"
        >
          <RotateCwIcon
            aria-hidden="true"
            className={cn("size-4", retrying && "motion-safe:animate-spin")}
          />
          {retrying ? "重试中" : "重试"}
        </Button>
      </StatusScreen>
    </>
  );
}
