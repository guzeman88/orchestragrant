"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Trash2, Download, Upload, FileText, File } from "lucide-react";
import { useRef, useState } from "react";
import { documentsApi } from "@/lib/api";
import { toast } from "@/hooks/use-toast";
import { formatDate } from "@/lib/utils";
import type { OrgDocument } from "@orchestragrant/types";

const CATEGORY_LABELS: Record<string, string> = {
  financial: "Financial",
  governance: "Governance",
  program: "Program",
  legal: "Legal",
  marketing: "Marketing",
  other: "Other",
};

const CATEGORY_COLORS: Record<string, string> = {
  financial: "bg-emerald-50 text-emerald-700",
  governance: "bg-violet-50 text-violet-700",
  program: "bg-blue-50 text-blue-700",
  legal: "bg-amber-50 text-amber-700",
  marketing: "bg-pink-50 text-pink-700",
  other: "bg-muted text-foreground/50",
};

const ALLOWED_MIME: Record<string, string> = {
  "application/pdf": "pdf",
  "application/msword": "doc",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
  "application/vnd.ms-excel": "xls",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
  "text/plain": "txt",
};

// Demo documents for display without backend

export default function DocumentsPage() {
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);

  const { data: documents } = useQuery({
    queryKey: ["documents"],
    queryFn: () => documentsApi.list(),
  });

  const deleteDoc = useMutation({
    mutationFn: (id: string) => documentsApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["documents"] }); toast({ title: "Document deleted" }); },
  });

  const handleDownload = async (doc: OrgDocument) => {
    try {
      const { download_url } = await documentsApi.getDownloadUrl(doc.id);
      window.open(download_url, "_blank", "noopener,noreferrer");
    } catch {
      toast({ variant: "destructive", title: "Download failed" });
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!ALLOWED_MIME[file.type]) {
      toast({ variant: "destructive", title: "Unsupported file type" });
      return;
    }
    setUploading(true);
    try {
      const { upload_url, document_id } = await documentsApi.getUploadUrl({
        file_name: file.name,
        mime_type: file.type,
        file_size_bytes: file.size,
        category: "other",
      });
      const uploadRes = await fetch(upload_url, { method: "PUT", body: file, headers: { "Content-Type": file.type } });
      if (!uploadRes.ok) throw new Error("Upload to S3 failed");
      await documentsApi.confirmUpload(document_id);
      qc.invalidateQueries({ queryKey: ["documents"] });
      toast({ title: "Document uploaded" });
    } catch {
      toast({ variant: "destructive", title: "Upload failed" });
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const docs: OrgDocument[] = documents ?? [];

  return (
    <div className="p-7 space-y-5 max-w-[900px]">
      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <h2 className="font-serif text-2xl font-semibold text-foreground leading-tight">Documents</h2>
          <p className="text-sm text-foreground/45 mt-1">{docs.length} document{docs.length !== 1 ? "s" : ""}</p>
        </div>
        <div>
          <input ref={fileRef} type="file" accept={Object.keys(ALLOWED_MIME).join(",")} className="hidden" onChange={handleUpload} />
          <button
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            className="inline-flex items-center gap-2 text-[12px] font-medium text-white rounded-lg px-4 py-2 transition-all duration-150 hover:opacity-90 disabled:opacity-50"
            style={{ background: "linear-gradient(135deg, #7B1F3A 0%, #9B2D4E 100%)" }}
          >
            <Upload size={13} />
            {uploading ? "Uploading…" : "Upload Document"}
          </button>
        </div>
      </div>

      {/* File type hint */}
      <p className="text-[11px] text-foreground/35">
        Accepted: PDF, Word (.doc, .docx), Excel (.xls, .xlsx), plain text — used for AI-assisted grant narrative matching.
      </p>

      {/* Document list */}
      {docs.length === 0 ? (
        <div
          className="rounded-xl bg-white flex flex-col items-center justify-center py-20 text-center"
          style={{ border: "1px solid hsl(220 18% 91%)", boxShadow: "0 1px 3px 0 rgb(0 0 0 / 0.05)" }}
        >
          <FileText size={36} className="text-foreground/12 mb-3" />
          <p className="text-sm font-medium text-foreground/40">No documents yet</p>
          <p className="text-xs text-foreground/30 mt-1 max-w-xs">
            Upload financial statements, IRS letters, board lists, and more.
          </p>
        </div>
      ) : (
        <div
          className="rounded-xl bg-white overflow-hidden"
          style={{ border: "1px solid hsl(220 18% 91%)", boxShadow: "0 1px 3px 0 rgb(0 0 0 / 0.05)" }}
        >
          {/* Table header */}
          <div
            className="grid px-5 py-3"
            style={{ gridTemplateColumns: "1fr 120px 60px 80px 80px", borderBottom: "1px solid hsl(220 18% 92%)" }}
          >
            {["Document", "Category", "Year", "Uploaded", ""].map((h) => (
              <span key={h} className="text-[10px] font-semibold uppercase tracking-wider text-foreground/35">{h}</span>
            ))}
          </div>

          {/* Rows */}
          <div className="divide-y divide-border/40">
            {docs.map((doc: OrgDocument) => (
              <div
                key={doc.id}
                className="grid items-center px-5 py-3.5 hover:bg-muted/30 transition-colors"
                style={{ gridTemplateColumns: "1fr 120px 60px 80px 80px" }}
              >
                {/* File name */}
                <div className="flex items-center gap-2.5 overflow-hidden">
                  <div
                    className="h-7 w-7 rounded-lg shrink-0 flex items-center justify-center"
                    style={{ background: "rgba(123,31,58,0.08)" }}
                  >
                    <File size={13} style={{ color: "#7B1F3A" }} />
                  </div>
                  <div className="overflow-hidden">
                    <p className="text-[12px] font-semibold text-foreground/90 truncate">{doc.file_name}</p>
                    {doc.processing_status === "processing" && (
                      <p className="text-[10px] text-amber-500 font-medium">Processing…</p>
                    )}
                  </div>
                </div>

                {/* Category */}
                <span
                  className={`text-[10px] font-semibold px-2 py-0.5 rounded-full w-fit ${
                    CATEGORY_COLORS[doc.category] ?? "bg-muted text-foreground/50"
                  }`}
                >
                  {CATEGORY_LABELS[doc.category] ?? doc.category}
                </span>

                {/* Year */}
                <span className="text-[12px] text-foreground/45">{doc.year ?? "—"}</span>

                {/* Uploaded */}
                <span className="text-[11px] text-foreground/40">
                  {doc.created_at ? new Date(doc.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "—"}
                </span>

                {/* Actions */}
                <div className="flex items-center gap-0.5 justify-end">
                  <button
                    className="h-7 w-7 rounded-md flex items-center justify-center text-foreground/30 hover:text-foreground/60 hover:bg-muted/60 transition-all"
                    onClick={() => handleDownload(doc)}
                    aria-label="Download"
                  >
                    <Download size={13} />
                  </button>
                  <button
                    className="h-7 w-7 rounded-md flex items-center justify-center text-foreground/20 hover:text-red-500 hover:bg-red-50 transition-all"
                    onClick={() => deleteDoc.mutate(doc.id)}
                    aria-label="Delete"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

