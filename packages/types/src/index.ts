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
  firstName: string;
  lastName: string;
  role: UserRole;
  orgId: string;
  isActive: boolean;
  isMfaEnabled: boolean;
  avatarUrl?: string;
  lastLoginAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Organization {
  id: string;
  name: string;
  legalName: string;
  ein: string;
  orgType: OrgType;
  subscriptionTier: SubscriptionTier;
  subscriptionStatus: "active" | "trialing" | "past_due" | "canceled";
  stripeCustomerId?: string;
  logoUrl?: string;
  website?: string;
  primaryEmail: string;
  phone?: string;
  addressStreet?: string;
  addressCity?: string;
  addressState?: string;
  addressZip?: string;
  foundedYear?: number;
  budgetSize?: number;
  staffCount?: number;
  isOnboarded: boolean;
  profileCompletenessScore: number;
  createdAt: string;
  updatedAt: string;
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
  funderId: string;
  funder?: Funder;
  title: string;
  description?: string;
  type: GrantType;
  eligibleOrgTypes: OrgType[];
  minAmount?: number;
  maxAmount?: number;
  typicalAmount?: number;
  deadline?: string;
  cycleFrequency?: "annual" | "biannual" | "rolling" | "one_time";
  applicationUrl?: string;
  loiRequired: boolean;
  reportingRequired: boolean;
  matchRequired: boolean;
  matchPercentage?: number;
  geographicRestrictions?: string[];
  budgetSizeMin?: number;
  budgetSizeMax?: number;
  isActive: boolean;
  isVerified: boolean;
  lastVerifiedAt?: string;
  notes?: string;
  tagline?: string;
  source?: "candid" | "grants_gov" | "scraped" | "manual";
  createdAt: string;
  updatedAt: string;
}

export interface Application {
  id: string;
  orgId: string;
  grantId: string;
  grant?: Grant;
  title: string;
  stage: ApplicationStage;
  requestedAmount?: number;
  awardedAmount?: number;
  submissionDeadline?: string;
  submittedAt?: string;
  outcomeAt?: string;
  reportingDeadline?: string;
  projectTitle?: string;
  projectDescription?: string;
  assignedTo?: string;
  assignedUser?: User;
  priority?: "low" | "medium" | "high" | "critical";
  internalNotes?: string;
  tags?: string[];
  stageHistory?: StageHistoryEntry[];
  sections?: ApplicationSection[];
  createdAt: string;
  updatedAt: string;
}

export interface StageHistoryEntry {
  fromStage: ApplicationStage | null;
  toStage: ApplicationStage;
  changedBy: string;
  changedAt: string;
  note?: string;
}

export interface ApplicationSection {
  id: string;
  applicationId: string;
  title: string;
  prompt?: string;
  content?: string; // JSON (ProseMirror doc) or plain text
  wordLimit?: number;
  charLimit?: number;
  isRequired: boolean;
  sortOrder: number;
  status: "not_started" | "in_progress" | "complete" | "approved";
  lastEditedBy?: string;
  lockedBy?: string;
  lockedAt?: string;
  updatedAt: string;
}

export interface OrgDocument {
  id: string;
  orgId: string;
  category: DocumentCategory;
  fileName: string;
  fileKey: string; // S3 key
  fileSizeBytes?: number;
  mimeType?: string;
  uploadedBy: string;
  uploadedAt: string;
  processedAt?: string;
  processingStatus: "pending" | "processing" | "complete" | "failed";
  extractedTextLength?: number;
  year?: number;
  description?: string;
  tags?: string[];
}

export interface Deadline {
  id: string;
  orgId: string;
  applicationId?: string;
  grantId?: string;
  title: string;
  deadlineAt: string;
  type:
    | "application"
    | "loi"
    | "report"
    | "award_decision"
    | "meeting"
    | "other";
  reminderDays: number[];
  notes?: string;
  isCompleted: boolean;
  completedAt?: string;
  createdAt: string;
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
