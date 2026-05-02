# Module 05 — Application Lifecycle

**Project:** OrchestraGrant Platform  
**Version:** 1.0  
**Last Updated:** 2026-05-01

---

## 1. Purpose

The Application Lifecycle module manages the full lifecycle of a grant application from initial consideration through submission and outcome recording. It provides the Kanban pipeline view, application workspace, document checklist, approval workflows, and all task management.

---

## 2. Application Pipeline States

An application progresses through the following stages. Transitions are logged in `application_stage_history`.

```
CONSIDERING
    │  Staff decides to pursue
    ▼
IN_PROGRESS  ◄─────────────────────────┐
    │  Writing in progress             │
    ▼                                  │
STAFF_REVIEW                     (Sent back)
    │  Primary staff reviewer signs off│
    ▼                                  │
DIRECTOR_REVIEW ─────────────────────►─┘
    │  ED or Artistic Director approves
    ▼
BOARD_REVIEW  (optional, configurable per grant)
    │  Board member approval (if required)
    ▼
READY_TO_SUBMIT
    │  All approvals obtained; final proofread
    ▼
SUBMITTED
    │  Application submitted to funder
    ▼
UNDER_REVIEW (by funder)
    │
    ├─ AWARDED ────────────────► Post-Award module
    │
    └─ DECLINED
         │
         └─ ARCHIVED
```

**Terminal states:** `AWARDED`, `DECLINED`, `ARCHIVED`, `WITHDRAWN`

---

## 3. Pipeline Views

### 3.1 Kanban View

The primary pipeline view is a Kanban board. Each column represents a stage. Applications are cards that can be dragged between columns.

```
┌─────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│ CONSIDERING │ IN PROGRESS  │ STAFF REVIEW │ DIR. REVIEW  │ READY        │
│─────────────│──────────────│──────────────│──────────────│──────────────│
│ ┌─────────┐ │ ┌─────────┐  │ ┌─────────┐  │ ┌─────────┐  │ ┌─────────┐  │
│ │ NEA Art │ │ │ IL Arts │  │ │ Knight  │  │ │ Mellon  │  │ │ CMA     │  │
│ │ Works   │ │ │ Council │  │ │ Fdn     │  │ │ Fdn     │  │ │ Residency│ │
│ │ Due:    │ │ │ Due:    │  │ │ Due:    │  │ │ Due:    │  │ │ Due:    │  │
│ │ Jan 15  │ │ │ Mar 1   │  │ │ Feb 15  │  │ │ Dec 1   │  │ │ Nov 30  │  │
│ │ ⚠️ 45d  │ │ │ ✓ 72d  │  │ │ ⚠️ 30d │  │ │ 🔴 5d  │  │ │ ✓ Appvd │  │
│ └─────────┘ │ └─────────┘  │ └─────────┘  │ └─────────┘  │ └─────────┘  │
│             │              │              │              │              │
│ + Add       │ + Add        │              │              │              │
└─────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
```

Application cards display:
- Grant name and funder name
- Days until deadline (color-coded: green > 60d, yellow 30–60d, orange 14–30d, red < 14d)
- Assigned staff member avatar
- Current section completion (% bar)
- Tag badges (e.g., "Match Required", "LOI First")

### 3.2 List View

Alternately, all applications are shown in a sortable, filterable table:

Columns: Grant name, Funder, Stage, Assigned to, Deadline, Amount requested, Section completion, Last activity.

Sortable by all columns. Filterable by stage, assigned user, deadline range, funder type.

### 3.3 Calendar View

