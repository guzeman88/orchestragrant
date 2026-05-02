# Data Models — TypeScript Interfaces & Zod Schemas

**Project:** OrchestraGrant Platform  
**Version:** 1.0  
**Last Updated:** 2026-05-01

---

## 1. Overview

This document defines the TypeScript interfaces and Zod validation schemas shared between the frontend and backend (via a shared `packages/types` package in the monorepo). These types correspond to the database schema defined in [database-schema.md](../data/database-schema.md) and the API contracts in [api-reference.md](../api/api-reference.md).

---

## 2. Shared Package Structure

```
packages/
  types/
    src/
      entities/
        organization.ts
        grant.ts
        application.ts
        award.ts
        user.ts
        deadline.ts
        document.ts
        discovery.ts
      api/
        requests.ts
        responses.ts
        websocket.ts
      schemas/
        organization.schema.ts
        grant.schema.ts
        application.schema.ts
        award.schema.ts
      index.ts
```

---

## 3. Core Entity Types

### 3.1 User & Auth

```typescript
// entities/user.ts

export type UserRole = 
  | 'admin' 
  | 'staff' 
  | 'artistic_director' 
  | 'board_member' 
  | 'read_only';

export interface User {
  id: string;                   // UUID
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  orgId: string;
  isActive: boolean;
  mfaEnabled: boolean;
  lastLoginAt: string | null;   // ISO 8601
  createdAt: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;            // seconds
}

export interface AuthSession {
  user: User;
  tokens: AuthTokens;
}
```

### 3.2 Organization

```typescript
// entities/organization.ts

export interface Organization {
  id: string;
  name: string;
  ein: string | null;
  websiteUrl: string | null;
  primaryPhone: string | null;
  primaryAddress: Address | null;
  subscriptionTier: 'starter' | 'professional' | 'enterprise';
  subscriptionStatus: 'active' | 'past_due' | 'cancelled' | 'trialing';
  createdAt: string;
}

export interface Address {
  street1: string;
  street2?: string;
  city: string;
  state: string;
  zip: string;
  country: string;
}

export interface OrgProfile {
  orgId: string;
  missionStatement: string | null;
  visionStatement: string | null;
  coreValues: string[];
  descriptionShort: string | null;
  descriptionLong: string | null;
  ensembleType: EnsembleType;
  rosterSize: number | null;
  musicianClassification: 'per_service' | 'salaried' | 'hybrid' | null;
  primaryVenue: string | null;
  seasonStructure: string | null;
  geographicServiceArea: string | null;
  populationsServed: string[];
  missionTags: string[];
  activityTags: string[];
  leagueMember: boolean;
  afmSignatory: boolean;
  completenessScore: number;    // 0–100
  updatedAt: string;
}

export type EnsembleType = 
  | 'chamber_orchestra' 
  | 'full_orchestra' 
  | 'sinfonietta' 
  | 'symphony' 
  | 'philharmonic' 
  | 'other';

export interface OrgFinancials {
  id: string;
  orgId: string;
  fiscalYear: number;
  totalBudget: number;
  earnedRevenue: number | null;
  contributedRevenue: number | null;
  foundationGrants: number | null;
  governmentGrants: number | null;
  individualDonations: number | null;
  corporateSupport: number | null;
  endowmentValue: number | null;
  operatingReserves: number | null;
  auditStatus: 'audited' | 'reviewed' | 'compiled' | null;
  createdAt: string;
}

export interface BoardMember {
  id: string;
  orgId: string;
  firstName: string;
  lastName: string;
  title: string;
  boardRole: 'chair' | 'vice_chair' | 'treasurer' | 'secretary' | 'at_large';
  affiliation: string | null;
  affiliationTitle: string | null;
  joinDate: string | null;      // ISO date string
  termExpiry: string | null;
  committees: string[];
  isDonor: boolean;
  isActive: boolean;
}
```

### 3.3 Grants & Funders

