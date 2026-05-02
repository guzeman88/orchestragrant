import { z } from "zod";

// ─── Enums ──────────────────────────────────────────────────────────────────────

export const UserRole = {
  OWNER: "owner",
  DIRECTOR: "director",
  GRANT_WRITER: "grant_writer",
  STAFF: "staff",
  READ_ONLY: "read_only",
} as const;
export type UserRole = (typeof UserRole)[keyof typeof UserRole];

export const OrgType = {
  SYMPHONY: "symphony",
  CHAMBER_ORCHESTRA: "chamber_orchestra",
  OPERA: "opera",
  CHORUS: "chorus",
  PERFORMING_ARTS: "performing_arts",
  OTHER: "other",
} as const;
export type OrgType = (typeof OrgType)[keyof typeof OrgType];

export const ApplicationStage = {
  PROSPECTING: "prospecting",
  QUALIFYING: "qualifying",
  WRITING: "writing",
  INTERNAL_REVIEW: "internal_review",
  DIRECTOR_REVIEW: "director_review",
  BOARD_APPROVAL: "board_approval",
  READY_TO_SUBMIT: "ready_to_submit",
  SUBMITTED: "submitted",
  UNDER_REVIEW: "under_review",
  AWARDED: "awarded",
  DECLINED: "declined",
  WITHDRAWN: "withdrawn",
} as const;
export type ApplicationStage =
  (typeof ApplicationStage)[keyof typeof ApplicationStage];

export const GrantType = {
  GENERAL_OPERATING: "general_operating",
  PROJECT: "project",
  CAPITAL: "capital",
  ENDOWMENT: "endowment",
  EMERGENCY: "emergency",
  COMMISSIONING: "commissioning",
  EDUCATION: "education",
  TOURING: "touring",
  RECORDING: "recording",
  TECHNICAL_ASSISTANCE: "technical_assistance",
} as const;
export type GrantType = (typeof GrantType)[keyof typeof GrantType];

export const FunderType = {
  FOUNDATION: "foundation",
  GOVERNMENT_FEDERAL: "government_federal",
  GOVERNMENT_STATE: "government_state",
  GOVERNMENT_LOCAL: "government_local",
  CORPORATION: "corporation",
  INDIVIDUAL: "individual",
} as const;
export type FunderType = (typeof FunderType)[keyof typeof FunderType];

export const DocumentCategory = {
  MISSION_VISION: "mission_vision",
  STRATEGIC_PLAN: "strategic_plan",
  ANNUAL_REPORT: "annual_report",
  AUDIT: "audit",
  FORM_990: "form_990",
  IRS_DETERMINATION: "irs_determination",
  BOARD_LIST: "board_list",
  BUDGET: "budget",
  PROGRAM_DESCRIPTIONS: "program_descriptions",
  EVALUATION_REPORTS: "evaluation_reports",
  PRESS_KIT: "press_kit",
  POLICIES: "policies",
  OTHER: "other",
} as const;
export type DocumentCategory =
  (typeof DocumentCategory)[keyof typeof DocumentCategory];

export const SubscriptionTier = {
  STARTER: "starter",
  PROFESSIONAL: "professional",
  ENTERPRISE: "enterprise",
} as const;
export type SubscriptionTier =
  (typeof SubscriptionTier)[keyof typeof SubscriptionTier];

// ─── Core Entity Types ─────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  org_id: string;
  is_active: boolean;
  is_mfa_enabled: boolean;
  avatar_url?: string;
  last_login_at?: string;
  created_at: string;
  updated_at: string;
}

export interface Organization {
  id: string;
  name: string;
  legal_name: string;
  ein: string;
  org_type: OrgType;
  subscription_tier: SubscriptionTier;
  subscription_status: "active" | "trialing" | "past_due" | "canceled";
  stripe_customer_id?: string;
  logo_url?: string;
  website?: string;
  primary_email: string;
  phone?: string;
  address_street?: string;
  address_city?: string;
  address_state?: string;
  address_zip?: string;
  founded_year?: number;
  budget_size?: number;
  staff_count?: number;
  is_onboarded: boolean;
  profile_completeness_score: number;
  created_at: string;
  updated_at: string;
}

