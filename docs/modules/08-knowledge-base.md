# Module 08 — Knowledge Base

**Project:** OrchestraGrant Platform  
**Version:** 1.0  
**Last Updated:** 2026-05-01

---

## 1. Purpose

The Knowledge Base is the platform's internal library of grant writing guidance, funder-specific intelligence, style guidelines, and reference materials. It serves three audiences:
1. **Staff** using OrchestraGrant day-to-day, needing quick answers and writing guidance
2. **New staff members** onboarding to grant writing for the first time
3. **The AI engine**, which uses knowledge base articles as additional context for generation

---

## 2. Knowledge Base Structure

The Knowledge Base is organized into four sections:

```
Knowledge Base
├── Grant Writing Guide
│   ├── Grant Writing Fundamentals
│   ├── Section-by-Section Guides
│   ├── Writing for Different Funder Types
│   └── Common Mistakes & How to Avoid Them
├── Funder Intelligence
│   ├── NEA
│   ├── State Arts Councils
│   ├── Foundations
│   └── [per-funder articles]
├── Style Guide
│   ├── Voice & Tone
│   ├── Terminology Standards
│   ├── Data Citation Standards
│   └── Formatting Requirements
└── Reference Library
    ├── Grant Writing Glossary
    ├── Funding Landscape Overview
    └── Per-Service Orchestra Context
```

---

## 3. Grant Writing Guide

### 3.1 Grant Writing Fundamentals

Platform-authored articles covering:

**The Logic Model Approach**
Explains how funders think: Inputs → Activities → Outputs → Outcomes → Impact. Every grant section should map to this framework. Article includes template logic model for a small orchestra.

**Understanding What Funders Want**
- Specificity over generality
- Quantified claims over qualitative assertions
- Community impact emphasis
- Organizational capacity signals

**The Statement of Need**
Full guide to writing a compelling statement of need:
- Leading with the community's need, not the organization's need
- Using local and national data effectively
- Connecting the need to the org's unique position to address it
- Example before/after passages

**The Project Description**
- SMART goals framework
- Describing what will happen, not what usually happens
- Connecting program activities to outcomes
- Avoiding jargon

**Budget Narratives**
- What funders look for in a budget narrative
- Explaining each line item without repetition
- Cost-sharing and matching language
- Indirect cost explanations

**Evaluation Plans**
- Types of evaluation (process / outcome / impact)
- Appropriate metrics for small orchestras
- Third-party evaluation language

**Organizational History Sections**
- What to include and what to omit
- Using financial health signals strategically
- Board composition as a strength signal

### 3.2 Writing for Different Funder Types

A guide for each major funder category:

**Federal Grantmakers (NEA, NEH, IMLS)**
- Formal tone requirements
- CFDA compliance language
- Federal eligibility documentation
- Matching requirement language
- Civil rights assurance requirements
- How to read an NEA peer review rubric

**State Arts Councils**
- Geographic emphasis requirements
- In-state partnership expectations
- Service area documentation
- State-specific programs overview

**Private Foundations**
- Relationship-first culture
- LOI best practices
- Cover letter strategy
- When and how to call program officers

**Community Foundations**
- Local impact emphasis
- Geographic specificity
- Community partnership documentation

---

## 4. Funder Intelligence Notes

Each major funder in the database can have linked Knowledge Base articles with staff-curated intelligence. These are distinct from the structured funder profile fields — these are narrative notes, tips, and institutional memory.

### 4.1 Funder Note Structure

Each funder note article:
- Author and date (for currency assessment)
- Note type tag: Application Tips, Program Officer Notes, Panel Notes, Relationship History, Evaluation Criteria
- Body (rich text, markdown)
- Visibility: team-wide or personal (staff can maintain private notes)

### 4.2 Example: NEA Art Works Intelligence Note

```
NEA Art Works — Application Tips
Last updated: James Chen, October 2025

**Panel review structure**
Art Works panels are peer review panels of 3–5 artists and arts 
administrators. They score applications on:
- Artistic excellence (40%)
- Artistic merit of the organization (30%)
- Access (30%)

Access criteria weight has increased significantly in the last 
2 grant cycles. Emphasize free and reduced-price programming, 
accessibility accommodations, and geographic reach.

**What works for us**
Our best-performing narrative themes:
- Emphasis on per-service model enabling local musician employment
- Free summer concert series (mention specific attendance #s)
- Education partnerships with Title I schools

**What to avoid**
- Do not describe the music director's biography in excessive detail
- Avoid quoting press reviews unless from national publications
- Budget: NEA panels flag indirect rates > 20% — keep ours at 15%

**Our history**
Applied 5 times; awarded 2. Declined in 2021 (panel notes 
suggested stronger evaluation plan needed) and 2022 (budget 
narrative lacked sufficient detail on per-project costing).
```

---

## 5. Style Guide

