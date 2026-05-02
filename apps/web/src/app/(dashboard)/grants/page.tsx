"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Search, Star, StarOff, SlidersHorizontal, X } from "lucide-react";
import Link from "next/link";
import { grantsApi } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { Grant } from "@orchestragrant/types";

const GRANT_TYPES = ["general_operating", "project", "capital", "endowment", "commission", "residency"];
const FUNDER_TYPES = ["federal_government", "state_government", "local_government", "private_foundation", "corporate", "community_foundation", "individual_donor"];

// Demo grants for display without backend

function daysUntil(date: string | Date): number {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const target = new Date(date);
  target.setHours(0, 0, 0, 0);
  return Math.round((target.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
}

const FUNDER_TYPE_LABELS: Record<string, string> = {
  federal_government: "Federal",
  state_government: "State",
  local_government: "Local Gov.",
  private_foundation: "Foundation",
  corporate: "Corporate",
  community_foundation: "Community Fdn",
  individual_donor: "Individual",
};

export default function GrantsPage() {
  const qc = useQueryClient();
  const [query, setQuery] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [grantType, setGrantType] = useState("");
  const [funderType, setFunderType] = useState("");
  const [artsOnly, setArtsOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [watchedLocal, setWatchedLocal] = useState<Set<string>>(new Set());

  const { data, isLoading } = useQuery({
    queryKey: ["grants", query, grantType, funderType, artsOnly, page],
    queryFn: () =>
      grantsApi.list({
        query: query || undefined,
        type: grantType || undefined,
        funder_type: funderType || undefined,
        arts_specific: artsOnly || undefined,
        is_active: true,
        page,
        page_size: 18,
      }),
    placeholderData: (prev) => prev,
  });

  const { data: watchlist } = useQuery({
    queryKey: ["grants-watchlist"],
    queryFn: () => grantsApi.getWatchlist(),
  });

  const watchedIds = watchlist
    ? new Set((watchlist as Grant[]).map((g) => g.id))
    : watchedLocal;

  const addWatch = useMutation({
    mutationFn: (id: string) => grantsApi.addToWatchlist(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["grants-watchlist"] }),
    onMutate: (id) => setWatchedLocal((s) => new Set([...s, id])),
  });
  const removeWatch = useMutation({
    mutationFn: (id: string) => grantsApi.removeFromWatchlist(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["grants-watchlist"] }),
    onMutate: (id) => setWatchedLocal((s) => { const n = new Set(s); n.delete(id); return n; }),
  });

  const apiGrants: Grant[] = data?.items ?? [];
  const grants: Grant[] = apiGrants;
  const total = data?.total ?? 0;
  const hasMore = data?.has_more ?? false;

  const hasActiveFilters = grantType || funderType || artsOnly;

  return (
    <div className="p-7 space-y-5 max-w-[1400px]">
      {/* Page header */}
      <div className="flex items-end justify-between">
        <div>
          <h2 className="font-serif text-2xl font-semibold text-foreground leading-tight">Grant Database</h2>
          <p className="text-sm text-foreground/45 mt-1">
            {isLoading ? "Searching…" : `${total.toLocaleString()} active grants`}
          </p>
        </div>
      </div>

      {/* Search + filter bar */}
      <div className="flex gap-2.5 items-center">
        <div className="relative flex-1 max-w-xl">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground/30"
            size={14}
            strokeWidth={2}
          />
          <input
            className="w-full h-9 pl-9 pr-4 text-[13px] rounded-lg bg-white outline-none transition-all placeholder:text-foreground/30 focus:ring-2 focus:ring-og-burgundy/20"
            style={{ border: "1px solid hsl(220 18% 88%)", boxShadow: "0 1px 2px 0 rgb(0 0 0 / 0.03)" }}
            placeholder="Search by keyword, funder, or program area…"
            value={query}
            onChange={(e) => { setQuery(e.target.value); setPage(1); }}
          />
        </div>
        <button
          onClick={() => setShowFilters((v) => !v)}
          className={cn(
            "flex items-center gap-1.5 h-9 px-3.5 text-[12px] font-medium rounded-lg transition-all duration-150",
            showFilters || hasActiveFilters
              ? "bg-og-burgundy text-white"
              : "bg-white text-foreground/60 hover:text-foreground/80"
          )}
          style={!(showFilters || hasActiveFilters) ? { border: "1px solid hsl(220 18% 88%)", boxShadow: "0 1px 2px 0 rgb(0 0 0 / 0.03)" } : undefined}
        >
          <SlidersHorizontal size={13} strokeWidth={2} />
          Filters
          {hasActiveFilters && <span className="ml-0.5 h-4 w-4 rounded-full bg-white/20 text-[10px] flex items-center justify-center">!</span>}
        </button>
      </div>

      {/* Filter panel */}
      {showFilters && (
        <div
          className="rounded-xl bg-white p-4 flex flex-wrap gap-4 items-end"
          style={{ border: "1px solid hsl(220 18% 90%)", boxShadow: "0 1px 3px 0 rgb(0 0 0 / 0.05)" }}
        >
          <div className="space-y-1.5 min-w-[160px]">
            <label className="text-[11px] font-semibold uppercase tracking-wider text-foreground/40">Grant Type</label>
            <select
              className="flex h-8 w-full rounded-lg border border-input bg-background px-3 text-[12px] focus:outline-none focus:ring-1 focus:ring-og-burgundy/30"
              value={grantType}
              onChange={(e) => { setGrantType(e.target.value); setPage(1); }}
            >
              <option value="">All types</option>
              {GRANT_TYPES.map((t) => (
                <option key={t} value={t}>{t.replace(/_/g, " ")}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1.5 min-w-[180px]">
            <label className="text-[11px] font-semibold uppercase tracking-wider text-foreground/40">Funder Type</label>
            <select
              className="flex h-8 w-full rounded-lg border border-input bg-background px-3 text-[12px] focus:outline-none focus:ring-1 focus:ring-og-burgundy/30"
              value={funderType}
              onChange={(e) => { setFunderType(e.target.value); setPage(1); }}
            >
              <option value="">All funders</option>
              {FUNDER_TYPES.map((t) => (
                <option key={t} value={t}>{t.replace(/_/g, " ")}</option>
              ))}
            </select>
          </div>
          <label className="flex items-center gap-2 text-[12px] cursor-pointer text-foreground/70 hover:text-foreground transition-colors">
            <input
              type="checkbox"
              checked={artsOnly}
              onChange={(e) => { setArtsOnly(e.target.checked); setPage(1); }}
              className="h-3.5 w-3.5 rounded accent-og-burgundy"
            />
            Arts-specific only
          </label>
          {hasActiveFilters && (
            <button
              onClick={() => { setGrantType(""); setFunderType(""); setArtsOnly(false); setPage(1); }}
              className="flex items-center gap-1 text-[11px] font-medium text-foreground/40 hover:text-foreground/70 transition-colors ml-auto"
            >
              <X size={11} /> Clear filters
            </button>
          )}
        </div>
      )}

      {/* Grant grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 9 }).map((_, i) => (
            <div key={i} className="h-44 rounded-xl bg-white animate-pulse" style={{ border: "1px solid hsl(220 18% 91%)" }} />
          ))}
        </div>
      ) : grants.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <Search size={32} className="text-foreground/15 mb-3" />
          <p className="text-sm font-medium text-foreground/40">No grants found</p>
          <p className="text-xs text-foreground/30 mt-1">Try adjusting your search or filters</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-2 xl:grid-cols-3">
          {grants.map((grant) => (
            <GrantCard
              key={grant.id}
              grant={grant}
              watched={watchedIds.has(grant.id)}
              onToggleWatch={() =>
                watchedIds.has(grant.id)
                  ? removeWatch.mutate(grant.id)
                  : addWatch.mutate(grant.id)
              }
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {(page > 1 || hasMore) && (
        <div className="flex items-center justify-center gap-3 pt-2">
          <button
            className="h-8 px-4 text-[12px] font-medium rounded-lg border border-border bg-white hover:bg-muted/50 disabled:opacity-40 transition-all"
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
          >
            Previous
          </button>
          <span className="text-[12px] text-foreground/40">Page {page}</span>
          <button
            className="h-8 px-4 text-[12px] font-medium rounded-lg border border-border bg-white hover:bg-muted/50 disabled:opacity-40 transition-all"
            disabled={!hasMore}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

function GrantCard({
  grant,
  watched,
  onToggleWatch,
}: {
  grant: Grant;
  watched: boolean;
  onToggleWatch: () => void;
}) {
  const days = grant.deadline ? daysUntil(grant.deadline) : null;
  const urgent = days !== null && days >= 0 && days <= 7;

  return (
    <div
      className="group relative flex flex-col gap-3 rounded-xl bg-white p-4 transition-all duration-150 hover:shadow-md hover:-translate-y-px cursor-default"
      style={{ border: "1px solid hsl(220 18% 91%)", boxShadow: "0 1px 2px 0 rgb(0 0 0 / 0.04)" }}
    >
      {/* Top row: title + watchlist */}
      <div className="flex items-start gap-2">
        <Link
          href={`/grants/${grant.id}`}
          className="flex-1 text-[13px] font-semibold text-foreground/90 leading-snug hover:text-og-burgundy transition-colors line-clamp-2"
        >
          {grant.title}
        </Link>
        <button
          onClick={onToggleWatch}
          className="shrink-0 mt-0.5 transition-all duration-150 hover:scale-110"
          aria-label={watched ? "Remove from watchlist" : "Add to watchlist"}
        >
          {watched ? (
            <Star size={14} className="fill-[#C9A84C] text-[#C9A84C]" />
          ) : (
            <Star size={14} className="text-foreground/20 group-hover:text-foreground/40 transition-colors" />
          )}
        </button>
      </div>

      {/* Funder */}
      <div className="flex items-center gap-1.5">
        {grant.funder?.type && (
          <span className="shrink-0 text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-muted text-foreground/40">
            {FUNDER_TYPE_LABELS[grant.funder.type] ?? grant.funder.type}
          </span>
        )}
        <p className="text-[12px] text-foreground/50 truncate">{grant.funder?.name ?? "Unknown Funder"}</p>
      </div>

      {/* Amount row */}
      <div className="flex items-center justify-between gap-2">
        {(grant.min_amount != null || grant.max_amount != null) ? (
          <span className="text-[13px] font-semibold" style={{ color: "#7B1F3A" }}>
            {grant.min_amount != null && grant.max_amount != null
              ? `${formatCurrency(grant.min_amount)} – ${formatCurrency(grant.max_amount)}`
              : grant.max_amount != null
              ? `Up to ${formatCurrency(grant.max_amount)}`
              : formatCurrency(grant.min_amount!)}
          </span>
        ) : (
          <span className="text-[12px] text-foreground/30">Amount TBD</span>
        )}

        {days !== null && (
          <span
            className={cn(
              "text-[11px] font-semibold tabular-nums px-2 py-0.5 rounded-md shrink-0",
              urgent ? "bg-red-50 text-red-600" : "bg-foreground/5 text-foreground/40"
            )}
          >
            {days < 0 ? "Closed" : days === 0 ? "Today" : `${days}d left`}
          </span>
        )}
      </div>

      {/* Tags */}
      <div className="flex flex-wrap gap-1 mt-auto">
        {grant.type && (
          <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-muted text-foreground/50 capitalize">
            {grant.type.replace(/_/g, " ")}
          </span>
        )}
        {grant.arts_specific && (
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full text-[#B8922A]" style={{ background: "rgba(201,168,76,0.12)" }}>
            Arts-specific
          </span>
        )}
      </div>
    </div>
  );
}