export interface OrgProfile {
  id: string;
  orgId: string;
  mission?: string;
  vision?: string;
  programsDescription?: string;
  geographicScope?: string;
  primaryArtisticFocus?: string;
  performancesPerYear?: number;
  audienceSize?: number;
  memberMusicians?: number;
  communityImpactStatement?: string;
  diversityStatement?: string;
  updatedAt: string;
}

export interface Funder {
  id: string;
  name: string;
  type: FunderType;
  ein?: string;
  website?: string;
  primaryContact?: string;
  primaryContactEmail?: string;
  primaryContactPhone?: string;
  description?: string;
  geographicFocus?: string[];
  artsSpecific: boolean;
  givingRange?: { min: number; max: number };
  totalGrantsPerYear?: number;
  annualGivingTotal?: number;
  deadlineNotes?: string;
  preferenceNotes?: string;
  relationshipStrength?: "none" | "cold" | "warm" | "strong";
  lastContactDate?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Grant {
  id: string;
  funder_id: string;
  funder?: Funder;
  title: string;
  description?: string;
  type: GrantType;
  eligible_org_types: OrgType[];
  min_amount?: number;
  max_amount?: number;
  typical_amount?: number;
  deadline?: string;
  cycle_frequency?: "annual" | "biannual" | "rolling" | "one_time";
  application_url?: string;
  loi_required: boolean;
  reporting_required: boolean;
  match_required: boolean;
  match_percentage?: number;
  geographic_restrictions?: string[];
  budget_size_min?: number;
  budget_size_max?: number;
  is_active: boolean;
  is_verified: boolean;
  last_verified_at?: string;
  arts_specific?: boolean;
  notes?: string;
  tagline?: string;
  source?: "candid" | "grants_gov" | "scraped" | "manual";
  created_at: string;
  updated_at: string;
}

export interface Application {
  id: string;
  org_id: string;
  grant_id: string;
  grant?: Grant;
  title: string;
  stage: ApplicationStage;
  requested_amount?: number;
  awarded_amount?: number;
  submission_deadline?: string;
  submitted_at?: string;
  outcome_at?: string;
  reporting_deadline?: string;
  project_title?: string;
  project_description?: string;
  assigned_to?: string;
  assigned_user?: User;
  priority?: "low" | "medium" | "high" | "critical";
  internal_notes?: string;
  tags?: string[];
  stage_history?: StageHistoryEntry[];
  sections?: ApplicationSection[];
  created_at: string;
  updated_at: string;
}

export interface StageHistoryEntry {
  from_stage: ApplicationStage | null;
  to_stage: ApplicationStage;
  changed_by: string;
  changed_at: string;
  note?: string;
}

export interface ApplicationSection {
  id: string;
  application_id: string;
  title: string;
  prompt?: string;
  content?: string; // JSON (ProseMirror doc) or plain text
  word_limit?: number;
  char_limit?: number;
  is_required: boolean;
  sort_order: number;
  status: "not_started" | "in_progress" | "complete" | "approved";
  last_edited_by?: string;
  locked_by?: string;
  locked_at?: string;
  updated_at: string;
}

export interface OrgDocument {
  id: string;
  org_id: string;
  category: DocumentCategory;
  file_name: string;
  file_key: string; // S3 key
  file_size_bytes?: number;
  mime_type?: string;
  uploaded_by: string;
  uploaded_at: string;
  processed_at?: string;
  processing_status: "pending" | "processing" | "complete" | "failed";
  extracted_text_length?: number;
  year?: number;
  description?: string;
  tags?: string[];
  created_at?: string;
}

export interface Deadline {
  id: string;
  org_id: string;
  application_id?: string;
  grant_id?: string;
  title: string;
  deadline_at: string;
  type:
    | "application"
    | "loi"
    | "report"
    | "award_decision"
    | "meeting"
    | "other";
  reminder_days: number[];
  notes?: string;
  is_completed: boolean;
  completed_at?: string;
  created_at: string;
}

export interface Award {
  id: string;
  orgId: string;
  applicationId: string;
  application?: Application;
  funderId: string;
  funder?: Funder;
  amount: number;
  awardedAt: string;
  periodStart?: string;
  periodEnd?: string;
  agreementUrl?: string;
  restrictionType: "unrestricted" | "restricted" | "project";
  reportingSchedule?: ReportingScheduleEntry[];
  totalSpent?: number;
  totalRemaining?: number;
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ReportingScheduleEntry {
  dueDate: string;
  type: "interim" | "final" | "financial";
  submittedAt?: string;
  status: "pending" | "submitted" | "approved";
}

// ─── API Request/Response Types ────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  nextCursor?: string;
  hasMore: boolean;
}

export interface ApiError {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance?: string;
  errors?: Record<string, string[]>;
}

// ─── Auth ──────────────────────────────────────────────────────────────────────

export interface LoginRequest {
  email: string;
  password: string;
  totpCode?: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
  user: User;
  org: Organization;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RefreshTokenResponse {
  access_token: string;
  expires_in: number;
}

// ─── Zod Schemas ───────────────────────────────────────────────────────────────

export const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(1, "Password is required"),
  totp_code: z.string().optional(),
});
export type LoginFormData = z.infer<typeof loginSchema>;

