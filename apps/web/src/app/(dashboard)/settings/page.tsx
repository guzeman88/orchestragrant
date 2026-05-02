"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, UserPlus, UserX } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/stores/auth-store";
import { orgsApi, usersApi } from "@/lib/api";
import { toast } from "@/hooks/use-toast";
import type { User } from "@orchestragrant/types";

const TAB_LIST = ["Organization", "Team", "Billing"] as const;
type Tab = (typeof TAB_LIST)[number];

const orgSchema = z.object({
  name: z.string().min(2, "Name is required"),
  website: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  phone: z.string().optional(),
  ein: z.string().optional(),
});
type OrgFormData = z.infer<typeof orgSchema>;

const profileSchema = z.object({
  mission: z.string().optional(),
  vision: z.string().optional(),
  programs_description: z.string().optional(),
  community_impact_statement: z.string().optional(),
  performances_per_year: z.coerce.number().optional(),
  audience_size: z.coerce.number().optional(),
  member_musicians: z.coerce.number().optional(),
});
type ProfileFormData = z.infer<typeof profileSchema>;

const inviteSchema = z.object({
  email: z.string().email(),
  first_name: z.string().min(1, "Required"),
  last_name: z.string().min(1, "Required"),
  role: z.enum(["viewer", "writer", "manager", "director", "owner"]),
});
type InviteFormData = z.infer<typeof inviteSchema>;

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<Tab>("Organization");

  return (
    <div className="p-7 space-y-6 max-w-[760px]">
      <h2 className="font-serif text-2xl font-semibold text-foreground leading-tight">Settings</h2>

      {/* Tab strip */}
      <div
        className="flex gap-0.5 p-1 rounded-xl bg-muted/50 w-fit"
        style={{ border: "1px solid hsl(220 18% 91%)" }}
      >
        {TAB_LIST.map((t) => (
          <button
            key={t}
            onClick={() => setActiveTab(t)}
            className={`px-4 py-1.5 text-[12px] font-semibold rounded-lg transition-all duration-150 ${
              activeTab === t
                ? "bg-white text-foreground shadow-sm"
                : "text-foreground/50 hover:text-foreground/70"
            }`}
            style={activeTab === t ? { boxShadow: "0 1px 3px 0 rgb(0 0 0 / 0.08)" } : undefined}
          >
            {t}
          </button>
        ))}
      </div>

      {activeTab === "Organization" && <OrgSettings />}
      {activeTab === "Team" && <TeamSettings />}
      {activeTab === "Billing" && <BillingSettings />}
    </div>
  );
}

const CARD_STYLE = {
  border: "1px solid hsl(220 18% 91%)",
  boxShadow: "0 1px 3px 0 rgb(0 0 0 / 0.05)",
};

const SECTION_BORDER = { borderBottom: "1px solid hsl(220 18% 93%)" };

const TEXTAREA_CLASS =
  "w-full rounded-lg border border-input bg-background px-3 py-2.5 text-[13px] min-h-[80px] resize-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/30 focus-visible:border-primary/40 transition-all placeholder:text-muted-foreground/50";

