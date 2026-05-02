# User Stories

**Project:** OrchestraGrant Platform  
**Version:** 1.0  
**Last Updated:** 2026-05-01

Stories follow the format: *As a [persona], I want to [action] so that [outcome].*  
Priority: **P0** = must-have for phase indicated, **P1** = should-have, **P2** = nice-to-have.

---

## Epic 1 — Onboarding & Organization Profile

| ID | Story | Persona | Priority | Phase |
|---|---|---|---|---|
| US-001 | As an Admin, I want to create an organization account by entering our legal name, EIN, and 501(c)(3) status so that the system knows our basic identity | Admin | P0 | 1 |
| US-002 | As an Admin, I want to complete a guided org profile setup wizard so that I don't have to discover all required fields on my own | Admin | P0 | 1 |
| US-003 | As a Staff user, I want to enter multiple versions of our mission statement (30-word, 100-word, 300-word) so that the AI can select the appropriate length for each grant | Staff | P0 | 1 |
| US-004 | As a Staff user, I want to upload our IRS determination letter and have the system extract our EIN and effective date automatically so that I don't have to enter them manually | Staff | P1 | 1 |
| US-005 | As a Staff user, I want to enter annual operating budget data for the past 5 fiscal years so that grant applications requiring financial history are pre-populated | Staff | P0 | 1 |
| US-006 | As a Staff user, I want to add board member records including name, title, employer, term start, and term end so that board lists can be auto-generated for attachments | Staff | P0 | 1 |
| US-007 | As a Staff user, I want to add staff and artistic leadership bios so that the AI can include them in applications requiring key personnel descriptions | Staff | P0 | 1 |
| US-008 | As a Staff user, I want to define our service area by city, county, state, and zip codes so that the eligibility pre-screener can filter geographically restricted grants | Staff | P0 | 1 |
| US-009 | As a Staff user, I want to see a profile completeness score so that I know what information is missing that might affect AI generation quality | Staff | P1 | 1 |
| US-010 | As an Admin, I want to invite team members by email and assign them a role so that the right people have access to the right features | Admin | P0 | 1 |
| US-011 | As a Staff user, I want to enter our concert season history (programs, venues, attendance, ticket prices) by season so that applications can reference historical programming data | Staff | P0 | 1 |
| US-012 | As a Staff user, I want to enter our educational and community programs with participant counts, dates, and descriptions so that education-focused grants have rich source material | Staff | P0 | 1 |
| US-013 | As a Staff user, I want to enter our DEI statement and supporting demographic data so that applications requiring equity information are pre-populated | Staff | P1 | 1 |
| US-014 | As a Board Member, I want to view the org profile in read-only mode so that I can verify the accuracy of information before applications are submitted | Board | P1 | 1 |

---

## Epic 2 — Document Vault

| ID | Story | Persona | Priority | Phase |
|---|---|---|---|---|
| US-020 | As a Staff user, I want to upload documents and tag them by type (990, audit, budget, application, media, etc.) so that they can be automatically attached to relevant applications | Staff | P0 | 1 |
| US-021 | As a Staff user, I want to upload prior grant applications (PDF or Word) and have the system parse them into reusable sections so that I don't have to re-enter past content | Staff | P0 | 1 |
| US-022 | As a Staff user, I want to upload our annual IRS Form 990s by year so that applications requiring 990s can link to the correct fiscal year automatically | Staff | P0 | 1 |
| US-023 | As a Staff user, I want to preview any uploaded PDF or image without downloading it so that I can quickly verify file contents | Staff | P1 | 1 |
| US-024 | As a Staff user, I want documents to be versioned so that I can access and restore a prior version of any file | Staff | P1 | 1 |
| US-025 | As a Staff user, I want to search documents by keyword, tag, and date range so that I can quickly locate a specific file | Staff | P0 | 1 |
| US-026 | As a Staff user, I want to link a document to one or more grant applications so that I can track which documents were submitted with each application | Staff | P1 | 1 |
| US-027 | As a Staff user, I want to see how much storage we have used versus our quota so that we don't unexpectedly run out of space | Staff | P1 | 1 |

