import { ArrowLeftIcon, FileQuestionIcon } from "lucide-react";
import { Link } from "react-router";

import { StatusScreen } from "@/app/components/status-screen";
import { Button } from "@/components/ui/button";

export function NotFoundPage() {
  return (
    <>
      <title>未找到 - Rule Set</title>
      <StatusScreen
        icon={FileQuestionIcon}
        eyebrow="404"
        title="页面不存在"
      >
        <Button asChild size="lg">
          <Link to="/">
            <ArrowLeftIcon aria-hidden="true" className="size-4" />
            返回首页
          </Link>
        </Button>
      </StatusScreen>
    </>
  );
}
