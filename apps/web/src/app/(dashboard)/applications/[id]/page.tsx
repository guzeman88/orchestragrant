"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import {
  ArrowLeft, ChevronDown, Loader2, Sparkles, Save, X,
  Calendar, DollarSign, Flag, FileText, Edit2,
  ChevronRight, Download, ExternalLink,
} from "lucide-react";
import Link from "next/link";
import { applicationsApi, documentsApi } from "@/lib/api";
import { formatDate, formatCurrency } from "@/lib/utils";
import { cn } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";
import type { ApplicationSection } from "@orchestragrant/types";

// ─── Stage config ─────────────────────────────────────────────────────────────

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
  withdrawn:        "Withdrawn",
};

// Matches the backend STAGE_TRANSITIONS
const STAGE_TRANSITIONS: Record<string, string[]> = {
  prospecting:      ["qualifying", "withdrawn"],
  qualifying:       ["writing", "prospecting", "withdrawn"],
  writing:          ["internal_review", "qualifying", "withdrawn"],
  internal_review:  ["director_review", "writing", "withdrawn"],
  director_review:  ["board_approval", "internal_review", "writing", "withdrawn"],
  board_approval:   ["ready_to_submit", "director_review", "withdrawn"],
  ready_to_submit:  ["submitted", "board_approval", "withdrawn"],
  submitted:        ["under_review", "withdrawn"],
  under_review:     ["awarded", "declined"],
  awarded:          [],
  declined:         [],
  withdrawn:        [],
};

const STAGE_COLORS: Record<string, { dot: string; badge: string }> = {
  prospecting:      { dot: "bg-slate-400",   badge: "bg-slate-100 text-slate-600" },
  qualifying:       { dot: "bg-sky-400",     badge: "bg-sky-100 text-sky-700" },
  writing:          { dot: "bg-blue-400",    badge: "bg-blue-100 text-blue-700" },
  internal_review:  { dot: "bg-violet-400",  badge: "bg-violet-100 text-violet-700" },
  director_review:  { dot: "bg-purple-400",  badge: "bg-purple-100 text-purple-700" },
  board_approval:   { dot: "bg-fuchsia-400", badge: "bg-fuchsia-100 text-fuchsia-700" },
  ready_to_submit:  { dot: "bg-teal-400",    badge: "bg-teal-100 text-teal-700" },
  submitted:        { dot: "bg-amber-400",   badge: "bg-amber-100 text-amber-700" },
  under_review:     { dot: "bg-orange-400",  badge: "bg-orange-100 text-orange-700" },
  awarded:          { dot: "bg-emerald-500", badge: "bg-emerald-100 text-emerald-700" },
  declined:         { dot: "bg-red-400",     badge: "bg-red-100 text-red-600" },
  withdrawn:        { dot: "bg-gray-300",    badge: "bg-gray-100 text-gray-500" },
};

const PRIORITY_LABELS: Record<string, { label: string; className: string }> = {
  low:      { label: "Low",      className: "text-foreground/40 bg-foreground/5" },
  medium:   { label: "Medium",   className: "text-amber-700 bg-amber-50" },
  high:     { label: "High",     className: "text-orange-700 bg-orange-50" },
  critical: { label: "Critical", className: "text-red-700 bg-red-50" },
};

const SECTION_STATUS_COLORS: Record<string, string> = {
  not_started: "text-foreground/30",
  in_progress: "text-blue-600",
  complete:    "text-emerald-600",
  approved:    "text-violet-600",
};

const SECTION_STATUS_LABELS: Record<string, string> = {
  not_started: "Not started",
  in_progress: "In progress",
  complete:    "Complete",
  approved:    "Approved",
};

const VISIBLE_STAGES = [
  "prospecting", "qualifying", "writing", "internal_review",
  "director_review", "board_approval", "ready_to_submit",
  "submitted", "under_review",
];

// ─── Sub-components ────────────────────────────────────────────────────────────