export const orgProfileSchema = z.object({
  mission: z.string().max(2000).optional(),
  vision: z.string().max(2000).optional(),
  programsDescription: z.string().max(5000).optional(),
  geographicScope: z.string().max(500).optional(),
  primaryArtisticFocus: z.string().max(500).optional(),
  performancesPerYear: z.number().int().min(0).max(1000).optional(),
  audienceSize: z.number().int().min(0).optional(),
  memberMusicians: z.number().int().min(0).optional(),
  communityImpactStatement: z.string().max(2000).optional(),
  diversityStatement: z.string().max(2000).optional(),
});
export type OrgProfileFormData = z.infer<typeof orgProfileSchema>;

export const createApplicationSchema = z.object({
  grantId: z.string().uuid(),
  title: z.string().min(1).max(500),
  requestedAmount: z.number().min(0).optional(),
  submissionDeadline: z.string().datetime().optional(),
  projectTitle: z.string().max(500).optional(),
  projectDescription: z.string().max(5000).optional(),
  assignedTo: z.string().uuid().optional(),
  priority: z.enum(["low", "medium", "high", "critical"]).optional(),
});
export type CreateApplicationFormData = z.infer<typeof createApplicationSchema>;

export const grantSearchSchema = z.object({
  query: z.string().optional(),
  type: z.nativeEnum(GrantType).optional(),
  funderType: z.nativeEnum(FunderType).optional(),
  minAmount: z.number().optional(),
  maxAmount: z.number().optional(),
  deadlineBefore: z.string().optional(),
  deadlineAfter: z.string().optional(),
  artsSpecific: z.boolean().optional(),
  isActive: z.boolean().default(true),
  page: z.number().int().min(1).default(1),
  pageSize: z.number().int().min(1).max(100).default(25),
  sortBy: z.enum(["deadline", "amount", "relevance", "createdAt"]).default("relevance"),
  sortOrder: z.enum(["asc", "desc"]).default("desc"),
});
export type GrantSearchParams = z.infer<typeof grantSearchSchema>;

// ─── WebSocket Event Types ─────────────────────────────────────────────────────

export type WsEventType =
  | "section.locked"
  | "section.unlocked"
  | "section.updated"
  | "application.stage_changed"
  | "deadline.reminder"
  | "notification.new";

export interface WsEvent<T = unknown> {
  type: WsEventType;
  payload: T;
  timestamp: string;
}

export interface SectionLockedPayload {
  sectionId: string;
  applicationId: string;
  lockedBy: string;
  lockedByName: string;
}

export interface StageChangedPayload {
  applicationId: string;
  fromStage: ApplicationStage;
  toStage: ApplicationStage;
  changedBy: string;
}
