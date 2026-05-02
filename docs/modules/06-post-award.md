# Module 06 — Post-Award Management

**Project:** OrchestraGrant Platform  
**Version:** 1.0  
**Last Updated:** 2026-05-01

---

## 1. Purpose

Winning the grant is not the finish line. Post-award management — compliant expenditure tracking, impact data collection, report writing, stewardship, and relationship maintenance — is where small orchestras most often struggle. This module ensures that every awarded grant is managed to completion and that all reporting obligations are met on time.

---

## 2. Award Workspace

When an application is recorded as Awarded (see Module 05, Section 11), the system automatically creates an Award record and opens an Award Workspace.

### 2.1 Award Workspace Layout

The Award Workspace has tabs parallel to the Application Workspace:

| Tab | Content |
|---|---|
| **Overview** | Award summary, key dates, budget status, compliance status |
| **Expenditures** | Budget ledger and expense log |
| **Impact Data** | Audience metrics, program data, outcome tracking |
| **Reports** | Report drafts, submission history |
| **Stewardship** | Contact log, relationship notes, stewardship tasks |
| **Documents** | Grant agreement, signed docs, correspondence |
| **Activity** | Full audit trail |

### 2.2 Award Overview

```
┌──────────────────────────────────────────────────────────────┐
│  Knight Foundation — Arts Engagement Grant                   │
│  Award Period:  July 1, 2026 – June 30, 2027                 │
│                                                              │
│  Amount Awarded:    $45,000                                  │
│  Amount Spent:      $18,750   (42% of award)                 │
│  Budget Status:     On track                                 │
│                                                              │
│  Grant Period:      ████████████░░░░░░░░░  58% elapsed       │
│                                                              │
│  Reporting:                                                  │
│  ○ Interim Report    Due: Jan 15, 2027  (45 days away)       │
│  ○ Final Report      Due: Aug 31, 2027                       │
│                                                              │
│  Stewardship:                                                │
│  Last contact: Nov 5, 2026 (Email to Sarah Chen, PO)         │
│  Next contact: Jan 5, 2027 (before interim report)           │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Grant Agreement Management

When an award is created, staff upload the grant agreement document.

### 3.1 Agreement Parsing

The platform uses LlamaParse to extract key terms from the agreement:
- Grant amount
- Reporting deadlines (triggers auto-creation of deadline records)
- Budget restrictions (allowable cost categories, indirect cost caps)
- Program period
- Matching requirements
- Special conditions (e.g., "prior written approval required for budget modifications > 10%")

Extracted terms are displayed for staff review and confirmation before being saved.

### 3.2 Agreement Storage

Agreements are stored in S3 and linked to the award record. Signing workflow (DocuSign / Adobe Sign integration, Phase 4) allows in-platform signature routing for agreements that require it.

---

## 4. Expenditure Tracking

### 4.1 Budget Ledger

The budget ledger shows the grant budget structure against actual spending.

For each budget line item:
- Category (personnel, fringe benefits, fees/services, supplies, travel, indirect, other)
- Budgeted amount
- Amount spent (from expense entries)
- Remaining balance
- % of line item used
- Variance flag if overspent or > 25% variance from typical burn rate

### 4.2 Expense Entry

Staff log expenses against the grant:

**Manual Entry:**
```
Add Expense
─────────────────
Date:            [Nov 15, 2026    ]
Category:        [Personnel ▾     ]
Description:     [Conductor fee - 
                  Fall Concert     ]
