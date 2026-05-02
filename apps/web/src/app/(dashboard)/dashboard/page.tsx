"use client";

import { useQuery } from "@tanstack/react-query";
import { DollarSign, FileText, TrendingUp, Clock, ChevronRight, ArrowUpRight } from "lucide-react";
import Link from "next/link";
import { useAuthStore } from "@/stores/auth-store";
import { applicationsApi, deadlinesApi } from "@/lib/api";
import { formatCurrency, formatDate, daysUntil } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { Application, Deadline } from "@orchestragrant/types";

const STAGE_COLORS: Record<string, string> = {
  research: "bg-slate-100 text-slate-600",
  drafting: "bg-blue-50 text-blue-600",
  internal_review: "bg-violet-50 text-violet-600",
  submitted: "bg-amber-50 text-amber-700",
  under_review: "bg-orange-50 text-orange-600",
  awarded: "bg-emerald-50 text-emerald-700",
  declined: "bg-red-50 text-red-600",
  no_response: "bg-gray-50 text-gray-500",
};

function KpiCard({
  title,
  value,
  sub,
  icon: Icon,
  gradient,
  trend,
}: {
  title: string;
  value: string | number;
  sub?: string;
  icon: React.ElementType;
  gradient: string;
  trend?: string;
}) {
  return (
    <div
      className="relative overflow-hidden rounded-xl bg-white p-5 flex flex-col gap-4"
      style={{ boxShadow: "0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.04)", border: "1px solid hsl(220 18% 91%)" }}
    >
      {/* Icon */}
      <div className="flex items-center justify-between">
        <div
          className="h-9 w-9 rounded-lg flex items-center justify-center shrink-0"
          style={{ background: gradient }}
        >
          <Icon size={16} className="text-white" strokeWidth={2} />
        </div>
        {trend && (
          <span className="flex items-center gap-0.5 text-[11px] font-medium text-emerald-600">
            <ArrowUpRight size={11} />
            {trend}
          </span>
        )}
      </div>

      {/* Value */}
      <div>
        <p className="text-2xl font-bold text-foreground tracking-tight leading-none">{value}</p>
        <p className="text-[11px] text-foreground/40 mt-1 font-medium uppercase tracking-wider">{title}</p>
        {sub && <p className="text-xs text-foreground/50 mt-0.5">{sub}</p>}
      </div>

      {/* Subtle gradient accent in top-right corner */}
      <div
        className="pointer-events-none absolute -top-6 -right-6 h-20 w-20 rounded-full opacity-[0.07]"
        style={{ background: gradient }}
      />
    </div>
  );
}