```typescript
// entities/grant.ts

export type GrantType = 
  | 'general_operating' 
  | 'project' 
  | 'capacity_building' 
  | 'commissioning' 
  | 'education' 
  | 'emergency' 
  | 'capital' 
  | 'endowment';

export type FunderType = 
  | 'federal_government' 
  | 'state_government' 
  | 'local_government' 
  | 'private_foundation' 
  | 'community_foundation' 
  | 'corporate_foundation' 
  | 'performing_arts_service_org';

export type GrantStatus = 
  | 'discovered' 
  | 'pending_review' 
  | 'draft' 
  | 'verified' 
  | 'under_review' 
  | 'discontinued';

export type CycleType = 'annual' | 'biannual' | 'rolling' | 'one_time';

export interface Funder {
  id: string;
  name: string;
  funderType: FunderType;
  websiteUrl: string | null;
  guidelinesUrl: string | null;
  headquartersState: string | null;
  ein: string | null;
  totalGivingAnnual: number | null;
  candid_orgId: string | null;
  primaryContactId: string | null;
}

export interface Grant {
  id: string;
  funderId: string;
  funderName: string;         // denormalized for display
  name: string;
  grantType: GrantType;
  description: string | null;
  guidelinesUrl: string | null;
  guidelinesS3Key: string | null;
  awardMin: number | null;
  awardMax: number | null;
  awardTypical: number | null;
  cycleType: CycleType | null;
  loiRequired: boolean;
  matchRequired: boolean;
  matchPercent: number | null;
  eligibleOrgTypes: string[];
  geographicRestriction: string | null;
  status: GrantStatus;
  relevanceScore: number | null;      // 0–100
  lastVerifiedAt: string | null;
  requiredSections: string[];
  requiredAttachments: string[];
}

export interface GrantCycle {
  id: string;
  grantId: string;
  cycleName: string | null;
  openDate: string | null;
  applicationDeadline: string;        // ISO date
  loiDeadline: string | null;
  announcementDate: string | null;
  programPeriodStart: string | null;
  programPeriodEnd: string | null;
  awardAmountsThisCycle: number | null;
  notes: string | null;
}
```

### 3.4 Applications

```typescript
// entities/application.ts

export type ApplicationStage = 
  | 'considering'
  | 'in_progress'
  | 'staff_review'
  | 'director_review'
  | 'board_review'
  | 'ready_to_submit'
  | 'submitted'
  | 'under_review'
  | 'awarded'
  | 'declined'
  | 'archived'
  | 'withdrawn';

export type SectionStatus = 
  | 'empty' 
  | 'generating' 
  | 'drafted' 
  | 'in_review' 
  | 'complete';

export interface Application {
  id: string;
  orgId: string;
  grantId: string;
  grantCycleId: string | null;
  grantName: string;            // denormalized
  funderName: string;           // denormalized
  stage: ApplicationStage;
  amountRequested: number | null;
  amountAwarded: number | null;
  applicationDeadline: string;
  loiDeadline: string | null;
  programPeriodStart: string | null;
  programPeriodEnd: string | null;
  projectName: string | null;
  assignedUserId: string | null;
  submittedAt: string | null;
  submissionMethod: string | null;
  submissionConfirmationNumber: string | null;
  outcomeRecordedAt: string | null;
  declineReason: string | null;
  willReapply: boolean | null;
  sectionCount: number;
  sectionsComplete: number;
  createdAt: string;
  updatedAt: string;
}

export interface ApplicationSection {
  id: string;
  applicationId: string;
  sectionName: string;
  sectionOrder: number;
  content: string | null;       // JSON string (Tiptap doc)
  contentPlaintext: string | null;
  wordCount: number | null;
  wordLimit: number | null;
  status: SectionStatus;
  lastGeneratedAt: string | null;
  lastGenerationJobId: string | null;
  generationSettings: GenerationSettings | null;
  updatedAt: string;
}

export interface GenerationSettings {
  emphasis: 'community_impact' | 'artistic_excellence' | 'education' | 'innovation' | 'balanced';
  tone: 'foundation' | 'government' | 'auto';
  additionalContext: string | null;
  pinnedAtomIds: string[];
}

export interface ApplicationComment {
  id: string;
  applicationId: string;
  sectionId: string | null;
  authorId: string;
  authorName: string;
  content: string;
  isResolved: boolean;
  parentCommentId: string | null;
  createdAt: string;
}

export interface ApplicationTask {
  id: string;
  applicationId: string;
  title: string;
  description: string | null;
  assigneeId: string | null;
  dueDate: string | null;
  priority: 'high' | 'normal' | 'low';
  status: 'open' | 'in_progress' | 'done';
  createdAt: string;
}

export interface StageHistoryEntry {
  id: string;
  applicationId: string;
  fromStage: ApplicationStage | null;
  toStage: ApplicationStage;
  actorId: string;
  actorName: string;
  comment: string | null;
  createdAt: string;
}
```

