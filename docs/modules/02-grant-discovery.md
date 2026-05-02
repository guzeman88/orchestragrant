# Module 02 — Grant Discovery

**Project:** OrchestraGrant Platform  
**Version:** 1.0  
**Last Updated:** 2026-05-01

---

## 1. Purpose

The Grant Discovery module is the user-facing layer of the automated grant discovery pipeline. While the pipeline backend runs continuously in the background (see [Grant Discovery Pipeline](../ai/grant-discovery-pipeline.md)), this module defines how staff interact with discovery results: reviewing new grants, managing their watchlist, configuring alert preferences, and maintaining the eligibility profile that drives pre-screening.

---

## 2. Discovery Queue

The Discovery Queue is the staff inbox for newly found grant opportunities. Every grant discovered by the automated pipeline (scrapers, Grants.gov, Candid) that passes the relevance classifier lands in this queue for human review before entering the main grant database.

### 2.1 Queue View

The queue is presented as a card list, sorted by relevance score descending:

```
┌────────────────────────────────────────────────────┐
│  New Grants Requiring Review (14)                  │
│  ─────────────────────────────────────────────────  │
│  [Filter: All Types ▾] [Sort: Relevance ▾]         │
│                                                    │
│  ┌─────────────────────────────────────────┐       │
│  │ ● New   Art Works — National Endowment  │  ⭐92 │
│  │         for the Arts                    │       │
│  │   Project grants · $10K–$100K           │       │
│  │   Deadline: Jan 15, 2027                │       │
│  │   Why: "orchestral music" + geography   │       │
│  │   [View Details] [Add to Database] [✗]  │       │
│  └─────────────────────────────────────────┘       │
│                                                    │
│  ┌─────────────────────────────────────────┐       │
│  │ ● New   Illinois Arts Council —         │  ⭐87 │
│  │         Artists Projects                │       │
│  │   Project grant · Up to $15,000         │       │
│  │   Deadline: Mar 1, 2027                 │       │
│  │   Why: "Illinois" + "performing arts"   │       │
│  │   [View Details] [Add to Database] [✗]  │       │
│  └─────────────────────────────────────────┘       │
│  ...                                               │
└────────────────────────────────────────────────────┘
```

Each card shows:
- Discovery status (New, Changed, Re-verified)
- Grant name and funder
- Grant type, award range
- Application deadline
- Why flagged (key matching terms)
- Relevance score (0–100)
- Action buttons: **View Details**, **Add to Database**, **Dismiss**

### 2.2 Discovery Detail View

Clicking "View Details" opens a side panel:

- Full scraped description from the funder website
- Archived guidelines PDF (if successfully scraped)
- Eligibility pre-screen results table:
  - ✓ Geography: Illinois — matches
  - ✓ Org type: 501(c)(3) — matches
  - ✓ Budget range: $300K — within acceptable range
  - ✗ LOI required: Unknown (not found in guidelines)
- Proposed field values (pre-populated from scraper):
  - Funder, name, deadline, award range, grant type, guidelines URL
- Editable fields: staff can correct any pre-populated values before adding

### 2.3 Review Actions

| Action | Result |
|---|---|
| **Add to Database** | Creates a grant record in DRAFT status with pre-populated fields; removes from queue |
| **Dismiss** | Moves to "Dismissed" filter; notated as "not relevant"; not shown again unless re-scraped with materially new information |
| **Defer** | Moves to "Deferred" filter; re-surfaces in 30 days |
| **Request More Info** | Flags for platform database team to do manual research; adds to admin queue |

---

## 3. Grant Change Alerts

When the Discovery Pipeline detects a material change to a grant the org is watching or has in their pipeline, a change alert is generated.

### 3.1 Change Alert View

The change queue is a sub-tab of the Discovery Queue:

