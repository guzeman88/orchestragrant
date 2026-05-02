"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, Trash2, Plus, X, Calendar, Clock, AlertTriangle } from "lucide-react";
import { deadlinesApi } from "@/lib/api";
import { cn } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";

// Raw snake_case shape returned by the API
interface DeadlineRow {
  id: string;
  title: string;
  deadline_at: string;
  type?: string;
  notes?: string;
  is_completed: boolean;
  completed_at?: string;
  created_at: string;
}

const DEADLINE_TYPE_LABELS: Record<string, string> = {
  application:    "Application",
  loi:            "LOI",
  report:         "Report",
  award_decision: "Award Decision",
  meeting:        "Meeting",
  other:          "Other",
};

const DEADLINE_TYPES = ["application", "loi", "report", "award_decision", "meeting", "other"];

function getUrgency(deadline_at: string, is_completed: boolean) {
  if (is_completed) return "done";
  const days = Math.ceil((new Date(deadline_at).getTime() - Date.now()) / 86_400_000);
  if (days < 0) return "overdue";
  if (days <= 7) return "urgent";
  if (days <= 14) return "soon";
  return "normal";
}

function DeadlineBadge({ deadline_at, is_completed }: { deadline_at: string; is_completed: boolean }) {
  const urgency = getUrgency(deadline_at, is_completed);
  const days = Math.ceil((new Date(deadline_at).getTime() - Date.now()) / 86_400_000);

  const styles = {
    done:    "bg-emerald-50 text-emerald-700",
    overdue: "bg-red-50 text-red-700",
    urgent:  "bg-orange-50 text-orange-700",
    soon:    "bg-amber-50 text-amber-700",
    normal:  "bg-foreground/5 text-foreground/50",
  };

  const label = is_completed
    ? "Done"
    : days < 0
    ? `${Math.abs(days)}d overdue`
    : days === 0
    ? "Due today"
    : `${days}d left`;

  return (
    <span className={cn("text-[11px] font-semibold px-2 py-0.5 rounded-full inline-flex items-center gap-1", styles[urgency])}>
      {urgency === "overdue" && <AlertTriangle size={9} />}
      {label}
    </span>
  );
}