function OrgSettings() {
  const qc = useQueryClient();
  const { data: org } = useQuery({ queryKey: ["org"], queryFn: () => orgsApi.getMe() });
  const { data: profile } = useQuery({ queryKey: ["org-profile"], queryFn: () => orgsApi.getProfile() });

  const orgForm = useForm<OrgFormData>({ resolver: zodResolver(orgSchema), values: org ? { name: org.name ?? "", website: org.website ?? "", phone: (org as any).phone ?? "", ein: (org as any).ein ?? "" } : undefined });
  const profileForm = useForm<ProfileFormData>({ resolver: zodResolver(profileSchema), values: profile as any });

  const saveOrg = useMutation({
    mutationFn: (d: OrgFormData) => orgsApi.update(d as any),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["org"] }); toast({ title: "Organization saved" }); },
    onError: () => toast({ variant: "destructive", title: "Save failed" }),
  });
  const saveProfile = useMutation({
    mutationFn: (d: ProfileFormData) => orgsApi.updateProfile(d as any),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["org-profile"] }); toast({ title: "Profile saved" }); },
    onError: () => toast({ variant: "destructive", title: "Save failed" }),
  });

  return (
    <div className="space-y-5">
      {/* Profile completeness */}
      {org?.profile_completeness_score !== undefined && (
        <div className="rounded-xl bg-white p-4 space-y-2.5" style={CARD_STYLE}>
          <div className="flex items-center justify-between">
            <span className="text-[12px] font-semibold text-foreground/70">Profile Completeness</span>
            <span className="text-[12px] font-bold tabular-nums" style={{ color: "#7B1F3A" }}>
              {org.profile_completeness_score}%
            </span>
          </div>
          <div className="h-1.5 rounded-full bg-muted overflow-hidden">
            <div
              className="h-full rounded-full transition-all"
              style={{ width: `${org.profile_completeness_score}%`, background: "linear-gradient(90deg, #7B1F3A 0%, #C9A84C 100%)" }}
            />
          </div>
        </div>
      )}

      {/* Basic info */}
      <div className="rounded-xl bg-white overflow-hidden" style={CARD_STYLE}>
        <div className="px-5 py-4" style={SECTION_BORDER}>
          <h3 className="text-[13px] font-semibold text-foreground/80">Basic Information</h3>
        </div>
        <form onSubmit={orgForm.handleSubmit((d) => saveOrg.mutate(d))} className="p-5 space-y-4">
          <FormField label="Organization Name" error={orgForm.formState.errors.name?.message}>
            <Input {...orgForm.register("name")} />
          </FormField>
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Website" error={orgForm.formState.errors.website?.message}>
              <Input type="url" placeholder="https://" {...orgForm.register("website")} />
            </FormField>
            <FormField label="Phone">
              <Input {...orgForm.register("phone")} />
            </FormField>
          </div>
          <FormField label="EIN">
            <Input placeholder="xx-xxxxxxx" {...orgForm.register("ein")} />
          </FormField>
          <div className="flex justify-end pt-1">
            <SaveButton pending={saveOrg.isPending} label="Save" />
          </div>
        </form>
      </div>

      {/* Grant profile */}
      <div className="rounded-xl bg-white overflow-hidden" style={CARD_STYLE}>
        <div className="px-5 py-4" style={SECTION_BORDER}>
          <h3 className="text-[13px] font-semibold text-foreground/80">Grant Profile</h3>
          <p className="text-[11px] text-foreground/40 mt-0.5">Used to inform AI-assisted narrative drafting.</p>
        </div>
        <form onSubmit={profileForm.handleSubmit((d) => saveProfile.mutate(d))} className="p-5 space-y-4">
          <FormField label="Mission Statement">
            <textarea className={TEXTAREA_CLASS} {...profileForm.register("mission")} />
          </FormField>
          <FormField label="Vision">
            <textarea className={TEXTAREA_CLASS} {...profileForm.register("vision")} />
          </FormField>
          <FormField label="Programs Description">
            <textarea className={TEXTAREA_CLASS} {...profileForm.register("programs_description")} />
          </FormField>
          <FormField label="Community Impact Statement">
            <textarea className={TEXTAREA_CLASS} {...profileForm.register("community_impact_statement")} />
          </FormField>
          <div className="grid grid-cols-3 gap-4">
            <FormField label="Performances / Year">
              <Input type="number" {...profileForm.register("performances_per_year")} />
            </FormField>
            <FormField label="Audience Size">
              <Input type="number" {...profileForm.register("audience_size")} />
            </FormField>
            <FormField label="Member Musicians">
              <Input type="number" {...profileForm.register("member_musicians")} />
            </FormField>
          </div>
          <div className="flex justify-end pt-1">
            <SaveButton pending={saveProfile.isPending} label="Save Profile" />
          </div>
        </form>
      </div>
    </div>
  );
}