---

## Epic 3 — Grant Database

| ID | Story | Persona | Priority | Phase |
|---|---|---|---|---|
| US-030 | As a Staff user, I want to browse the grant database filtered by funder type, grant type, amount range, and geographic eligibility so that I can identify the best candidates for us | Staff | P0 | 1 |
| US-031 | As a Staff user, I want to view a full grant record including all eligibility requirements, application requirements, deadlines, and funder intelligence so that I have everything I need without going to the funder's website | Staff | P0 | 1 |
| US-032 | As a Staff user, I want to see when a grant's guidelines were last verified so that I know if the information might be stale | Staff | P0 | 1 |
| US-033 | As a Staff user, I want to add a grant to our pipeline directly from its database record so that discovery and pipeline management are connected | Staff | P0 | 1 |
| US-034 | As a Staff user, I want to manually add a new grant record that is not yet in the database so that we can manage grants we discover on our own | Staff | P0 | 1 |
| US-035 | As a Staff user, I want to view the application history for each grant (years we applied, amounts requested, outcomes) so that I can track our relationship with each funder over time | Staff | P0 | 1 |
| US-036 | As a Staff user, I want to see a list of required attachments for each grant so that I know in advance what documents to prepare | Staff | P0 | 1 |
| US-037 | As a Staff user, I want to view a funder's full profile including their giving history, current priorities, and program officers so that I can tailor our application appropriately | Staff | P1 | 2 |
| US-038 | As a Staff user, I want to save grants to a watchlist so that I can monitor them without immediately starting an application | Staff | P1 | 1 |
| US-039 | As an Admin, I want to flag a grant record as needing verification so that the team knows to double-check its accuracy before applying | Admin | P1 | 1 |

---

## Epic 4 — Grant Discovery

| ID | Story | Persona | Priority | Phase |
|---|---|---|---|---|
| US-040 | As a Staff user, I want to receive a notification when a new grant is discovered that matches our eligibility profile so that I never miss an opportunity | Staff | P0 | 2 |
| US-041 | As a Staff user, I want to receive an alert when a grant in our watchlist or pipeline changes its guidelines or deadline so that I can update our application accordingly | Staff | P0 | 2 |
| US-042 | As a Staff user, I want to review a queue of newly discovered grants and mark each as relevant, not relevant, or save for later so that the database stays curated | Staff | P0 | 2 |
| US-043 | As an Admin, I want to configure which federal and state grant programs the scraper monitors so that discovery is focused on our geography and mission | Admin | P1 | 2 |
| US-044 | As a Staff user, I want to see a relevance score for each discovered grant so that I can prioritize my review time | Staff | P1 | 2 |
| US-045 | As a Staff user, I want to see an explanation of why a grant was flagged as relevant or ineligible so that I can judge whether the automated assessment is correct | Staff | P1 | 2 |
| US-046 | As an Admin, I want to receive an alert when a previously active grant has had no new cycle for 18 months so that I can investigate whether it has ended | Admin | P2 | 2 |

---

## Epic 5 — Application Pipeline Management