### 3.5 Awards

```typescript
// entities/award.ts

export interface Award {
  id: string;
  orgId: string;
  applicationId: string;
  grantId: string;
  funderName: string;           // denormalized
  grantName: string;            // denormalized
  amountAwarded: number;
  amountSpent: number;          // computed from expenditures
  grantAgreementDate: string | null;
  programPeriodStart: string;
  programPeriodEnd: string;
  reportingDeadlines: AwardDeadline[];
  stewardshipContactId: string | null;
  notes: string | null;
  createdAt: string;
}

export interface AwardExpenditure {
  id: string;
  awardId: string;
  date: string;
  category: ExpenditureCategory;
  description: string;
  amount: number;
  budgetLineItem: string | null;
  documentationS3Key: string | null;
  createdAt: string;
}

export type ExpenditureCategory = 
  | 'personnel' 
  | 'fringe_benefits' 
  | 'fees_services' 
  | 'supplies' 
  | 'travel' 
  | 'indirect' 
  | 'other';

export interface AwardDeadline {
  id: string;
  awardId: string;
  deadlineType: 'interim_report' | 'final_report' | 'budget_report' | 'other';
  dueDate: string;
  completedAt: string | null;
}

export interface ImpactData {
  id: string;
  awardId: string;
  fieldKey: string;
  fieldLabel: string;
  plannedValue: number | null;
  actualValue: number | null;
  unit: string;
  notes: string | null;
}
```

### 3.6 Deadlines

```typescript
// entities/deadline.ts

export type DeadlineType = 
  | 'application' 
  | 'loi' 
  | 'reporting' 
  | 'board_meeting' 
  | 'other';

export type DeadlineUrgency = 'overdue' | 'critical' | 'warning' | 'approaching' | 'ok';

export interface Deadline {
  id: string;
  orgId: string;
  applicationId: string | null;
  awardId: string | null;
  deadlineType: DeadlineType;
  title: string;
  dueDate: string;              // ISO date
  completedAt: string | null;
  isComplete: boolean;
  urgency: DeadlineUrgency;     // computed
  daysUntil: number;            // computed
  assigneeId: string | null;
}
```

### 3.7 Documents

```typescript
// entities/document.ts

export type DocumentCategory = 
  | 'audit' 
  | 'form_990' 
  | 'annual_report' 
  | 'strategic_plan' 
  | 'past_application' 
  | 'board_minutes' 
  | 'program_notes' 
  | 'press_release' 
  | 'evaluation_report' 
  | 'determination_letter' 
  | 'bylaws' 
  | 'w9' 
  | 'other';

export type DocumentStatus = 'processing' | 'indexed' | 'failed' | 'deleted';

export interface Document {
  id: string;
  orgId: string;
  filename: string;
  s3Key: string;
  mimeType: string;
  sizeBytes: number;
  category: DocumentCategory;
  fiscalYear: number | null;
  description: string | null;
  status: DocumentStatus;
  atomCount: number | null;     // number of extracted narrative atoms
  uploadedByUserId: string;
  uploadedAt: string;
  indexedAt: string | null;
}

export interface DocumentUploadRequest {
  filename: string;
  mimeType: string;
  sizeBytes: number;
  category: DocumentCategory;
  fiscalYear?: number;
  description?: string;
}

export interface DocumentUploadResponse {
  documentId: string;
  uploadUrl: string;            // presigned S3 URL
  expiresAt: string;
}
```

---

