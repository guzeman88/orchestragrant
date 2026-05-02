"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft, Star, ExternalLink, Building2,
  CheckCircle2, XCircle, AlertCircle,
  FileText, Users, BarChart3, Clock, BadgeCheck,
} from "lucide-react";
import Link from "next/link";
import { grantsApi, applicationsApi } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

const FUNDER_TYPE_LABELS: Record<string, string> = {
  federal_government: "Federal Government",
  government_federal: "Federal Government",
  state_government: "State Government",
  government_state: "State Government",
  local_government: "Local Government",
  private_foundation: "Private Foundation",
  foundation: "Private Foundation",
  corporate: "Corporate",
  community_foundation: "Community Foundation",
  individual_donor: "Individual Donor",
};

const GRANT_TYPE_LABELS: Record<string, string> = {
  general_operating: "General Operating",
  project: "Project Support",
  capital: "Capital",
  endowment: "Endowment",
  commission: "Commission",
  residency: "Residency",
  education: "Education",
  technical_assistance: "Technical Assistance",
};

const ORG_TYPE_LABELS: Record<string, string> = {
  symphony: "Symphony",
  chamber_orchestra: "Chamber Orchestra",
  opera: "Opera",
  chorus: "Chorus",
  performing_arts: "Performing Arts",
  other: "Other",
};

const CYCLE_LABELS: Record<string, string> = {
  annual: "Annual",
  biannual: "Twice a year",
  rolling: "Rolling",
  one_time: "One-time",
};

function daysUntil(d: string | Date): number {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const target = new Date(d);
  target.setHours(0, 0, 0, 0);
  return Math.round((target.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
}

function BoolBadge({ value, trueLabel, falseLabel }: { value: boolean; trueLabel: string; falseLabel?: string }) {
  return value ? (
    <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700">
      <CheckCircle2 size={10} /> {trueLabel}
    </span>
  ) : falseLabel ? (
    <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-foreground/5 text-foreground/40">
      <XCircle size={10} /> {falseLabel}
    </span>
  ) : null;
}

function Section({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div
      className="rounded-xl bg-white p-5"
      style={{ border: "1px solid hsl(220 18% 91%)", boxShadow: "0 1px 2px 0 rgb(0 0 0 / 0.04)" }}
    >
      <h3 className="flex items-center gap-2 text-[13px] font-semibold text-foreground/80 mb-4">
        <span className="text-og-burgundy/70">{icon}</span>
        {title}
      </h3>
      {children}
    </div>
  );
}

function MetaRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 py-2.5 border-b border-foreground/5 last:border-0">
      <span className="text-[12px] text-foreground/45 shrink-0 mt-px">{label}</span>
      <span className="text-[12px] font-medium text-foreground/80 text-right">{value}</span>
    </div>
  );
}