Each alert shows:
- Grant name and funder
- Type of change detected: **Deadline Changed**, **Award Amount Changed**, **Guidelines Updated**, **New Cycle Opened**, **Program Discontinued**
- Old value → New value (where applicable)
- LLM-generated change summary (1–2 sentences)
- Links: View grant record, View application (if any)

### 3.2 Change Alert Actions

| Action | Result |
|---|---|
| **Acknowledge** | Marks change as reviewed; updates grant record |
| **Update Application** | Opens related application workspace to make updates based on the change |
| **Remove from Watchlist** | If the change makes the grant no longer relevant |
| **Mark Discontinued** | Sets grant status to `discontinued`; closes related open applications |

---

## 4. Watchlist Management

The Watchlist is a user-curated list of grants they want to monitor closely. Any grant in the watchlist triggers alerts for changes, new cycles opening, and deadlines.

### 4.1 Adding to Watchlist

Any grant in the database can be added to the watchlist by clicking the ⭐ icon in search results or on the grant detail page.

When adding, optionally configure:
- Alert frequency for this grant (immediate / daily digest / weekly digest)
- Note (free text) — e.g., "Check with NEA program officer in October before applying"

### 4.2 Watchlist View

Organized by status:
- **Monitoring** — Actively watched, no active application
- **Applied** — Org currently has an application in progress for this grant
- **Tracking** — Past applicant, monitoring for future cycles

Columns: Grant name, Funder, Typical deadline, Last cycle status, Last application outcome, Next action date.

---

## 5. Eligibility Profile

The Eligibility Profile is the structured set of org characteristics used by the pre-screener to filter discovery results. It is maintained separately from the org's full narrative profile because it uses structured values that can be compared programmatically against grant eligibility criteria.

### 5.1 Eligibility Fields

```typescript
interface EligibilityProfile {
  // Geography
  states: string[];                // ["IL"] — states org operates in
  cities: string[];                // ["Chicago", "Evanston"]
  us_based: boolean;
  
  // Org type
  org_types: OrgType[];            // ["nonprofit_501c3"]
  is_fiscally_sponsored: boolean;
  fiscal_sponsor_name?: string;
  
  // Financial
  annual_budget: number;           // most recent FY total budget
  has_endowment: boolean;
  endowment_value?: number;
  
  // Activities
  mission_tags: MissionTag[];      // ["orchestral_music", "education", "community_engagement"]
  activity_tags: ActivityTag[];    // ["concerts", "youth_education", "free_programming"]
  
  // Membership
  league_member: boolean;          // League of American Orchestras
  afm_signatory: boolean;          // American Federation of Musicians
  
  // Other
  accepts_us_only_applications: boolean;
  years_in_operation: number;
}
```

### 5.2 Eligibility Profile UI

The eligibility profile is edited via a dedicated settings page with toggle groups, multi-selects, and number inputs. Changes take effect immediately on pre-screening results.

A "Test pre-screener" button lets staff paste a grant description and see the eligibility check output.

---

## 6. Discovery Alert Preferences

Each user can configure how they receive discovery notifications:

| Alert Type | Options |
|---|---|
| New high-relevance grant (score ≥ 80) | In-app, email immediate |
| New discovery queue items | In-app, email daily digest |
| Material change to watchlist grant | In-app, email immediate |
| Material change to pipeline grant | In-app, email immediate |
| New cycle opened for watchlist grant | In-app, email immediate |
| Dead grant detected (watchlist) | In-app, email immediate |

Default: admin and staff users receive all alerts via in-app notifications; email is opt-in.

Board member and read-only roles receive no discovery alerts by default.

---

## 7. Discovery Statistics Dashboard

A summary panel on the Discovery module home page:

- Grants discovered this month: N
- Grants added to database this month: N
- Grants dismissed this month: N
- Average relevance score of accepted grants: N
- Last scraper run: timestamp + status (success / partial / failed)
- Top sources this month (bar chart): NEA, State Arts Councils, Foundations, etc.

---

*Last Updated: 2026-05-01*