## 4. API Request / Response Types

```typescript
// api/requests.ts

export interface PaginationParams {
  cursor?: string;
  limit?: number;               // default 25, max 100
}

export interface GrantSearchParams extends PaginationParams {
  query?: string;
  grantTypes?: GrantType[];
  funderTypes?: FunderType[];
  awardMin?: number;
  awardMax?: number;
  geographic?: string;
  loiRequired?: boolean;
  matchRequired?: boolean;
  eligibleOnly?: boolean;
  verifiedWithin?: number;      // days
  sort?: 'relevance' | 'deadline' | 'award_asc' | 'award_desc' | 'recently_added';
}

export interface CreateApplicationRequest {
  grantId: string;
  grantCycleId?: string;
  amountRequested?: number;
  applicationDeadline: string;
  loiDeadline?: string;
  programPeriodStart?: string;
  programPeriodEnd?: string;
  projectName?: string;
  assignedUserId?: string;
  notes?: string;
  sections: CreateSectionRequest[];
}

export interface CreateSectionRequest {
  sectionName: string;
  sectionOrder: number;
  wordLimit?: number;
}

export interface GenerateSectionRequest {
  applicationId: string;
  sectionId: string;
  settings: GenerationSettings;
}

export interface TransitionStageRequest {
  targetStage: ApplicationStage;
  comment?: string;
}
```

```typescript
// api/responses.ts

export interface PaginatedResponse<T> {
  data: T[];
  meta: {
    nextCursor: string | null;
    total: number;
    hasMore: boolean;
  };
}

export interface ApiError {
  type: string;                 // URI
  title: string;
  status: number;
  detail: string;
  instance: string;
  traceId?: string;
}

export interface GenerationJobResponse {
  jobId: string;
  status: 'queued' | 'processing' | 'complete' | 'failed';
  estimatedWaitSeconds?: number;
  result?: {
    content: string;            // Tiptap JSON
    contentPlaintext: string;
    wordCount: number;
    atomsUsed: AtomReference[];
    complianceResult: ComplianceResult;
  };
}

export interface AtomReference {
  atomId: string;
  excerpt: string;
  sourceDocumentName: string;
  similarityScore: number;
}

export interface ComplianceResult {
  score: number;                // 0–100
  band: 'excellent' | 'good' | 'needs_work' | 'incomplete';
  elements: ComplianceElement[];
  unsupportedClaims: UnsupportedClaim[];
}

export interface ComplianceElement {
  label: string;
  present: boolean;
  suggestion?: string;
}

export interface UnsupportedClaim {
  text: string;
  startOffset: number;
  endOffset: number;
}
```

---

## 5. WebSocket Message Types

```typescript
// api/websocket.ts

export type WebSocketEvent = 
  | SectionGenerationProgressEvent
  | SectionGenerationCompleteEvent
  | SectionGenerationFailedEvent
  | ApplicationStageChangedEvent
  | DeadlineReminderEvent
  | DiscoveryAlertEvent
  | PresenceEvent
  | EditLockEvent;

export interface WebSocketMessage<T extends WebSocketEvent> {
  event: T['event'];
  payload: T;
  timestamp: string;
}

export interface SectionGenerationProgressEvent {
  event: 'section.generation_progress';
  jobId: string;
  sectionId: string;
  percentComplete: number;
  message: string;
}

export interface SectionGenerationCompleteEvent {
  event: 'section.generation_complete';
  jobId: string;
  sectionId: string;
  applicationId: string;
}

export interface SectionGenerationFailedEvent {
  event: 'section.generation_failed';
  jobId: string;
  sectionId: string;
  reason: string;
}

export interface ApplicationStageChangedEvent {
  event: 'application.stage_changed';
  applicationId: string;
  fromStage: ApplicationStage;
  toStage: ApplicationStage;
  actorName: string;
}

export interface DeadlineReminderEvent {
  event: 'deadline.reminder';
  deadlineId: string;
  title: string;
  daysUntil: number;
  applicationId: string | null;
}

export interface DiscoveryAlertEvent {
  event: 'discovery.new_grants';
  count: number;
  topGrant: { name: string; funder: string; relevanceScore: number; };
}

export interface PresenceEvent {
  event: 'presence.update';
  sectionId: string;
  activeUsers: { userId: string; name: string; color: string; }[];
}

export interface EditLockEvent {
  event: 'section.lock_changed';
  sectionId: string;
  lockedByUserId: string | null;
  lockedByName: string | null;
}
```