| ID | Story | Persona | Priority | Phase |
|---|---|---|---|---|
| US-050 | As a Staff user, I want to see all active applications in a Kanban view organized by pipeline stage so that I can assess our workload at a glance | Staff | P0 | 1 |
| US-051 | As a Staff user, I want to see all applications in a sortable list view with deadline, amount, status, and assignee columns so that I can find specific applications quickly | Staff | P0 | 1 |
| US-052 | As a Staff user, I want to open an application workspace that contains all drafts, documents, notes, and tasks in one place so that I don't have to look in multiple systems | Staff | P0 | 1 |
| US-053 | As a Staff user, I want to move an application to the next pipeline stage by clicking a button and confirming so that stage transitions are intentional and recorded | Staff | P0 | 1 |
| US-054 | As a Staff user, I want to create tasks within an application workspace with an assignee and due date so that the team knows exactly what work remains | Staff | P0 | 1 |
| US-055 | As an ED, I want to see a document checklist for each application that is automatically populated from the grant's requirements so that I don't miss required attachments | ED | P0 | 1 |
| US-056 | As a Staff user, I want to add comments to an application that are visible to all team members so that we can discuss it without leaving the platform | Staff | P0 | 1 |
| US-057 | As a Board Member, I want to receive an email notification when an application is ready for my review so that I don't have to check the platform proactively | Board | P0 | 1 |
| US-058 | As a Board Member, I want to approve or request changes on an application from within the platform so that my sign-off is recorded | Board | P0 | 1 |
| US-059 | As a Staff user, I want to record the submission confirmation number and date after submitting an application so that we have proof of timely submission | Staff | P0 | 1 |
| US-060 | As an ED, I want to record the outcome of an application (awarded amount, declined, waitlisted) so that our win/loss data is accurate | ED | P0 | 1 |
| US-061 | As a Staff user, I want to see the total dollar value of all applications currently in our pipeline so that I can project potential revenue | Staff | P1 | 1 |

---

## Epic 6 — Deadline Management

| ID | Story | Persona | Priority | Phase |
|---|---|---|---|---|
| US-070 | As a Staff user, I want to see a calendar view of all upcoming LOI deadlines, application deadlines, and reporting deadlines so that I can plan my work schedule | Staff | P0 | 1 |
| US-071 | As a Staff user, I want to receive automated email reminders at 30, 14, 7, and 2 days before each deadline so that I never miss a submission | Staff | P0 | 1 |
| US-072 | As an Admin, I want to configure which reminder intervals are active and which email addresses receive them so that alerts go to the right people | Admin | P1 | 1 |
| US-073 | As a Staff user, I want to export the deadline calendar to an iCal file so that I can import it into Google Calendar or Outlook | Staff | P1 | 1 |
| US-074 | As a Staff user, I want reporting deadlines for awarded grants to be automatically created based on the grant agreement terms so that I don't have to enter them manually | Staff | P0 | 1 |
| US-075 | As an ED, I want to see all deadlines in the next 30 days on my home dashboard so that urgent items are immediately visible | ED | P0 | 1 |

---

## Epic 7 — AI Writing Engine

| ID | Story | Persona | Priority | Phase |
|---|---|---|---|---|
| US-080 | As a Staff user, I want to select a target grant and click "Generate Application" to receive a complete first draft of all required narrative sections so that application drafting starts from a strong baseline | Staff | P0 | 1 |
| US-081 | As a Staff user, I want each generated section to be within the funder's specified word or character limit so that I don't have to manually cut content | Staff | P0 | 1 |
| US-082 | As a Staff user, I want to edit generated text inline with a rich text editor so that I can refine the AI output without switching tools | Staff | P0 | 1 |
| US-083 | As a Staff user, I want to click "Regenerate" on any section to get an alternative draft with a different angle or emphasis so that I'm not locked into the first output | Staff | P0 | 1 |
| US-084 | As a Staff user, I want the AI to highlight which source document each generated paragraph was derived from so that I can verify accuracy | Staff | P1 | 3 |
| US-085 | As a Staff user, I want to run a compliance check that tells me if any of the funder's required narrative elements are missing from our draft so that I don't submit an incomplete application | Staff | P0 | 3 |
| US-086 | As a Staff user, I want to see a readability score for each section so that I know if the writing level is appropriate for the audience | Staff | P1 | 3 |
| US-087 | As a Staff user, I want the system to flag claims in the draft that are not supported by any uploaded source document so that I can add evidence before submitting | Staff | P1 | 3 |
| US-088 | As a Staff user, I want to browse the narrative atom library and manually insert specific paragraphs into a draft so that I can leverage strong writing from prior applications | Staff | P1 | 3 |
| US-089 | As a Staff user, I want to specify a project or program focus when generating an application so that the AI writes about the right activities | Staff | P0 | 1 |
| US-090 | As a Staff user, I want to see a side-by-side view of the grant guidelines and the application draft so that I can verify alignment without switching tabs | Staff | P1 | 3 |
| US-091 | As a Staff user, I want version history on each application draft so that I can compare and restore prior versions | Staff | P0 | 1 |
| US-092 | As an ED, I want the AI to adjust its emphasis when generating for a community foundation (community impact) vs. an arts endowment (artistic excellence) vs. a corporate funder (economic impact) automatically so that our applications resonate with each funder's priorities | ED | P0 | 3 |