function StageProgressBar({ currentStage }: { currentStage: string }) {
  const isTerminal = ["awarded", "declined", "withdrawn"].includes(currentStage);
  const currentIdx = VISIBLE_STAGES.indexOf(currentStage);

  if (isTerminal) {
    const color = currentStage === "awarded"
      ? "bg-emerald-100 text-emerald-700"
      : currentStage === "declined"
      ? "bg-red-100 text-red-600"
      : "bg-gray-100 text-gray-500";
    return (
      <span className={cn("text-[11px] font-semibold px-2.5 py-1 rounded-full", color)}>
        {STAGE_LABELS[currentStage]}
      </span>
    );
  }

  return (
    <div className="flex items-center gap-0.5 flex-wrap">
      {VISIBLE_STAGES.map((stage, i) => {
        const done = i < currentIdx;
        const active = i === currentIdx;
        return (
          <div key={stage} className="flex items-center gap-0.5">
            <div className={cn(
              "h-1.5 w-1.5 rounded-full shrink-0 transition-colors",
              done ? "bg-og-burgundy" : active ? "bg-og-burgundy" : "bg-foreground/12"
            )} />
            {active && (
              <span className="text-[11px] font-semibold text-og-burgundy mx-1">{STAGE_LABELS[stage]}</span>
            )}
            {i < VISIBLE_STAGES.length - 1 && (
              <div className={cn("h-px w-2.5", done ? "bg-og-burgundy/35" : "bg-foreground/8")} />
            )}
          </div>
        );
      })}
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

// ─── Main page ─────────────────────────────────────────────────────────────────

export default function ApplicationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const [stageOpen, setStageOpen] = useState(false);
  const [editingSection, setEditingSection] = useState<string | null>(null);
  const [draft, setDraft] = useState("");

  const { data: app, isLoading } = useQuery({
    queryKey: ["application", id],
    queryFn: () => applicationsApi.get(id),
    enabled: !!id,
  });

  const { data: sections } = useQuery({
    queryKey: ["application-sections", id],
    queryFn: () => applicationsApi.getSections(id),
    enabled: !!id,
  });

  const transition = useMutation({
    mutationFn: (stage: string) => applicationsApi.transition(id, stage),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["application", id] });
      qc.invalidateQueries({ queryKey: ["applications"] });
      setStageOpen(false);
      toast({ title: "Stage updated" });
    },
    onError: () => toast({ variant: "destructive", title: "Transition not allowed" }),
  });

  const saveSection = useMutation({
    mutationFn: ({ sectionId, content }: { sectionId: string; content: string }) =>
      applicationsApi.updateSection(id, sectionId, { content }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["application-sections", id] });
      setEditingSection(null);
      toast({ title: "Section saved" });
    },
    onError: () => toast({ variant: "destructive", title: "Failed to save" }),
  });

  const generateSection = useMutation({
    mutationFn: (sectionId: string) => applicationsApi.generateSection(id, sectionId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["application-sections", id] });
      toast({ title: "Draft generated", description: "Review and edit the content below." });
    },
    onError: () => toast({ variant: "destructive", title: "Generation failed" }),
  });

  const { data: documents } = useQuery({
    queryKey: ["documents"],
    queryFn: () => documentsApi.list(),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="p-7 max-w-[960px] space-y-5">
        <div className="h-7 w-40 rounded-lg bg-foreground/5 animate-pulse" />
        <div className="h-36 rounded-xl bg-foreground/5 animate-pulse" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <div className="lg:col-span-2 space-y-4">
            <div className="h-40 rounded-xl bg-foreground/5 animate-pulse" />
            <div className="h-40 rounded-xl bg-foreground/5 animate-pulse" />
          </div>
          <div className="h-64 rounded-xl bg-foreground/5 animate-pulse" />
        </div>
      </div>
    );
  }

  if (!app) {
    return (
      <div className="p-7">
        <Link href="/applications" className="inline-flex items-center gap-1.5 text-[13px] text-foreground/50 hover:text-foreground/80 transition-colors mb-6">
          <ArrowLeft size={14} /> Back to applications
        </Link>
        <p className="text-sm text-foreground/40">Application not found.</p>
      </div>
    );
  }

  const a = app as any;
  const allowedTransitions = STAGE_TRANSITIONS[a.stage] ?? [];
  const stageColor = STAGE_COLORS[a.stage] ?? STAGE_COLORS.prospecting;
  const priorityStyle = PRIORITY_LABELS[a.priority ?? "medium"];

  return (
    <div className="p-7 max-w-[960px] space-y-5">
      {/* Back nav */}
      <Link
        href="/applications"
        className="inline-flex items-center gap-1.5 text-[13px] text-foreground/45 hover:text-foreground/70 transition-colors"
      >
        <ArrowLeft size={13} strokeWidth={2} /> Applications
      </Link>

      {/* Hero card */}
      <div
        className="rounded-xl bg-white p-6"
        style={{ border: "1px solid hsl(220 18% 91%)", boxShadow: "0 1px 3px 0 rgb(0 0 0 / 0.05)" }}
      >
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="flex-1 min-w-0">
            <div className="mb-2">
              <StageProgressBar currentStage={a.stage} />
            </div>
            <h1 className="text-xl font-serif font-semibold text-foreground leading-tight mt-1">{a.title}</h1>
            {a.grant?.funder?.name && (
              <p className="text-[13px] text-foreground/50 mt-1">{a.grant.funder.name}</p>
            )}
          </div>

          {/* Stage transition button */}
          <div className="relative shrink-0">
            <button
              onClick={() => setStageOpen((v) => !v)}
              disabled={allowedTransitions.length === 0}
              className={cn(
                "inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-[12px] font-semibold transition-all duration-150",
                "border border-foreground/10 bg-white hover:bg-foreground/[0.03]",
                allowedTransitions.length === 0 && "opacity-50 cursor-not-allowed"
              )}
            >
              <span className={cn("h-1.5 w-1.5 rounded-full", stageColor.dot)} />
              {STAGE_LABELS[a.stage]}
              {allowedTransitions.length > 0 && <ChevronDown size={12} />}
            </button>
            {stageOpen && allowedTransitions.length > 0 && (
              <div
                className="absolute right-0 top-full mt-1 z-50 rounded-xl bg-white overflow-hidden"
                style={{ border: "1px solid hsl(220 18% 88%)", boxShadow: "0 8px 24px -4px rgb(0 0 0 / 0.12)", minWidth: "180px" }}
              >
                <div className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-foreground/35 border-b border-foreground/5">
                  Move to
                </div>
                {allowedTransitions.map((s) => (
                  <button
                    key={s}
                    onClick={() => transition.mutate(s)}
                    disabled={transition.isPending}
                    className="flex w-full items-center gap-2.5 px-3 py-2.5 text-[12px] font-medium hover:bg-foreground/[0.03] transition-colors"
                  >
                    {transition.isPending
                      ? <Loader2 className="h-3 w-3 animate-spin text-foreground/30" />
                      : <span className={cn("h-1.5 w-1.5 rounded-full shrink-0", STAGE_COLORS[s]?.dot ?? "bg-foreground/20")} />
                    }
                    {STAGE_LABELS[s]}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 4-stat strip */}
        <div
          className="mt-5 pt-5 grid grid-cols-2 sm:grid-cols-4 gap-4"
          style={{ borderTop: "1px solid hsl(220 18% 93%)" }}
        >
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-foreground/30 flex items-center gap-1">
              <DollarSign size={9} /> Requested
            </p>
            <p className="text-[14px] font-bold text-foreground/90 mt-1">
              {a.requested_amount ? formatCurrency(a.requested_amount) : "—"}
            </p>
          </div>
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-foreground/30 flex items-center gap-1">
              <Calendar size={9} /> Deadline
            </p>
            <p className="text-[14px] font-bold text-foreground/90 mt-1">
              {a.submission_deadline ? formatDate(a.submission_deadline) : "—"}
            </p>
          </div>
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-foreground/30 flex items-center gap-1">
              <Flag size={9} /> Priority
            </p>
            <p className="mt-1">
              <span className={cn("text-[11px] font-semibold px-2 py-0.5 rounded-full", priorityStyle?.className)}>
                {priorityStyle?.label ?? "—"}
              </span>
            </p>
          </div>
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-foreground/30 flex items-center gap-1">
              <FileText size={9} /> Sections
            </p>
            <p className="text-[14px] font-bold text-foreground/90 mt-1">
              {sections?.length ?? 0}
            </p>
          </div>
        </div>
      </div>

      {/* Body — 2-col grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Left: sections */}
        <div className="lg:col-span-2 space-y-4">
          {/* Project info */}
          {(a.project_title || a.project_description) && (
            <div
              className="rounded-xl bg-white p-5"
              style={{ border: "1px solid hsl(220 18% 91%)", boxShadow: "0 1px 2px 0 rgb(0 0 0 / 0.04)" }}
            >
              <h3 className="text-[13px] font-semibold text-foreground/80 mb-3">Project</h3>
              {a.project_title && <p className="text-[13px] font-medium text-foreground/90 mb-1">{a.project_title}</p>}
              {a.project_description && <p className="text-[13px] text-foreground/60 leading-relaxed">{a.project_description}</p>}
            </div>
          )}

          {/* Application sections */}
          <div
            className="rounded-xl bg-white overflow-hidden"
            style={{ border: "1px solid hsl(220 18% 91%)", boxShadow: "0 1px 2px 0 rgb(0 0 0 / 0.04)" }}
          >
            <div
              className="flex items-center justify-between px-5 py-4"
              style={{ borderBottom: "1px solid hsl(220 18% 93%)" }}
            >
              <h3 className="text-[13px] font-semibold text-foreground/80">Application Sections</h3>
              <span className="text-[11px] text-foreground/35">{sections?.length ?? 0} sections</span>
            </div>

            {!sections || sections.length === 0 ? (
              <div className="py-10 text-center">
                <FileText size={28} className="mx-auto text-foreground/10 mb-3" />
                <p className="text-[13px] text-foreground/40">No sections yet</p>
                <p className="text-[11px] text-foreground/25 mt-0.5">Move this application forward to add writing sections</p>
              </div>
            ) : (
              <div className="divide-y divide-foreground/5">
                {sections.map((sec: ApplicationSection) => (
                  <SectionCard
                    key={sec.id}
                    section={sec}
                    isEditing={editingSection === sec.id}
                    draft={editingSection === sec.id ? draft : sec.content ?? ""}
                    isGenerating={generateSection.isPending && generateSection.variables === sec.id}
                    onEdit={() => { setEditingSection(sec.id); setDraft(sec.content ?? ""); }}
                    onCancel={() => setEditingSection(null)}
                    onDraftChange={setDraft}
                    onSave={() => saveSection.mutate({ sectionId: sec.id, content: draft })}
                    isSaving={saveSection.isPending && (saveSection.variables as any)?.sectionId === sec.id}
                    onGenerate={() => generateSection.mutate(sec.id)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right: details */}
        <div className="space-y-4">
          <div
            className="rounded-xl bg-white p-5"
            style={{ border: "1px solid hsl(220 18% 91%)", boxShadow: "0 1px 2px 0 rgb(0 0 0 / 0.04)" }}
          >
            <h3 className="text-[13px] font-semibold text-foreground/80 mb-3">Details</h3>
            {a.grant?.funder?.name && <MetaRow label="Funder" value={a.grant.funder.name} />}
            {a.grant?.title && (
              <MetaRow label="Grant" value={
                <Link href={`/grants/${a.grant_id}`} className="text-og-burgundy hover:underline flex items-center gap-1">
                  {a.grant.title.length > 28 ? a.grant.title.slice(0, 28) + "…" : a.grant.title}
                  <ChevronRight size={10} />
                </Link>
              } />
            )}
            <MetaRow label="Stage" value={
              <span className={cn("text-[11px] font-semibold px-2 py-0.5 rounded-full", stageColor.badge)}>
                {STAGE_LABELS[a.stage]}
              </span>
            } />
            {a.requested_amount && <MetaRow label="Requested" value={formatCurrency(a.requested_amount)} />}
            {a.awarded_amount && (
              <MetaRow label="Awarded" value={
                <span className="text-emerald-700 font-bold">{formatCurrency(a.awarded_amount)}</span>
              } />
            )}
            {a.submission_deadline && <MetaRow label="Deadline" value={formatDate(a.submission_deadline)} />}
            {a.submitted_at && <MetaRow label="Submitted" value={formatDate(a.submitted_at)} />}
            {a.assigned_user && (
              <MetaRow label="Assigned" value={`${a.assigned_user.first_name} ${a.assigned_user.last_name}`} />
            )}
            <MetaRow label="Updated" value={formatDate(a.updated_at)} />
          </div>

          {/* Stage history */}
          {a.stage_history?.length > 0 && (
            <div
              className="rounded-xl bg-white p-5"
              style={{ border: "1px solid hsl(220 18% 91%)", boxShadow: "0 1px 2px 0 rgb(0 0 0 / 0.04)" }}
            >
              <h3 className="text-[13px] font-semibold text-foreground/80 mb-3">History</h3>
              <div className="space-y-2.5">
                {[...a.stage_history].reverse().slice(0, 5).map((entry: any, i: number) => (
                  <div key={i} className="flex items-start gap-2">
                    <div className={cn("h-1.5 w-1.5 rounded-full mt-1.5 shrink-0", STAGE_COLORS[entry.to_stage]?.dot ?? "bg-foreground/20")} />
                    <div className="min-w-0">
                      <p className="text-[11px] font-medium text-foreground/70">
                        {STAGE_LABELS[entry.from_stage] ?? entry.from_stage} → {STAGE_LABELS[entry.to_stage] ?? entry.to_stage}
                      </p>
                      <p className="text-[10px] text-foreground/30 mt-0.5">
                        {new Date(entry.changed_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                      </p>
                      {entry.note && <p className="text-[11px] text-foreground/50 mt-0.5 italic">{entry.note}</p>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {a.internal_notes && (
            <div
              className="rounded-xl bg-white p-5"
              style={{ border: "1px solid hsl(220 18% 91%)", boxShadow: "0 1px 2px 0 rgb(0 0 0 / 0.04)" }}
            >
              <h3 className="text-[13px] font-semibold text-foreground/80 mb-2">Notes</h3>
              <p className="text-[12px] text-foreground/60 leading-relaxed whitespace-pre-wrap">{a.internal_notes}</p>
            </div>
          )}
        </div>
      </div>

      {/* Documents panel */}
      <div
        className="rounded-xl bg-white overflow-hidden"
        style={{ border: "1px solid hsl(220 18% 91%)", boxShadow: "0 1px 2px 0 rgb(0 0 0 / 0.04)" }}
      >
        <div
          className="flex items-center justify-between px-5 py-4"
          style={{ borderBottom: "1px solid hsl(220 18% 93%)" }}
        >
          <h3 className="text-[13px] font-semibold text-foreground/80">Organization Documents</h3>
          <Link href="/documents" className="text-[11px] text-og-burgundy hover:underline flex items-center gap-1">
            Manage <ExternalLink size={10} />
          </Link>
        </div>
        {!documents || documents.length === 0 ? (
          <div className="py-8 text-center">
            <Download size={24} className="mx-auto text-foreground/10 mb-2" />
            <p className="text-[13px] text-foreground/40">No documents uploaded yet</p>
            <Link href="/documents" className="text-[11px] text-og-burgundy hover:underline mt-1 block">
              Upload documents →
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-foreground/5">
            {(documents as any[]).map((doc) => (
              <DocumentRow key={doc.id} doc={doc} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Section card ──────────────────────────────────────────────────────────────

function SectionCard({
  section, isEditing, draft, onEdit, onCancel, onDraftChange,
  onSave, isSaving, isGenerating, onGenerate,
}: {
  section: ApplicationSection;
  isEditing: boolean;
  draft: string;
  onEdit: () => void;
  onCancel: () => void;
  onDraftChange: (v: string) => void;
  onSave: () => void;
  isSaving: boolean;
  isGenerating: boolean;
  onGenerate: () => void;
}) {
  const wordCount = draft.trim().split(/\s+/).filter(Boolean).length;
  const limit = section.word_limit;
  const overLimit = !!limit && wordCount > limit;

  return (
    <div className="px-5 py-4">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-[13px] font-semibold text-foreground/85">{section.title}</span>
            {section.is_required && <span className="text-[10px] text-og-burgundy/60 font-semibold">Required</span>}
          </div>
          <div className="flex items-center gap-2 mt-0.5">
            <span className={cn("text-[10px] font-medium", SECTION_STATUS_COLORS[section.status])}>
              {SECTION_STATUS_LABELS[section.status]}
            </span>
            {limit && (
              <span className={cn("text-[10px]", overLimit ? "text-red-500 font-semibold" : "text-foreground/30")}>
                {isEditing ? `${wordCount} / ${limit} words` : `${limit}w limit`}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          {isEditing ? (
            <>
              <button
                onClick={onCancel}
                className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium text-foreground/50 hover:text-foreground/80 rounded-lg border border-foreground/10 bg-white transition-colors"
              >
                <X size={10} /> Cancel
              </button>
              <button
                onClick={onSave}
                disabled={isSaving}
                className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-semibold text-white rounded-lg transition-all"
                style={{ background: "linear-gradient(135deg, #7B1F3A 0%, #9B2D4E 100%)" }}
              >
                {isSaving ? <Loader2 size={10} className="animate-spin" /> : <Save size={10} />}
                Save
              </button>
            </>
          ) : (
            <>
              <button
                onClick={onGenerate}
                disabled={isGenerating}
                title="Generate draft"
                className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium text-amber-700 bg-amber-50 hover:bg-amber-100 rounded-lg border border-amber-100 transition-colors disabled:opacity-40"
              >
                {isGenerating ? <Loader2 size={10} className="animate-spin" /> : <Sparkles size={10} />}
                Draft
              </button>
              <button
                onClick={onEdit}
                className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium text-foreground/50 hover:text-foreground/80 rounded-lg border border-foreground/10 bg-white transition-colors"
              >
                <Edit2 size={10} /> Edit
              </button>
            </>
          )}
        </div>
      </div>

      {section.prompt && (
        <p className="text-[11px] text-foreground/40 italic mb-2.5 leading-relaxed">"{section.prompt}"</p>
      )}

      {isEditing ? (
        <textarea
          className="w-full rounded-lg border border-input bg-background px-3 py-2.5 text-[13px] resize-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-og-burgundy/20 transition-all"
          style={{ minHeight: "140px" }}
          value={draft}
          onChange={(e) => onDraftChange(e.target.value)}
          autoFocus
        />
      ) : (
        <div className="text-[13px] text-foreground/70 leading-relaxed whitespace-pre-wrap">
          {section.content || (
            <span className="text-foreground/25 italic">No content yet — click Edit or Draft to begin.</span>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Document row ──────────────────────────────────────────────────────────────

function DocumentRow({ doc }: { doc: any }) {
  const { mutate: getUrl, isPending } = useMutation({
    mutationFn: () => documentsApi.getDownloadUrl(doc.id),
    onSuccess: (data: any) => {
      window.open(data.download_url, "_blank", "noopener noreferrer");
    },
    onError: () => toast({ variant: "destructive", title: "Could not get download link" }),
  });

  const ext = doc.file_name?.split(".").pop()?.toLowerCase() ?? "";
  const extColors: Record<string, string> = {
    pdf: "bg-red-50 text-red-600",
    doc: "bg-blue-50 text-blue-600",
    docx: "bg-blue-50 text-blue-600",
    xls: "bg-green-50 text-green-600",
    xlsx: "bg-green-50 text-green-600",
  };

  return (
    <div className="flex items-center justify-between gap-3 px-5 py-3 hover:bg-foreground/[0.02] transition-colors">
      <div className="flex items-center gap-3 min-w-0">
        <span className={cn("text-[10px] font-bold uppercase px-1.5 py-0.5 rounded shrink-0", extColors[ext] ?? "bg-foreground/5 text-foreground/40")}>
          {ext || "—"}
        </span>
        <div className="min-w-0">
          <p className="text-[13px] font-medium text-foreground/80 truncate">{doc.file_name || doc.title || "Document"}</p>
          {doc.category && (
            <p className="text-[11px] text-foreground/35 capitalize">{doc.category.replace(/_/g, " ")}</p>
          )}
        </div>
      </div>
      <button
        onClick={() => getUrl()}
        disabled={isPending}
        className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium text-foreground/50 hover:text-foreground/80 rounded-lg border border-foreground/10 bg-white transition-colors shrink-0 disabled:opacity-40"
      >
        {isPending ? <Loader2 size={10} className="animate-spin" /> : <Download size={10} />}
        Download
      </button>
    </div>
  );
}
