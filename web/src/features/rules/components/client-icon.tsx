import { cn } from "cn";
import { LayersIcon } from "lucide-react";

import clashIcon from "@/assets/icons/clash.svg";
import egernIcon from "@/assets/icons/egern.svg";
import loonIcon from "@/assets/icons/loon.svg";
import singBoxIcon from "@/assets/icons/sing-box.svg";
import surgeIcon from "@/assets/icons/surge.svg";
import type { ClientSlug } from "@/types/manifest";

const CLIENT_ICONS: Partial<Record<ClientSlug, string>> = {
  clash: clashIcon,
  egern: egernIcon,
  loon: loonIcon,
  "sing-box": singBoxIcon,
  surge: surgeIcon,
};

interface ClientIconProps {
  name: ClientSlug;
  className?: string;
}

export function ClientIcon({ name, className }: ClientIconProps) {
  const icon = CLIENT_ICONS[name];
  if (icon) {
    return <img src={icon} alt="" className={cn("size-8", className)} />;
  }

  if (name === "geoip") {
    return (
      <svg
        className={cn("size-8", className)}
        fill="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
      </svg>
    );
  }

  return <LayersIcon className={cn("size-8", className)} strokeWidth={1.5} />;
}