export default function GrantDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const qc = useQueryClient();

  const { data: grant, isLoading } = useQuery({
    queryKey: ["grant", id],
    queryFn: () => grantsApi.get(id),
    enabled: !!id,
  });

  const { data: watchlist } = useQuery({
    queryKey: ["grants-watchlist"],
    queryFn: () => grantsApi.getWatchlist(),
  });

  const watched = (watchlist ?? []).some((g: any) => g.id === id);

  const addWatch = useMutation({
    mutationFn: () => grantsApi.addToWatchlist(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["grants-watchlist"] }),
  });
  const removeWatch = useMutation({
    mutationFn: () => grantsApi.removeFromWatchlist(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["grants-watchlist"] }),
  });

  const startApp = useMutation({
    mutationFn: () =>
      applicationsApi.create({
        grant_id: id,
        title: (grant as any)?.title ?? "New Application",
      } as any),
    onSuccess: (app) => {
      toast({ title: "Application created", description: "Redirecting to workspace…" });
      router.push(`/applications/${(app as any).id}`);
    },
    onError: () => toast({ variant: "destructive", title: "Failed to create application" }),
  });

  if (isLoading) {
    return (
      <div className="p-7 max-w-[900px] space-y-4">
        <div className="h-8 w-48 rounded-lg bg-foreground/5 animate-pulse" />
        <div className="h-40 rounded-xl bg-foreground/5 animate-pulse" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <div className="lg:col-span-2 space-y-5">
            <div className="h-40 rounded-xl bg-foreground/5 animate-pulse" />
            <div className="h-32 rounded-xl bg-foreground/5 animate-pulse" />
          </div>
          <div className="space-y-5">
            <div className="h-40 rounded-xl bg-foreground/5 animate-pulse" />
            <div className="h-32 rounded-xl bg-foreground/5 animate-pulse" />
          </div>
        </div>
      </div>
    );
  }

  if (!grant) {
    return (
      <div className="p-7">
        <Link href="/grants" className="inline-flex items-center gap-1.5 text-[13px] text-foreground/50 hover:text-foreground/80 transition-colors mb-6">
          <ArrowLeft size={14} /> Back to grants
        </Link>
        <p className="text-sm text-foreground/40">Grant not found.</p>
      </div>
    );
  }

  const g = grant as any;
  const days = g.deadline ? daysUntil(g.deadline) : null;
  const urgent = days !== null && days >= 0 && days <= 14;
  const closed = days !== null && days < 0;

  return (
    <div className="p-7 max-w-[900px] space-y-5">
      {/* Back nav */}
      <Link
        href="/grants"
        className="inline-flex items-center gap-1.5 text-[13px] text-foreground/45 hover:text-foreground/70 transition-colors"
      >
        <ArrowLeft size={13} strokeWidth={2} /> Grant Database
      </Link>

      {/* Hero card */}
      <div
        className="rounded-xl bg-white p-6"
        style={{ border: "1px solid hsl(220 18% 91%)", boxShadow: "0 1px 3px 0 rgb(0 0 0 / 0.05)" }}
      >
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="flex-1 min-w-0">
            {/* Funder badge */}
            <div className="flex items-center gap-2 mb-2">
              {g.funder?.type && (
                <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-muted text-foreground/40">
                  {FUNDER_TYPE_LABELS[g.funder.type] ?? g.funder.type}
                </span>
              )}
              {g.is_verified && (
                <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-600">
                  <BadgeCheck size={11} /> Verified
                </span>
              )}
            </div>
            <h1 className="font-serif text-2xl font-semibold text-foreground leading-snug">{g.title}</h1>
            {g.funder?.name && (
              <p className="mt-1 text-[13px] text-foreground/55">{g.funder.name}</p>
            )}
            {g.tagline && (
              <p className="mt-2 text-[13px] text-foreground/60 italic">{g.tagline}</p>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => (watched ? removeWatch.mutate() : addWatch.mutate())}
              className={cn(
                "flex items-center gap-1.5 h-8 px-3 text-[12px] font-medium rounded-lg transition-all",
                watched
                  ? "bg-[#C9A84C]/10 text-[#B8922A] border border-[#C9A84C]/30 hover:bg-[#C9A84C]/20"
                  : "bg-white text-foreground/50 hover:text-foreground/70 border border-foreground/10 hover:border-foreground/20"
              )}
            >
              <Star size={13} className={watched ? "fill-[#C9A84C] text-[#C9A84C]" : ""} strokeWidth={watched ? 0 : 2} />
              {watched ? "Watching" : "Watch"}
            </button>
            <button
              onClick={() => startApp.mutate()}
              disabled={startApp.isPending}
              className="flex items-center gap-1.5 h-8 px-4 text-[12px] font-semibold rounded-lg bg-og-burgundy text-white hover:bg-og-burgundy/90 transition-all disabled:opacity-60"
            >
              {startApp.isPending ? "Creating…" : "Start Application"}
            </button>
          </div>
        </div>

        {/* Key stats strip */}
        <div className="mt-5 pt-5 border-t border-foreground/5 grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-foreground/35 mb-1">Award Range</p>
            {(g.min_amount != null || g.max_amount != null) ? (
              <p className="text-[14px] font-semibold" style={{ color: "#7B1F3A" }}>
                {g.min_amount != null && g.max_amount != null
                  ? `${formatCurrency(g.min_amount)} – ${formatCurrency(g.max_amount)}`
                  : g.max_amount != null
                  ? `Up to ${formatCurrency(g.max_amount)}`
                  : formatCurrency(g.min_amount)}
              </p>
            ) : (
              <p className="text-[13px] text-foreground/30">Not specified</p>
            )}
          </div>

          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-foreground/35 mb-1">Deadline</p>
            {g.deadline ? (
              <div className="flex items-center gap-1.5">
                <p className={cn("text-[14px] font-semibold", closed ? "text-foreground/30 line-through" : urgent ? "text-red-600" : "text-foreground/80")}>
                  {formatDate(g.deadline)}
                </p>
                {!closed && days !== null && (
                  <span className={cn("text-[11px] font-semibold px-1.5 py-0.5 rounded", urgent ? "bg-red-50 text-red-600" : "bg-foreground/5 text-foreground/40")}>
                    {days === 0 ? "Today" : `${days}d`}
                  </span>
                )}
                {closed && <span className="text-[11px] text-foreground/30">(closed)</span>}
              </div>
            ) : (
              <p className="text-[13px] text-foreground/30">Rolling</p>
            )}
          </div>

          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-foreground/35 mb-1">Grant Type</p>
            <p className="text-[14px] font-semibold text-foreground/80">
              {GRANT_TYPE_LABELS[g.type] ?? g.type?.replace(/_/g, " ")}
            </p>
          </div>

          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-foreground/35 mb-1">Cycle</p>
            <p className="text-[14px] font-semibold text-foreground/80">
              {g.cycle_frequency ? CYCLE_LABELS[g.cycle_frequency] ?? g.cycle_frequency : "—"}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Left column */}
        <div className="lg:col-span-2 space-y-5">

          {g.description && (
            <Section title="About This Grant" icon={<FileText size={14} />}>
              <p className="text-[13px] text-foreground/70 leading-relaxed whitespace-pre-wrap">{g.description}</p>
            </Section>
          )}

          <Section title="How to Apply" icon={<CheckCircle2 size={14} />}>
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2 mb-3">
                <BoolBadge value={g.loi_required} trueLabel="LOI Required" falseLabel="No LOI Required" />
                <BoolBadge value={g.match_required} trueLabel={`Match Required${g.match_percentage ? ` (${g.match_percentage}%)` : ""}`} falseLabel="No Match Required" />
                <BoolBadge value={g.reporting_required} trueLabel="Reporting Required" />
              </div>
              {g.application_url ? (
                <a
                  href={g.application_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-[13px] font-medium text-og-burgundy hover:text-og-burgundy/80 transition-colors"
                >
                  <ExternalLink size={13} /> Open Application Portal
                </a>
              ) : (
                <p className="text-[12px] text-foreground/40">Contact the funder directly to request application materials.</p>
              )}
            </div>
          </Section>

          {g.funder && (
            <Section title="About the Funder" icon={<Building2 size={14} />}>
              <div className="space-y-3">
                {(g.funder as any).description && (
                  <p className="text-[13px] text-foreground/70 leading-relaxed">{(g.funder as any).description}</p>
                )}
                <div>
                  {g.funder.giving_range_min != null && g.funder.giving_range_max != null && (
                    <MetaRow
                      label="Typical giving range"
                      value={`${formatCurrency(g.funder.giving_range_min)} – ${formatCurrency(g.funder.giving_range_max)}`}
                    />
                  )}
                  {g.funder.website && (
                    <MetaRow
                      label="Website"
                      value={
                        <a href={g.funder.website} target="_blank" rel="noopener noreferrer"
                          className="text-og-burgundy hover:text-og-burgundy/80 inline-flex items-center gap-1">
                          {g.funder.website.replace(/^https?:\/\//, "").replace(/\/$/, "")}
                          <ExternalLink size={10} />
                        </a>
                      }
                    />
                  )}
                  {g.funder.primary_contact && (
                    <MetaRow label="Contact" value={g.funder.primary_contact} />
                  )}
                  {g.funder.primary_contact_email && (
                    <MetaRow
                      label="Email"
                      value={
                        <a href={`mailto:${g.funder.primary_contact_email}`} className="text-og-burgundy hover:text-og-burgundy/80">
                          {g.funder.primary_contact_email}
                        </a>
                      }
                    />
                  )}
                </div>
              </div>
            </Section>
          )}
        </div>

        {/* Right column */}
        <div className="space-y-5">

          <Section title="Who Can Apply" icon={<Users size={14} />}>
            <div className="space-y-3">
              {g.eligible_org_types?.length > 0 && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-foreground/35 mb-2">Eligible org types</p>
                  <div className="flex flex-wrap gap-1.5">
                    {g.eligible_org_types.map((t: string) => (
                      <span key={t} className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-muted text-foreground/55 capitalize">
                        {ORG_TYPE_LABELS[t] ?? t.replace(/_/g, " ")}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {(g.budget_size_min != null || g.budget_size_max != null) && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-foreground/35 mb-1">Budget requirement</p>
                  <p className="text-[12px] text-foreground/70">
                    {g.budget_size_min != null && g.budget_size_max != null
                      ? `${formatCurrency(g.budget_size_min)} – ${formatCurrency(g.budget_size_max)}`
                      : g.budget_size_min != null
                      ? `Minimum ${formatCurrency(g.budget_size_min)}`
                      : `Up to ${formatCurrency(g.budget_size_max)}`}
                  </p>
                </div>
              )}
              {g.geographic_restrictions?.length > 0 && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-foreground/35 mb-1.5">Geographic restrictions</p>
                  <div className="flex flex-wrap gap-1.5">
                    {g.geographic_restrictions.map((r: string) => (
                      <span key={r} className="text-[11px] px-2 py-0.5 rounded-full bg-muted text-foreground/55">
                        {r}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {!g.eligible_org_types?.length && g.budget_size_min == null && !g.geographic_restrictions?.length && (
                <p className="text-[12px] text-foreground/35">No specific restrictions listed.</p>
              )}
            </div>
          </Section>

          <Section title="Grant Details" icon={<BarChart3 size={14} />}>
            <div>
              {g.typical_amount != null && (
                <MetaRow label="Typical award" value={formatCurrency(g.typical_amount)} />
              )}
              {g.cycle_frequency && (
                <MetaRow label="Cycle" value={CYCLE_LABELS[g.cycle_frequency] ?? g.cycle_frequency} />
              )}
              {g.source && (
                <MetaRow label="Source" value={<span className="capitalize">{g.source.replace(/_/g, " ")}</span>} />
              )}
              {g.last_verified_at && (
                <MetaRow label="Last verified" value={formatDate(g.last_verified_at)} />
              )}
              <MetaRow
                label="Arts-specific"
                value={<BoolBadge value={!!g.funder?.arts_specific} trueLabel="Yes" falseLabel="No" />}
              />
            </div>
          </Section>

          {g.notes && (
            <Section title="Notes" icon={<AlertCircle size={14} />}>
              <p className="text-[12px] text-foreground/60 leading-relaxed whitespace-pre-wrap">{g.notes}</p>
            </Section>
          )}

          {g.deadline && !closed && (
            <div className={cn("rounded-xl p-4", urgent ? "bg-red-50 border border-red-100" : "bg-foreground/[0.02] border border-foreground/5")}>
              <div className="flex items-center gap-2 mb-1">
                <Clock size={13} className={urgent ? "text-red-500" : "text-foreground/30"} />
                <span className={cn("text-[11px] font-semibold uppercase tracking-wider", urgent ? "text-red-500" : "text-foreground/35")}>
                  Deadline
                </span>
              </div>
              <p className={cn("text-[14px] font-semibold", urgent ? "text-red-700" : "text-foreground/70")}>
                {formatDate(g.deadline)}
              </p>
              <p className={cn("text-[12px] mt-0.5", urgent ? "text-red-500" : "text-foreground/40")}>
                {days === 0 ? "Due today" : `${days} day${days === 1 ? "" : "s"} remaining`}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
