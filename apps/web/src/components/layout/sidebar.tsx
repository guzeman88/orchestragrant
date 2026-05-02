"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Search,
  Kanban,
  FolderOpen,
  Calendar,
  Settings,
  LogOut,
  Music2,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/ui-store";
import { useAuthStore } from "@/stores/auth-store";
import { authApi } from "@/lib/api";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/grants", label: "Grant Database", icon: Search },
  { href: "/applications", label: "Applications", icon: Kanban },
  { href: "/deadlines", label: "Deadlines", icon: Calendar },
  { href: "/documents", label: "Documents", icon: FolderOpen },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { sidebarCollapsed, toggleSidebar } = useUIStore();
  const { org, clearAuth } = useAuthStore();

  const handleLogout = async () => {
    await authApi.logout().catch(() => {});
    clearAuth();
    router.push("/login");
  };

  return (
    <aside
      className={cn(
        "relative flex flex-col shrink-0 transition-all duration-300 ease-in-out",
        "bg-[#111827] text-white",
        sidebarCollapsed ? "w-[68px]" : "w-[240px]"
      )}
      style={{ boxShadow: "1px 0 0 0 rgba(255,255,255,0.06)" }}
    >
      {/* Logo area */}
      <div
        className={cn(
          "flex items-center gap-3 px-4 py-5 shrink-0",
          sidebarCollapsed && "justify-center px-0"
        )}
        style={{ borderBottom: "1px solid rgba(255,255,255,0.07)" }}
      >
        <div className="h-8 w-8 shrink-0 rounded-lg flex items-center justify-center"
          style={{ background: "linear-gradient(135deg, #7B1F3A 0%, #9B2D4E 100%)" }}>
          <Music2 className="h-4 w-4 text-white" strokeWidth={2} />
        </div>
        {!sidebarCollapsed && (
          <div className="min-w-0">
            <p className="font-serif text-[13px] font-semibold leading-tight text-white truncate tracking-tight">
              OrchestraGrant
            </p>
            {org && (
              <p className="text-[11px] mt-0.5 truncate" style={{ color: "rgba(255,255,255,0.38)" }}>
                {org.name}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href + "/"));
          return (
            <Link
              key={href}
              href={href}
              title={sidebarCollapsed ? label : undefined}
              className={cn(
                "group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] font-medium transition-all duration-150",
                active
                  ? "text-white"
                  : "text-white/50 hover:text-white/80",
                sidebarCollapsed && "justify-center px-2"
              )}
              style={active ? {
                background: "rgba(255,255,255,0.09)",
                boxShadow: "inset 0 0 0 1px rgba(255,255,255,0.06)",
              } : undefined}
            >
              {/* Active indicator bar */}
              {active && (
                <span
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-r-full"
                  style={{ background: "#C9A84C" }}
                />
              )}
              <Icon
                className={cn("shrink-0 transition-colors", active ? "text-[#C9A84C]" : "text-white/40 group-hover:text-white/60")}
                size={15}
                strokeWidth={active ? 2.2 : 1.8}
              />
              {!sidebarCollapsed && <span>{label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="shrink-0 px-2 py-3 space-y-0.5" style={{ borderTop: "1px solid rgba(255,255,255,0.07)" }}>
        <button
          onClick={handleLogout}
          title={sidebarCollapsed ? "Sign Out" : undefined}
          className={cn(
            "group flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] font-medium transition-all duration-150",
            "text-white/40 hover:text-white/70 hover:bg-white/05",
            sidebarCollapsed && "justify-center px-2"
          )}
        >
          <LogOut className="shrink-0 text-white/30 group-hover:text-white/50 transition-colors" size={14} strokeWidth={1.8} />
          {!sidebarCollapsed && <span>Sign Out</span>}
        </button>

        <button
          onClick={toggleSidebar}
          title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          className={cn(
            "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-[13px] transition-all duration-150",
            "text-white/25 hover:text-white/50 hover:bg-white/05",
            sidebarCollapsed && "justify-center px-2"
          )}
        >
          {sidebarCollapsed ? (
            <ChevronRight size={13} strokeWidth={1.8} />
          ) : (
            <>
              <ChevronLeft size={13} strokeWidth={1.8} />
              <span>Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
