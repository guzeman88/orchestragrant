"use client";

import { usePathname } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { Bell } from "lucide-react";

const BREADCRUMB_MAP: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/grants": "Grant Database",
  "/applications": "Applications",
  "/deadlines": "Deadlines",
  "/documents": "Documents",
  "/settings": "Settings",
};

export function Header() {
  const pathname = usePathname();
  const user = useAuthStore((s) => s.user);
  const org = useAuthStore((s) => s.org);

  const label =
    BREADCRUMB_MAP[pathname] ??
    Object.entries(BREADCRUMB_MAP).find(([key]) => pathname.startsWith(key + "/"))?.[1] ??
    "Page";

  const initials = user
    ? `${user.first_name[0]}${user.last_name[0]}`.toUpperCase()
    : "AC";

  return (
    <header
      className="flex h-14 shrink-0 items-center justify-between px-6 bg-white"
      style={{ borderBottom: "1px solid hsl(220 18% 90%)", boxShadow: "0 1px 2px 0 rgb(0 0 0 / 0.03)" }}
    >
      {/* Page title */}
      <div className="flex items-center gap-2.5">
        <h1 className="text-[13px] font-semibold text-foreground/90 tracking-tight">{label}</h1>
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-2">
        {/* Notification bell */}
        <button
          className="relative flex h-8 w-8 items-center justify-center rounded-lg text-foreground/40 hover:text-foreground/70 hover:bg-muted transition-all duration-150"
          aria-label="Notifications"
        >
          <Bell size={15} strokeWidth={1.8} />
          {/* Unread dot */}
          <span className="absolute top-1.5 right-1.5 h-1.5 w-1.5 rounded-full bg-og-burgundy ring-1 ring-white" />
        </button>

        {/* Divider */}
        <div className="h-5 w-px bg-border mx-1" />

        {/* User avatar + info */}
        <div className="flex items-center gap-2.5 cursor-default">
          <div
            className="h-7 w-7 rounded-full flex items-center justify-center text-[11px] font-semibold text-white shrink-0 select-none"
            style={{ background: "linear-gradient(135deg, #7B1F3A 0%, #9B2D4E 100%)" }}
          >
            {initials}
          </div>
          <div className="hidden sm:block leading-none">
            <p className="text-[12px] font-medium text-foreground/90">
              {user?.first_name} {user?.last_name}
            </p>
            <p className="text-[11px] text-foreground/40 mt-0.5 truncate max-w-[160px]">{org?.name}</p>
          </div>
        </div>
      </div>
    </header>
  );
}