Applications appear as deadline markers on a monthly calendar view, color-coded by urgency. Clicking a marker opens the application card. Integrates with the Deadlines module (see [Deadlines](#8-deadline-management)).

---

## 4. Creating an Application

Staff can create a new application from:
- Grant database search results ("Start Application" button on any grant record)
- Pipeline view "Add" button (opens grant search modal)
- Discovery queue (when approving a grant)

### 4.1 Application Creation Wizard

**Step 1: Select Grant**
- If coming from a grant record, pre-populated
- Otherwise: search and select from the database
- "Grant not in database?" → inline mini-form to add grant first

**Step 2: Configure Application**
- Requested amount (optionally auto-populated from grant.award_typical)
- Application deadline (auto-populated from grant cycle; editable)
- LOI deadline (if applicable)
- Assigned staff member (default: current user)
- Approvers: Primary reviewer, Director reviewer, Board reviewer (optional)
- Program period (start date, end date)
- Project name (if different from org name for project-based grants)
- Notes

**Step 3: Build Section List**
- Platform suggests sections based on the grant's `required_sections` field
- Staff can add/remove/reorder sections
- Pre-built section templates:
  - Organization Overview (500–750 words)
  - Statement of Need (500–750 words)
  - Project Description (750–1000 words)
  - Goals and Objectives (500 words)
  - Evaluation Plan (500 words)
  - Budget Narrative (750 words)
  - Organizational History (500 words)
  - Artistic Vision (500 words)
  - Community Impact (500 words)
  - Sustainability Plan (500 words)

---

## 5. Application Workspace

The application workspace is the central working area for a single application. It is organized into tabs:

### 5.1 Workspace Tabs

| Tab | Content |
|---|---|
| **Overview** | Summary card, key dates, assigned users, progress summary |
| **Sections** | The AI section editor (see Module 04) |
| **Documents** | Document checklist and file attachments |
| **Tasks** | Task list specific to this application |
| **Comments** | Threaded comment log for the application (not section-level) |
| **Activity** | Full stage history and activity log |
| **Grant Info** | Read-only view of the grant record (funder details, requirements) |

### 5.2 Overview Tab

```
┌──────────────────────────────────────────────────────────────┐
│  Illinois Arts Council — Artists Projects                    │
│  Stage: IN PROGRESS          [Advance to Staff Review →]     │
│                                                              │
│  Application Deadline:  March 1, 2027  (72 days)            │
│  Amount Requested:      $15,000                              │
│  Assigned:              James Chen                           │
│  Reviewers:             Maria Santos (Staff) · ED Approval   │
│                                                              │
│  Section Progress:                                           │
│  ██████████████░░░░░░  5 / 7 sections drafted               │
│                                                              │
│  Document Checklist:   3 / 5 complete                        │
│  Open Tasks:           2 overdue                             │
└──────────────────────────────────────────────────────────────┘
```

---

## 6. Document Checklist

Each application has a document checklist. Items are required or optional based on the grant's `required_attachments` field.

### 6.1 Standard Checklist Items

Automatically added based on grant type:
- IRS Determination Letter
- Most Recent Audited Financials
- Current Year Operating Budget
- Board of Directors List
- List of Current Funders
- Most Recent IRS Form 990
- Staff Organizational Chart

Grant-specific items (from `required_attachments`):
- Grant-specific work samples, resumes, project budgets, letters of support, etc.

### 6.2 Checklist UI

```
Documents Required (3/7 complete)
─────────────────────────────────────────
✓ IRS Determination Letter         [View] [Replace]
✓ 2023 Audited Financials          [View] [Replace]
○ Current Year Budget              [Upload]  ← Required
✓ Board of Directors List          [View] [Replace]
○ 2023 Form 990                    [Upload]  ← Required
○ Project Budget                   [Upload]  ← Required
○ Letter of Support from Partner   [Upload]  Optional
─────────────────────────────────────────
[Add custom document]
```

When uploading, staff can pull from the Document Vault (previously uploaded files) or upload a new file.

---

## 7. Approval Workflow

### 7.1 Stage Transition Controls

Staff can advance or send back applications using the stage transition button in the workspace header. Available transitions depend on current stage and user role.

### 7.2 Approval Notifications

When an application is advanced to a review stage:
- Designated reviewer receives email notification + in-app notification
- Notification includes: grant name, requested amount, deadline, and direct link to workspace
- Board reviewers receive a simplified view of the application (read-only) with approve/decline/comment controls

### 7.3 Approval Actions

**Staff reviewer:**
- Approve → advance to Director Review
- Request changes → send back to In Progress with comment

**Director:**
- Approve → advance to Board Review or Ready to Submit
- Request changes → send back

**Board reviewer:**
- Approve → advance to Ready to Submit
- Decline → send back to Director with comment
- Comment only → add a comment without changing stage

### 7.4 Approval Audit Trail

Every approval action is logged in `application_stage_history` with:
- Actor user ID and name
- Previous stage → new stage
- Timestamp
- Comment (if provided)

The activity tab shows the full audit trail.

---

## 8. Deadline Management

Deadlines are created automatically when an application is created:
- LOI deadline (if LOI required)
- Application deadline
- Reporting deadlines (auto-created when award is entered)

### 8.1 Deadline Types

| Type | Auto-created | Reminders |
|---|---|---|
| LOI | From grant_cycles.loi_deadline | 14d, 7d, 2d before |
| Application | From grant_cycles.application_deadline | 60d, 30d, 14d, 7d, 2d before |
| Board meeting (for approval) | Manual | 7d, 2d before |
| Interim report | From award stewardship plan | 30d, 14d before |
| Final report | From award stewardship plan | 60d, 30d, 14d before |

### 8.2 Deadline Calendar

A dedicated Deadlines page shows all upcoming deadlines across all applications in a unified calendar view. Users can:
- Switch between calendar and list view
- Filter by deadline type, application stage, assignee
- Export to iCal (subscribe URL) or download .ics file

---

## 9. Task Management

Each application has its own task list.

### 9.1 Task Fields

- Title
- Description (optional)
- Assignee (org user)
- Due date
- Priority (high / normal / low)
- Status (open / in-progress / done)

### 9.2 Task Views

Tasks appear:
- In the Tasks tab of the application workspace
- In the cross-application task dashboard (all open tasks across all applications, assignable to self)
- In deadline reminders email if overdue

### 9.3 Auto-Generated Tasks

When an application is created, a default task set is generated:
- [ ] Gather supporting documents (due 4 weeks before deadline)
- [ ] Draft all sections (due 3 weeks before deadline)
- [ ] Internal review (due 2 weeks before deadline)
- [ ] Final proofreading (due 1 week before deadline)
- [ ] Submit application (due date = deadline)

Staff can edit, delete, or add tasks.

---

## 10. Submission Recording

OrchestraGrant does not submit to funders directly (most portals require direct submission). Instead, staff record the submission:

1. Click **[Record Submission]** from READY_TO_SUBMIT stage
2. Modal: Enter submission date, confirmation number (if provided by funder), and submission method (online portal, email, postal)
3. Attach submission confirmation (screenshot or email)
4. Application moves to SUBMITTED stage
5. System logs the event; notifications sent to all org users

---

## 11. Outcome Recording

When a funder notifies of a decision:

1. Click **[Record Outcome]** from SUBMITTED or UNDER_REVIEW stage
2. Select: Awarded / Declined / Withdrawn
3. If Awarded:
   - Enter amount awarded (may differ from requested)
   - Enter grant agreement date
   - Enter program period
   - → Application automatically transitions to the Post-Award module
4. If Declined:
   - Optional: enter decline reason / funder feedback
   - Optional: mark "will reapply" — sets a reminder for the next cycle
5. Application moves to terminal stage

---

*Last Updated: 2026-05-01*