Amount:          [$2,500           ]
Budget Line:     [Artistic Fees ▾ ]
Documentation:   [Upload receipt  ]
Notes:           [                ]
```

**QuickBooks/Xero Sync (Phase 5):** Transactions tagged to the grant's cost center in the accounting system can be imported automatically.

### 4.3 Budget Modification Tracking

When budget modifications are necessary, staff create a budget amendment:
- Enter revised amounts per line item
- Note the reason
- Attach funder approval documentation (if required)
- Amendment is versioned; original budget preserved

---

## 5. Impact Data Collection

Grant reports require outcome and impact data that must be collected throughout the grant period, not scrambled for at report time.

### 5.1 Impact Data Fields

The platform pre-loads a standard impact data schema based on the grant type:

**For orchestral performance grants:**
- Total number of performances (actual vs. planned)
- Total paid attendance
- Total free/subsidized attendance
- Geographic reach (zip codes represented)
- Economic impact (if tracked)

**For education grants:**
- Number of school partnerships
- Number of student participants
- Number of teachers engaged
- Grade levels served
- Number of classroom visits / workshops
- Number of schools in Title I designation

**For community engagement grants:**
- Number of free events
- Number of underserved community participants
- Number of community partnerships
- Income-qualifying participant %

**Custom fields:** Staff can add custom impact metrics specific to the grant's requirements.

### 5.2 Data Entry

Impact data is entered through structured forms at any point during the grant period. Data can be:
- Entered manually
- Imported from CSV (concert-by-concert data)
- Pulled from linked programs in the Org Intelligence Hub

A completeness indicator shows what data is still missing for upcoming reports.

---

## 6. Report Generation

### 6.1 Report Types

| Report Type | Description | AI Assistance |
|---|---|---|
| Interim Report | Mid-grant progress report | Full AI draft with impact data + expenditure summary |
| Final Report | End-of-grant comprehensive report | Full AI draft |
| Budget Report | Financial accounting of grant expenditures | Structured data output (no AI narrative needed) |
| Custom Report | Funder-requested non-standard report | AI draft with custom template |

### 6.2 Report Generation Flow

1. Staff navigate to the Reports tab and click **[Generate Report]**
2. Select report type
3. The platform auto-populates:
   - Impact data from the Impact Data tab
   - Expenditure summary from the Budget Ledger
   - Narrative from AI generation (using original application narrative as anchor, updated with impact data)
4. Staff review and edit in the full section editor (same interface as application writing)
5. Staff export to PDF or DOCX for submission

### 6.3 AI Report Generation

The report generation prompt includes:
- Original application sections (for narrative continuity)
- All impact data collected
- Expenditure summary vs. budget
- Any lessons learned / challenges noted in activity log
- Funder's report instructions (from grant record)

Output is structured to match the funder's report format requirements.

---

## 7. Multi-Grant Budget Ledger

The organization-level Awards dashboard provides a consolidated view across all active awards:

```
Active Awards — FY2026-27

Grant                Funder           Amount    Spent    Remaining   % Used
─────────────────────────────────────────────────────────────────────────────
Arts Engagement      Knight Fdn       $45,000   $18,750  $26,250     42%
General Support      IL Arts Council  $10,000   $3,200   $6,800      32%
Chamber Music Res.   CMA              $8,500    $8,500   $0          100% ✓
NEA Art Works        NEA              $22,000   $12,100  $9,900      55%
─────────────────────────────────────────────────────────────────────────────
TOTAL                                 $85,500   $42,550  $42,950     50%
```

Clicking any row opens the Award Workspace. Filtering by fiscal year, funder type, and status.

---

## 8. Stewardship Log

Grant stewardship — relationship maintenance with program officers — is tracked in the Stewardship Log.

### 8.1 Contact Log

Each contact entry:
- Date
- Contact person (linked to funder_contacts)
- Method (email, phone, in-person, site visit)
- Direction (outgoing / incoming)
- Summary (free text, 1–3 sentences)
- Follow-up required: yes/no; if yes, follow-up date

### 8.2 Stewardship Plan

An AI-generated stewardship plan is created with each award:
- Thank-you letter: due within 2 weeks of award notification
- Award acknowledgment: acknowledge on website/newsletter within 30 days
- Mid-grant update email to program officer: 1 month before interim report
- End-of-year update: if grant spans multiple FYs
- Report cover letter: personalized to program officer

The stewardship plan creates task items in the task manager automatically.

### 8.3 Stewardship Analytics

Per-funder stewardship history:
- All contact log entries across all years
- Applications submitted
- Awards received (total amount)
- Reports submitted (all on time? late?)
- Relationship strength score (composite of contact frequency, success rate, report timeliness)

---

## 9. Reporting Deadline Auto-Creation

When an award is created and the grant agreement is parsed:
1. All reporting deadlines from the agreement are extracted
2. Created as `deadlines` records of type `reporting`
3. Linked to the award record
4. Reminders scheduled per the standard deadline reminder cadence (30d, 14d, 7d before)

If no agreement is parsed (manual award entry), staff manually enter reporting deadlines.

---

*Last Updated: 2026-05-01*