const ACTIVE_STAGES = ["research", "drafting", "internal_review", "submitted", "under_review"];
const AWARDED_STAGE = "awarded";

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const org = useAuthStore((s) => s.org);

  const { data: applicationsData } = useQuery({
    queryKey: ["applications"],
    queryFn: () => applicationsApi.list({ page_size: 200 }),
  });

  const { data: deadlinesData } = useQuery({
    queryKey: ["deadlines", "upcoming"],
    queryFn: () => deadlinesApi.list(true),
  });

  const allApps: Application[] = applicationsData?.items ?? [];
  const deadlines: Deadline[] = deadlinesData ?? [];

  const activeCount = allApps.filter((a) => ACTIVE_STAGES.includes(a.stage)).length;
  const awardedApps = allApps.filter((a) => a.stage === AWARDED_STAGE);
  const totalAwarded = awardedApps.reduce((sum, a) => sum + (a.awarded_amount ?? 0), 0);
  const submittedCount = allApps.filter((a) =>
    ["submitted", "under_review", "awarded", "declined"].includes(a.stage)
  ).length;
  const wonCount = awardedApps.length;
  const winRate = submittedCount > 0 ? Math.round((wonCount / submittedCount) * 100) : 0;
  const upcomingCount = deadlines.filter((d) => !d.completed_at).length;

  const recentApps = [...allApps]
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
    .slice(0, 6);

  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  return (
    <div className="p-7 space-y-7 max-w-[1400px]">
      {/* Greeting */}
      <div className="flex items-end justify-between">
        <div>
          <h2 className="font-serif text-2xl font-semibold text-foreground leading-tight">
            {greeting}, {user?.first_name}.
          </h2>
          <p className="text-sm text-foreground/45 mt-1">{org?.name} &mdash; {new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}</p>
        </div>
        <Link
          href="/grants"
          className="inline-flex items-center gap-2 text-[12px] font-medium text-white rounded-lg px-4 py-2 transition-all duration-150 hover:opacity-90"
          style={{ background: "linear-gradient(135deg, #7B1F3A 0%, #9B2D4E 100%)" }}
        >
          Discover Grants <ArrowUpRight size={12} />
        </Link>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          title="Active Applications"
          value={activeCount}
          sub={`${allApps.length} total across all stages`}
          icon={FileText}
          gradient="linear-gradient(135deg, #7B1F3A 0%, #9B2D4E 100%)"
        />
        <KpiCard
          title="Awarded YTD"
          value={formatCurrency(totalAwarded)}
          sub={`${awardedApps.length} grant${awardedApps.length !== 1 ? "s" : ""} secured`}
          icon={DollarSign}
          gradient="linear-gradient(135deg, #B8922A 0%, #C9A84C 100%)"
        />
        <KpiCard
          title="Win Rate"
          value={`${winRate}%`}
          sub={`${wonCount} of ${submittedCount} submitted`}
          icon={TrendingUp}
          gradient="linear-gradient(135deg, #1B2E4B 0%, #2A4570 100%)"
        />
        <KpiCard
          title="Upcoming Deadlines"
          value={upcomingCount}
          sub="requiring attention"
          icon={Clock}
          gradient="linear-gradient(135deg, #C84B31 0%, #E05C3E 100%)"
        />
      </div>

      {/* Bottom two-column section */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">

        {/* Upcoming deadlines */}
        <div
          className="rounded-xl bg-white overflow-hidden"
          style={{ boxShadow: "0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.04)", border: "1px solid hsl(220 18% 91%)" }}
        >
          <div className="flex items-center justify-between px-5 py-4" style={{ borderBottom: "1px solid hsl(220 18% 93%)" }}>
            <div>
              <h3 className="text-[13px] font-semibold text-foreground">Upcoming Deadlines</h3>
              <p className="text-[11px] text-foreground/40 mt-0.5">{upcomingCount} pending</p>
            </div>
            <Link href="/applications" className="flex items-center gap-1 text-[11px] font-medium text-og-burgundy hover:opacity-70 transition-opacity">
              View all <ChevronRight size={11} />
            </Link>
          </div>
          <div className="px-5 py-2">
            {deadlines.length === 0 ? (
              <p className="text-sm text-foreground/40 py-6 text-center">No upcoming deadlines</p>
            ) : (
              <ul className="divide-y divide-border/60">
                {deadlines
                  .filter((d) => !d.completed_at)
                  .slice(0, 6)
                  .map((d: Deadline) => {
                    const days = daysUntil(d.deadline_at);
                    const urgent = days >= 0 && days <= 7;
                    const warning = days > 7 && days <= 14;
                    return (
                      <li key={d.id} className="flex items-center justify-between py-3 gap-4">
                        <div className="flex items-center gap-2.5 min-w-0">
                          <div
                            className={cn("shrink-0 h-1.5 w-1.5 rounded-full", urgent ? "bg-red-500" : warning ? "bg-amber-500" : "bg-foreground/20")}
                          />
                          <span className="text-[13px] text-foreground/80 truncate">{d.title}</span>
                        </div>
                        <span
                          className={cn(
                            "shrink-0 text-[11px] font-semibold tabular-nums px-2 py-0.5 rounded-md",
                            days < 0
                              ? "bg-foreground/5 text-foreground/40"
                              : urgent
                              ? "bg-red-50 text-red-600"
                              : warning
                              ? "bg-amber-50 text-amber-700"
                              : "bg-foreground/5 text-foreground/50"
                          )}
                        >
                          {days < 0 ? "Overdue" : days === 0 ? "Today" : `${days}d`}
                        </span>
                      </li>
                    );
                  })}
              </ul>
            )}
          </div>
        </div>

        {/* Recent applications */}
        <div
          className="rounded-xl bg-white overflow-hidden"
          style={{ boxShadow: "0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.04)", border: "1px solid hsl(220 18% 91%)" }}
        >
          <div className="flex items-center justify-between px-5 py-4" style={{ borderBottom: "1px solid hsl(220 18% 93%)" }}>
            <div>
              <h3 className="text-[13px] font-semibold text-foreground">Recent Applications</h3>
              <p className="text-[11px] text-foreground/40 mt-0.5">{allApps.length} total</p>
            </div>
            <Link href="/applications" className="flex items-center gap-1 text-[11px] font-medium text-og-burgundy hover:opacity-70 transition-opacity">
              View all <ChevronRight size={11} />
            </Link>
          </div>
          <div className="px-5 py-2">
            {recentApps.length === 0 ? (
              <p className="text-sm text-foreground/40 py-6 text-center">No applications yet</p>
            ) : (
              <ul className="divide-y divide-border/60">
                {recentApps.map((app) => (
                  <li key={app.id} className="flex items-center justify-between py-3 gap-4">
                    <Link
                      href={`/applications/${app.id}`}
                      className="text-[13px] text-foreground/80 hover:text-og-burgundy transition-colors truncate"
                    >
                      {app.title}
                    </Link>
                    <span className={cn("shrink-0 text-[11px] font-medium px-2 py-0.5 rounded-md capitalize", STAGE_COLORS[app.stage] ?? "bg-muted text-muted-foreground")}>
                      {app.stage.replace(/_/g, " ")}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}

