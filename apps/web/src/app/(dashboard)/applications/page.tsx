"use client";

import { useQuery } from "@tanstack/react-query";
import { Plus, ArrowUpRight } from "lucide-react";
import Link from "next/link";
import { applicationsApi } from "@/lib/api";
import { cn } from "@/lib/utils";
import { formatCurrency } from "@/lib/utils";
import type { Application } from "@orchestragrant/types";

const STAGE_ORDER = [
  "prospecting",
  "qualifying",
  "writing",
  "internal_review",
  "director_review",
  "board_approval",
  "ready_to_submit",
  "submitted",
  "under_review",
  "awarded",
  "declined",
];

const STAGE_LABELS: Record<string, string> = {
  prospecting:      "Prospecting",
  qualifying:       "Qualifying",
  writing:          "Writing",
  internal_review:  "Internal Review",
  director_review:  "Director Review",
  board_approval:   "Board Approval",
  ready_to_submit:  "Ready to Submit",
  submitted:        "Submitted",
  under_review:     "Under Review",
  awarded:          "Awarded",
  declined:         "Declined",
};

const STAGE_STYLES: Record<string, { dot: string; header: string; count: string }> = {
  prospecting:     { dot: "bg-slate-400",   header: "bg-slate-50 border-slate-200",     count: "text-slate-500 bg-slate-100" },
  qualifying:      { dot: "bg-sky-400",     header: "bg-sky-50 border-sky-200",         count: "text-sky-600 bg-sky-100" },
  writing:         { dot: "bg-blue-400",    header: "bg-blue-50 border-blue-200",       count: "text-blue-600 bg-blue-100" },
  internal_review: { dot: "bg-violet-400",  header: "bg-violet-50 border-violet-200",   count: "text-violet-600 bg-violet-100" },
  director_review: { dot: "bg-purple-400",  header: "bg-purple-50 border-purple-200",   count: "text-purple-600 bg-purple-100" },
  board_approval:  { dot: "bg-fuchsia-400", header: "bg-fuchsia-50 border-fuchsia-200", count: "text-fuchsia-600 bg-fuchsia-100" },
  ready_to_submit: { dot: "bg-teal-400",    header: "bg-teal-50 border-teal-200",       count: "text-teal-700 bg-teal-100" },
  submitted:       { dot: "bg-amber-400",   header: "bg-amber-50 border-amber-200",     count: "text-amber-700 bg-amber-100" },
  under_review:    { dot: "bg-orange-400",  header: "bg-orange-50 border-orange-200",   count: "text-orange-600 bg-orange-100" },
  awarded:         { dot: "bg-emerald-500", header: "bg-emerald-50 border-emerald-200", count: "text-emerald-700 bg-emerald-100" },
  declined:        { dot: "bg-red-400",     header: "bg-red-50 border-red-200",         count: "text-red-600 bg-red-100" },
};

// Demo data for display without backend

export default function ApplicationsPage() {
  const { data } = useQuery({
    queryKey: ["applications"],
    queryFn: () => applicationsApi.list({ page_size: 200 }),
  });

  const apps: Application[] = data?.items ?? [];

  const byStage = STAGE_ORDER.reduce<Record<string, Application[]>>((acc, s) => {
    acc[s] = apps.filter((a) => a.stage === s);
    return acc;
  }, {});

  const totalAwarded = apps.filter((a) => a.stage === "awarded").reduce((s, a) => s + ((a as any).awarded_amount ?? 0), 0);

  return (
    <div className="flex flex-col h-full">
      {/* Page header */}
      <div className="px-7 pt-7 pb-4 shrink-0 flex items-end justify-between">
        <div>
          <h2 className="font-serif text-2xl font-semibold text-foreground leading-tight">Applications</h2>
          <p className="text-sm text-foreground/45 mt-1">
            {apps.length} total &mdash; {formatCurrency(totalAwarded)} awarded
          </p>
        </div>
        <Link
          href="/grants"
          className="inline-flex items-center gap-2 text-[12px] font-medium text-white rounded-lg px-4 py-2 transition-all duration-150 hover:opacity-90"
          style={{ background: "linear-gradient(135deg, #7B1F3A 0%, #9B2D4E 100%)" }}
        >
          <Plus size={13} /> New Application
        </Link>
      </div>

      {/* Kanban board — horizontal scroll */}
      <div className="flex-1 overflow-x-auto overflow-y-hidden px-7 pb-7">
        <div className="flex gap-3 h-full min-h-[calc(100vh-200px)]" style={{ width: "max-content" }}>
          {STAGE_ORDER.map((stage) => {
            const style = STAGE_STYLES[stage];
            const stageApps = byStage[stage];
            return (
              <div key={stage} className="flex flex-col w-[220px] shrink-0">
                {/* Column header */}
                <div
                  className={cn("flex items-center justify-between px-3 py-2.5 rounded-t-xl border-b-0 border", style.header)}
                >
                  <div className="flex items-center gap-2">
                    <span className={cn("h-1.5 w-1.5 rounded-full shrink-0", style.dot)} />
                    <span className="text-[11px] font-semibold tracking-wide text-foreground/70">
                      {STAGE_LABELS[stage]}
                    </span>
                  </div>
                  <span className={cn("text-[10px] font-bold px-1.5 py-0.5 rounded-md tabular-nums", style.count)}>
                    {stageApps.length}
                  </span>
                </div>

                {/* Cards */}
                <div
                  className="flex-1 overflow-y-auto rounded-b-xl p-2 space-y-2"
                  style={{ background: "hsl(220 17% 96%)", border: "1px solid hsl(220 18% 89%)", borderTop: "none" }}
                >
                  {stageApps.length === 0 && (
                    <div className="flex items-center justify-center h-16 text-[11px] text-foreground/25 select-none">
                      Empty
                    </div>
                  )}
                  {stageApps.map((app) => (
                    <AppCard key={app.id} app={app} />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function AppCard({ app }: { app: Application }) {
  return (
    <Link href={`/applications/${app.id}`} className="block group">
      <div
        className="rounded-lg bg-white p-3 space-y-2.5 transition-all duration-150 group-hover:shadow-md group-hover:-translate-y-px"
        style={{ border: "1px solid hsl(220 18% 91%)", boxShadow: "0 1px 2px 0 rgb(0 0 0 / 0.04)" }}
      >
        <p className="text-[12px] font-semibold leading-snug text-foreground/90 line-clamp-2 group-hover:text-og-burgundy transition-colors">
          {app.title}
        </p>
        {app.requested_amount && (
          <p className="text-[11px] font-medium" style={{ color: "#7B1F3A" }}>
            {formatCurrency(app.requested_amount)}
          </p>
        )}
        {app.stage === "awarded" && (app as any).awarded_amount && (
          <div className="flex items-center gap-1">
            <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded-md">
              Awarded {formatCurrency((app as any).awarded_amount)}
            </span>
          </div>
        )}
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-foreground/30 font-medium">
            {app.updated_at ? new Date(app.updated_at).toLocaleDateString("en-US", { month: "short", day: "numeric" }) : ""}
          </span>
          <ArrowUpRight size={11} className="text-foreground/20 group-hover:text-og-burgundy transition-colors" />
        </div>
      </div>
    </Link>
  );
}