---

## 6. Zod Validation Schemas

```typescript
// schemas/application.schema.ts
import { z } from 'zod';

export const CreateApplicationSchema = z.object({
  grantId: z.string().uuid(),
  grantCycleId: z.string().uuid().optional(),
  amountRequested: z.number().positive().max(10_000_000).optional(),
  applicationDeadline: z.string().datetime(),
  loiDeadline: z.string().datetime().optional(),
  programPeriodStart: z.string().datetime().optional(),
  programPeriodEnd: z.string().datetime().optional(),
  projectName: z.string().max(255).optional(),
  assignedUserId: z.string().uuid().optional(),
  notes: z.string().max(5000).optional(),
  sections: z.array(z.object({
    sectionName: z.string().min(1).max(100),
    sectionOrder: z.number().int().min(0),
    wordLimit: z.number().int().positive().max(5000).optional(),
  })).min(1).max(20),
});

export const GenerateSectionSchema = z.object({
  applicationId: z.string().uuid(),
  sectionId: z.string().uuid(),
  settings: z.object({
    emphasis: z.enum(['community_impact', 'artistic_excellence', 'education', 'innovation', 'balanced']),
    tone: z.enum(['foundation', 'government', 'auto']),
    additionalContext: z.string().max(500).nullable(),
    pinnedAtomIds: z.array(z.string().uuid()).max(5),
  }),
});

export const TransitionStageSchema = z.object({
  targetStage: z.enum([
    'considering', 'in_progress', 'staff_review', 'director_review',
    'board_review', 'ready_to_submit', 'submitted', 'under_review',
    'awarded', 'declined', 'archived', 'withdrawn'
  ]),
  comment: z.string().max(1000).optional(),
});
```

```typescript
// schemas/organization.schema.ts
import { z } from 'zod';

export const OrgProfileUpdateSchema = z.object({
  missionStatement: z.string().max(1000).optional(),
  visionStatement: z.string().max(1000).optional(),
  coreValues: z.array(z.string().max(100)).max(12).optional(),
  descriptionShort: z.string().max(500).optional(),
  descriptionLong: z.string().max(3000).optional(),
  ensembleType: z.enum([
    'chamber_orchestra', 'full_orchestra', 'sinfonietta', 
    'symphony', 'philharmonic', 'other'
  ]).optional(),
  rosterSize: z.number().int().positive().max(500).optional(),
  musicianClassification: z.enum(['per_service', 'salaried', 'hybrid']).optional(),
  primaryVenue: z.string().max(255).optional(),
  seasonStructure: z.string().max(500).optional(),
  geographicServiceArea: z.string().max(500).optional(),
  populationsServed: z.array(z.string().max(100)).max(20).optional(),
  missionTags: z.array(z.string().max(100)).max(15).optional(),
  activityTags: z.array(z.string().max(100)).max(15).optional(),
  leagueMember: z.boolean().optional(),
  afmSignatory: z.boolean().optional(),
});

export const OrgFinancialsSchema = z.object({
  fiscalYear: z.number().int().min(2000).max(2100),
  totalBudget: z.number().positive().max(100_000_000),
  earnedRevenue: z.number().nonnegative().optional(),
  contributedRevenue: z.number().nonnegative().optional(),
  foundationGrants: z.number().nonnegative().optional(),
  governmentGrants: z.number().nonnegative().optional(),
  individualDonations: z.number().nonnegative().optional(),
  corporateSupport: z.number().nonnegative().optional(),
  endowmentValue: z.number().nonnegative().optional(),
  operatingReserves: z.number().nonnegative().optional(),
  auditStatus: z.enum(['audited', 'reviewed', 'compiled']).optional(),
});
```

---

*Last Updated: 2026-05-01*