---

## Epic 8 — Post-Award Compliance

| ID | Story | Persona | Priority | Phase |
|---|---|---|---|---|
| US-100 | As a Staff user, I want to upload the grant agreement after an award and have the system extract the award amount, grant period, reporting dates, and special conditions so that compliance tracking is automated | Staff | P0 | 5 |
| US-101 | As a Staff user, I want to log expenditures against specific budget line items in an active grant so that I can track how much of the award has been spent | Staff | P0 | 5 |
| US-102 | As a Staff user, I want to fill out an impact data collection form that captures attendance, participants served, and program outcomes so that reporting has accurate data | Staff | P0 | 5 |
| US-103 | As a Staff user, I want to click "Generate Report" for an active grant and receive a pre-populated first draft of the interim or final report based on tracked data so that reporting is as fast as application drafting | Staff | P0 | 5 |
| US-104 | As a Staff user, I want to see a warning when a reporting deadline is approaching (30, 14, 7 days) so that I don't miss it | Staff | P0 | 5 |
| US-105 | As an ED, I want to see a ledger of all active grants, their award amounts, amounts spent to date, and remaining balance so that I understand our grant fund position at any time | ED | P1 | 5 |
| US-106 | As a Staff user, I want to log funder stewardship activities (thank you letter sent, program officer invited to performance, update sent) so that our relationship history is documented | Staff | P1 | 5 |

---

## Epic 9 — Analytics & Strategy

| ID | Story | Persona | Priority | Phase |
|---|---|---|---|---|
| US-110 | As an ED, I want to see a dashboard summary of our grant program: applications submitted YTD, total awarded YTD, win rate, and pipeline value so that I can report to the board quickly | ED | P0 | 4 |
| US-111 | As a Staff user, I want to see our win rate broken down by funder type, grant type, and amount range so that I can focus our effort on the highest-yield categories | Staff | P1 | 4 |
| US-112 | As an ED, I want to see a chart of our funder concentration so that I can identify over-reliance on any single funder | ED | P1 | 4 |
| US-113 | As an ED, I want to see a projected grant revenue forecast for the next 12 months based on our pipeline and historical win rates so that I can budget with more confidence | ED | P1 | 4 |
| US-114 | As a Staff user, I want to see a list of grant categories we have not applied for this year that we qualify for so that we can identify strategic gaps in our portfolio | Staff | P1 | 4 |
| US-115 | As an ED, I want to compare our grant revenue composition to peer orchestras of similar size so that I can benchmark our development program | ED | P2 | 4 |

---

## Epic 10 — Knowledge Base

| ID | Story | Persona | Priority | Phase |
|---|---|---|---|---|
| US-120 | As a Staff user, I want to access a grant writing style guide with best practices for performing arts applications so that I can improve the quality of my edits to AI drafts | Staff | P1 | 1 |
| US-121 | As a Staff user, I want to read funder-specific guidance notes (e.g., "NEA reviewers look for clear community benefit statements") so that I can tailor applications more precisely | Staff | P1 | 2 |
| US-122 | As a new development coordinator, I want access to onboarding training content explaining the grant writing process so that I can get up to speed quickly | Staff | P2 | 1 |
| US-123 | As a Staff user, I want to search the knowledge base for a specific topic (e.g., "how to write an evaluation plan") and receive curated guidance so that help is always available | Staff | P1 | 1 |

---

*Last Updated: 2026-05-01*