function TeamSettings() {
  const qc = useQueryClient();
  const { data: users } = useQuery({ queryKey: ["users"], queryFn: () => usersApi.list() });
  const { register, handleSubmit, reset, formState: { errors } } = useForm<InviteFormData>({
    resolver: zodResolver(inviteSchema),
    defaultValues: { role: "writer" },
  });

  const invite = useMutation({
    mutationFn: (d: InviteFormData) => usersApi.invite(d),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["users"] }); reset(); toast({ title: "Invitation sent" }); },
    onError: () => toast({ variant: "destructive", title: "Invite failed" }),
  });

  const deactivate = useMutation({
    mutationFn: (id: string) => usersApi.deactivate(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });

  const memberList = users ?? [];

  return (
    <div className="space-y-5">
      {/* Member list */}
      <div className="rounded-xl bg-white overflow-hidden" style={CARD_STYLE}>
        <div className="px-5 py-4" style={SECTION_BORDER}>
          <h3 className="text-[13px] font-semibold text-foreground/80">Team Members</h3>
        </div>
        {memberList.length === 0 ? (
          <div className="px-5 py-8 text-center">
            <p className="text-[13px] text-foreground/35">No team members yet.</p>
          </div>
        ) : (
          <div className="divide-y divide-border/40">
            {memberList.map((u: User) => (
              <div key={u.id} className="flex items-center justify-between px-5 py-3.5">
                <div>
                  <p className="text-[13px] font-semibold text-foreground/80">{u.first_name} {u.last_name}</p>
                  <p className="text-[11px] text-foreground/40 mt-0.5">{u.email} · <span className="capitalize">{u.role}</span></p>
                </div>
                {u.is_active && (
                  <button
                    className="h-7 w-7 rounded-md flex items-center justify-center text-foreground/20 hover:text-red-500 hover:bg-red-50 transition-all"
                    onClick={() => deactivate.mutate(u.id)}
                    aria-label="Deactivate"
                  >
                    <UserX size={13} />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Invite form */}
      <div className="rounded-xl bg-white overflow-hidden" style={CARD_STYLE}>
        <div className="px-5 py-4" style={SECTION_BORDER}>
          <h3 className="text-[13px] font-semibold text-foreground/80">Invite Team Member</h3>
        </div>
        <form onSubmit={handleSubmit((d) => invite.mutate(d))} className="p-5 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <FormField label="First Name" error={errors.first_name?.message}>
              <Input {...register("first_name")} />
            </FormField>
            <FormField label="Last Name" error={errors.last_name?.message}>
              <Input {...register("last_name")} />
            </FormField>
          </div>
          <FormField label="Email" error={errors.email?.message}>
            <Input type="email" {...register("email")} />
          </FormField>
          <FormField label="Role">
            <select
              className="flex h-9 w-full rounded-lg border border-input bg-background px-3 text-[13px] focus:outline-none focus:ring-2 focus:ring-ring/30 transition-all"
              {...register("role")}
            >
              <option value="viewer">Viewer</option>
              <option value="writer">Writer</option>
              <option value="manager">Manager</option>
              <option value="director">Director</option>
              <option value="owner">Owner</option>
            </select>
          </FormField>
          <div className="flex justify-end pt-1">
            <button
              type="submit"
              disabled={invite.isPending}
              className="inline-flex items-center gap-2 text-[12px] font-medium text-white rounded-lg px-4 py-2 transition-all hover:opacity-90 disabled:opacity-50"
              style={{ background: "linear-gradient(135deg, #7B1F3A 0%, #9B2D4E 100%)" }}
            >
              {invite.isPending ? <Loader2 size={12} className="animate-spin" /> : <UserPlus size={12} />}
              Send Invite
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function BillingSettings() {
  const { org } = useAuthStore();

  const tiers = [
    { name: "Starter", price: "$99", period: "/mo", features: ["1 user", "50 grants/mo", "Basic AI drafting"] },
    { name: "Professional", price: "$249", period: "/mo", features: ["Up to 5 users", "Unlimited grants", "Full AI suite", "Priority support"] },
    { name: "Enterprise", price: "Custom", period: "", features: ["Unlimited users", "White-glove onboarding", "Custom integrations", "SLA"] },
  ];

  const currentPlan = org?.subscription_tier?.toLowerCase() ?? "starter";

  return (
    <div className="space-y-5">
      <div className="rounded-xl bg-white p-5 space-y-2" style={CARD_STYLE}>
        <h3 className="text-[13px] font-semibold text-foreground/80">Current Plan</h3>
        <p className="text-[12px] text-foreground/50">
          Subscription tier: <span className="font-semibold capitalize text-foreground/80">{org?.subscription_tier ?? "Starter"}</span>
        </p>
        <p className="text-[12px] text-foreground/40">Billing is managed via Stripe. To change your plan, upgrade below or contact support.</p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {tiers.map((tier) => {
          const isCurrent = currentPlan === tier.name.toLowerCase();
          return (
            <div
              key={tier.name}
              className="rounded-xl bg-white p-5 space-y-4 transition-all"
              style={{
                border: isCurrent ? "2px solid #7B1F3A" : "1px solid hsl(220 18% 91%)",
                boxShadow: isCurrent
                  ? "0 4px 12px 0 rgba(123,31,58,0.12)"
                  : "0 1px 3px 0 rgb(0 0 0 / 0.05)",
              }}
            >
              <div>
                <div className="flex items-baseline gap-0.5">
                  <span className="text-xl font-bold text-foreground/90">{tier.price}</span>
                  {tier.period && <span className="text-[12px] text-foreground/40">{tier.period}</span>}
                </div>
                <p className="text-[12px] font-semibold text-foreground/60 mt-0.5">{tier.name}</p>
              </div>
              <ul className="space-y-1.5">
                {tier.features.map((f) => (
                  <li key={f} className="flex items-center gap-2 text-[12px] text-foreground/55">
                    <span className="h-1.5 w-1.5 rounded-full bg-og-gold shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>
              <button
                disabled={isCurrent}
                className="w-full text-[12px] font-medium py-1.5 rounded-lg border transition-all hover:opacity-90 disabled:opacity-50"
                style={
                  isCurrent
                    ? { background: "rgba(123,31,58,0.06)", color: "#7B1F3A", borderColor: "rgba(123,31,58,0.2)" }
                    : { background: "white", color: "#6b7280", borderColor: "hsl(220 18% 88%)" }
                }
              >
                {isCurrent ? "Current Plan" : `Upgrade to ${tier.name}`}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function FormField({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label className="text-[11px] font-semibold uppercase tracking-wider text-foreground/40">{label}</Label>
      {children}
      {error && <p className="text-[11px] text-destructive">{error}</p>}
    </div>
  );
}

function SaveButton({ pending, label }: { pending: boolean; label: string }) {
  return (
    <button
      type="submit"
      disabled={pending}
      className="inline-flex items-center gap-2 text-[12px] font-medium text-white rounded-lg px-4 py-2 transition-all hover:opacity-90 disabled:opacity-50"
      style={{ background: "linear-gradient(135deg, #7B1F3A 0%, #9B2D4E 100%)" }}
    >
      {pending && <Loader2 size={12} className="animate-spin" />}
      {label}
    </button>
  );
}