function NewDeadlineForm({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const [title, setTitle] = useState("");
  const [deadline_at, setDeadlineAt] = useState("");
  const [type, setType] = useState("application");
  const [notes, setNotes] = useState("");

  const create = useMutation({
    mutationFn: () =>
      deadlinesApi.create({ title, deadline_at: new Date(deadline_at).toISOString(), type, notes: notes || undefined }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["deadlines"] });
      toast({ title: "Deadline created" });
      onClose();
    },
    onError: () => toast({ variant: "destructive", title: "Failed to create deadline" }),
  });

  return (
    <div
      className="rounded-xl bg-white p-5 mb-5"
      style={{ border: "1px solid hsl(220 18% 88%)", boxShadow: "0 4px 16px -4px rgb(0 0 0 / 0.08)" }}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-[13px] font-semibold text-foreground/80">New Deadline</h3>
        <button onClick={onClose} className="text-foreground/30 hover:text-foreground/60 transition-colors">
          <X size={15} />
        </button>
      </div>

      <div className="space-y-3">
        <div>
          <label className="text-[11px] font-semibold text-foreground/45 uppercase tracking-wider block mb-1">Title</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Submit full proposal to NEA"
            className="w-full rounded-lg border border-input bg-background px-3 py-2 text-[13px] focus:outline-none focus:ring-2 focus:ring-og-burgundy/20 transition-all"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-[11px] font-semibold text-foreground/45 uppercase tracking-wider block mb-1">Date</label>
            <input
              type="date"
              value={deadline_at}
              onChange={(e) => setDeadlineAt(e.target.value)}
              className="w-full rounded-lg border border-input bg-background px-3 py-2 text-[13px] focus:outline-none focus:ring-2 focus:ring-og-burgundy/20 transition-all"
            />
          </div>
          <div>
            <label className="text-[11px] font-semibold text-foreground/45 uppercase tracking-wider block mb-1">Type</label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="w-full rounded-lg border border-input bg-background px-3 py-2 text-[13px] focus:outline-none focus:ring-2 focus:ring-og-burgundy/20 transition-all"
            >
              {DEADLINE_TYPES.map((t) => (
                <option key={t} value={t}>{DEADLINE_TYPE_LABELS[t]}</option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="text-[11px] font-semibold text-foreground/45 uppercase tracking-wider block mb-1">Notes (optional)</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Any additional context..."
            className="w-full rounded-lg border border-input bg-background px-3 py-2 text-[13px] resize-none focus:outline-none focus:ring-2 focus:ring-og-burgundy/20 transition-all"
            style={{ minHeight: "72px" }}
          />
        </div>

        <div className="flex justify-end gap-2 pt-1">
          <button
            onClick={onClose}
            className="px-3.5 py-1.5 text-[12px] font-medium text-foreground/50 hover:text-foreground/80 rounded-lg border border-foreground/10 bg-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={() => create.mutate()}
            disabled={!title.trim() || !deadline_at || create.isPending}
            className="px-3.5 py-1.5 text-[12px] font-semibold text-white rounded-lg transition-all disabled:opacity-40"
            style={{ background: "linear-gradient(135deg, #7B1F3A 0%, #9B2D4E 100%)" }}
          >
            {create.isPending ? "Saving…" : "Create"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function DeadlinesPage() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [filter, setFilter] = useState<"all" | "upcoming" | "completed">("upcoming");

  const { data: deadlines, isLoading } = useQuery<DeadlineRow[]>({
    queryKey: ["deadlines", filter],
    queryFn: () => deadlinesApi.list(filter === "upcoming") as unknown as Promise<DeadlineRow[]>,
  });

  const complete = useMutation({
    mutationFn: (id: string) => deadlinesApi.complete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["deadlines"] });
      toast({ title: "Marked complete" });
    },
    onError: () => toast({ variant: "destructive", title: "Failed to complete" }),
  });

  const remove = useMutation({
    mutationFn: (id: string) => deadlinesApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["deadlines"] });
      toast({ title: "Deadline deleted" });
    },
    onError: () => toast({ variant: "destructive", title: "Failed to delete" }),
  });

  // Sort: overdue first, then by date, then completed last
  const sorted = [...(deadlines ?? [])].sort((a, b) => {
    if (a.is_completed !== b.is_completed) return a.is_completed ? 1 : -1;
    return new Date(a.deadline_at).getTime() - new Date(b.deadline_at).getTime();
  });

  const upcoming = sorted.filter((d) => !d.is_completed);
  const completed = sorted.filter((d) => d.is_completed);
  const displayed = filter === "completed" ? completed : filter === "upcoming" ? upcoming : sorted;

  const overdueCount = upcoming.filter((d) => getUrgency(d.deadline_at, false) === "overdue").length;
  const urgentCount  = upcoming.filter((d) => getUrgency(d.deadline_at, false) === "urgent").length;

  return (
    <div className="p-7 max-w-[800px] space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-serif font-semibold text-foreground leading-tight">Deadlines</h1>
          <p className="text-[13px] text-foreground/45 mt-0.5">Track grant submission and reporting deadlines</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-[12px] font-semibold text-white transition-all"
          style={{ background: "linear-gradient(135deg, #7B1F3A 0%, #9B2D4E 100%)" }}
        >
          <Plus size={13} /> New Deadline
        </button>
      </div>

      {/* Stat strip */}
      {(overdueCount > 0 || urgentCount > 0) && (
        <div className="flex gap-3 flex-wrap">
          {overdueCount > 0 && (
            <div className="flex items-center gap-2 px-3.5 py-2.5 rounded-xl bg-red-50 border border-red-100">
              <AlertTriangle size={13} className="text-red-600" />
              <span className="text-[12px] font-semibold text-red-700">{overdueCount} overdue</span>
            </div>
          )}
          {urgentCount > 0 && (
            <div className="flex items-center gap-2 px-3.5 py-2.5 rounded-xl bg-orange-50 border border-orange-100">
              <Clock size={13} className="text-orange-600" />
              <span className="text-[12px] font-semibold text-orange-700">{urgentCount} due this week</span>
            </div>
          )}
        </div>
      )}

      {/* New form */}
      {showForm && <NewDeadlineForm onClose={() => setShowForm(false)} />}

      {/* Filter tabs */}
      <div className="flex gap-1">
        {(["upcoming", "all", "completed"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={cn(
              "px-3 py-1.5 rounded-lg text-[12px] font-medium capitalize transition-colors",
              filter === f
                ? "bg-og-burgundy/10 text-og-burgundy font-semibold"
                : "text-foreground/45 hover:text-foreground/70 hover:bg-foreground/5"
            )}
          >
            {f === "upcoming" ? `Upcoming (${upcoming.length})` : f === "completed" ? `Completed (${completed.length})` : `All (${sorted.length})`}
          </button>
        ))}
      </div>

      {/* List */}
      {isLoading ? (
        <div className="space-y-3">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-16 rounded-xl bg-foreground/5 animate-pulse" />
          ))}
        </div>
      ) : displayed.length === 0 ? (
        <div
          className="rounded-xl bg-white p-10 text-center"
          style={{ border: "1px solid hsl(220 18% 91%)" }}
        >
          <Calendar size={32} className="mx-auto text-foreground/10 mb-3" />
          <p className="text-[13px] text-foreground/40">
            {filter === "completed" ? "No completed deadlines yet" : "No upcoming deadlines"}
          </p>
          {filter !== "completed" && (
            <button
              onClick={() => setShowForm(true)}
              className="mt-3 text-[12px] font-medium text-og-burgundy hover:underline"
            >
              Add your first deadline →
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          {displayed.map((deadline: DeadlineRow) => {
            const urgency = getUrgency(deadline.deadline_at, deadline.is_completed);
            const leftBorder = {
              overdue: "border-l-red-400",
              urgent:  "border-l-orange-400",
              soon:    "border-l-amber-400",
              normal:  "border-l-foreground/10",
              done:    "border-l-emerald-300",
            }[urgency];

            return (
              <div
                key={deadline.id}
                className={cn(
                  "flex items-start gap-3 rounded-xl bg-white px-4 py-3.5 border-l-[3px] transition-all",
                  leftBorder,
                  deadline.is_completed && "opacity-60"
                )}
                style={{ border: "1px solid hsl(220 18% 92%)", borderLeftWidth: "3px", boxShadow: "0 1px 2px 0 rgb(0 0 0 / 0.03)" }}
              >
                {/* Complete button */}
                <button
                  onClick={() => !deadline.is_completed && complete.mutate(deadline.id)}
                  disabled={deadline.is_completed || complete.isPending}
                  className={cn(
                    "mt-0.5 h-5 w-5 rounded-full border-2 flex items-center justify-center shrink-0 transition-all",
                    deadline.is_completed
                      ? "border-emerald-400 bg-emerald-400"
                      : "border-foreground/20 hover:border-og-burgundy hover:bg-og-burgundy/5"
                  )}
                >
                  {deadline.is_completed && <Check size={10} strokeWidth={3} className="text-white" />}
                </button>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-3 flex-wrap">
                    <div className="flex-1 min-w-0">
                      <p className={cn(
                        "text-[13px] font-medium text-foreground/85 leading-snug",
                        deadline.is_completed && "line-through text-foreground/40"
                      )}>
                        {deadline.title}
                      </p>
                      <div className="flex items-center gap-2 mt-1 flex-wrap">
                        <span className="text-[11px] text-foreground/40 flex items-center gap-1">
                          <Calendar size={9} />
                          {new Date(deadline.deadline_at).toLocaleDateString("en-US", {
                            month: "short", day: "numeric", year: "numeric",
                          })}
                        </span>
                        {deadline.type && (
                          <span className="text-[10px] font-medium text-foreground/35 bg-foreground/5 px-1.5 py-0.5 rounded">
                            {DEADLINE_TYPE_LABELS[deadline.type] ?? deadline.type}
                          </span>
                        )}
                        {deadline.notes && (
                          <span className="text-[11px] text-foreground/40 italic truncate max-w-[220px]">{deadline.notes}</span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <DeadlineBadge deadline_at={deadline.deadline_at} is_completed={deadline.is_completed} />
                      <button
                        onClick={() => remove.mutate(deadline.id)}
                        disabled={remove.isPending}
                        className="text-foreground/20 hover:text-red-400 transition-colors disabled:opacity-40"
                        title="Delete"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