The Style Guide defines how the organization presents itself in writing. The AI writing engine is trained to follow these guidelines.

### 5.1 Voice & Tone

**Our voice is:**
- Confident but not boastful
- Specific and evidence-based
- Community-centered
- Mission-driven

**Our voice is not:**
- Jargon-heavy
- Deficit-framing (describing communities as "lacking" rather than as having assets)
- Self-congratulatory
- Vague or aspirational without specifics

### 5.2 Preferred Terminology

| Preferred | Avoid |
|---|---|
| "musicians" | "players" (for formal grant writing) |
| "per-service orchestra" | "part-time orchestra" |
| "concert season" | "year" |
| "audience members" | "attendees" |
| "community partners" | "partners" (too vague) |
| "underserved communities" | "poor communities" |
| "free concerts" | "complimentary performances" |
| Our legal name (for first reference) | Shortened name in formal sections |

### 5.3 Data Citation Standards

All quantitative claims in grant applications must be cited. Citation formats:

- **Internal data:** "(Our records, FY2024-25)"
- **Survey data:** "(Audience survey, Spring 2025, n=342)"
- **External data:** Full source with year "(National Endowment for the Arts, 2024 Survey of Public Participation in the Arts)"
- **Economic impact:** Specify methodology source "(Americans for the Arts Arts & Economic Prosperity 6, 2023)"

### 5.4 Numbers and Figures

- Spell out numbers one through ten; use numerals for 11 and above
- Always use numerals for dollar amounts: "$10,000" not "ten thousand dollars"
- Use commas in numbers ≥ 1,000
- Use the em dash (—) not the hyphen-dash (--)
- Fiscal year format: "FY2024-25" not "FY2025" or "fiscal year 2024-2025"

---

## 6. Grant Writing Glossary

A searchable glossary of terms used in grant writing. Platform-authored, 80+ terms at launch:

| Term | Definition |
|---|---|
| 501(c)(3) | IRS designation for a tax-exempt nonprofit organization |
| CFDA Number | Catalog of Federal Domestic Assistance number; identifies federal grant programs |
| Cost-sharing | The portion of a project's costs borne by the applicant rather than the funder |
| DUNS Number | (Now replaced by UEI) Unique entity identifier for federal grant applicants |
| General Operating Support (GOS) | Grant funding unrestricted to a specific project; supports operations broadly |
| Indirect Costs | Overhead costs not directly attributed to a project (rent, utilities, admin) |
| LOI | Letter of Intent or Letter of Inquiry; a brief document submitted before a full application |
| Match | Required amount the applicant contributes; may be cash or in-kind |
| NTEE Code | National Taxonomy of Exempt Entities code; classifies nonprofit purpose |
| Per-Service | Refers to musicians hired for individual events rather than on salary |
| Program Officer | The funder's staff member responsible for managing a grant program |
| RFP | Request for Proposals; a funder's call for applications |
| SAM.gov | System for Award Management; required registration for federal grant applicants |
| UEI | Unique Entity Identifier; replaced DUNS for federal grants in 2022 |

---

## 7. Onboarding Flow

New staff members are guided through a structured onboarding track within the Knowledge Base.

### 7.1 Onboarding Checklist

```
Getting Started with OrchestraGrant (6 steps)

✓ 1. Watch: Platform overview (8 min video)
○ 2. Read: Grant writing fundamentals (30 min)
○ 3. Read: How the AI writing engine works (15 min)
○ 4. Tutorial: Your first application (interactive, 45 min)
○ 5. Read: Your organization's style guide
○ 6. Read: Your top 5 active funders' intelligence notes
```

### 7.2 Role-Specific Onboarding Paths

**Staff / Grant Writer:**
- Full onboarding (all 6 steps)
- Read all module docs (sections 3–7)
- Shadow an existing application draft with a senior staff member

**Executive Director:**
- Overview (step 1)
- Analytics & Reporting module overview
- Approval workflow tutorial

**Board Member:**
- Board portal orientation (15-minute video)
- How to review and approve applications

---

## 8. Knowledge Base Search

The Knowledge Base is full-text searchable. Search covers:
- Article titles and body text
- Funder intelligence notes (team-visible only; not personal notes)
- Glossary terms

Results ranked by:
1. Exact title match
2. Term frequency in article body
3. Article recency

Knowledge Base articles are not indexed into the narrative atom embedding system (they are guidance for humans, not evidence for grant applications).

---

## 9. Knowledge Base Contributions

Team members can contribute to the Knowledge Base:

- **Create article:** Any staff member can draft an article; admin publishes after review
- **Edit article:** Staff can suggest edits; changes tracked with author and date
- **Rate article:** Thumbs up/down + optional comment; low-rated articles flagged for review
- **Request article:** Staff can request a topic; assigned to the knowledge base curator role

The platform team maintains the Grant Writing Guide section. Org staff own the Funder Intelligence section.

---

*Last Updated: 2026-05-01*
