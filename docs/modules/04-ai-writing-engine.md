# Module 04 — AI Writing Engine

**Project:** OrchestraGrant Platform  
**Version:** 1.0  
**Last Updated:** 2026-05-01

---

## 1. Purpose

The AI Writing Engine is the primary value-differentiating feature of OrchestraGrant. It generates grant-ready narrative sections grounded exclusively in the organization's own documents and data — no hallucinated facts, no generic filler. This module defines the user-facing features of the writing engine: how staff interact with generation, regeneration, emphasis controls, source attribution, compliance checking, and version history.

For the underlying technical architecture, see [AI Engine Design](../ai/ai-engine-design.md).

---

## 2. Section Generation UX

### 2.1 Section Editor Layout

The section editor is a three-panel layout:

```
┌──────────────────┬───────────────────────────┬─────────────────┐
│  SECTIONS        │  EDITOR                   │  AI PANEL       │
│  ─────────────── │  ────────────────────────  │  ───────────────│
│  ✓ Org Overview  │  [Section title]           │  [Generate]     │
│  ✓ Need/Problem  │                            │                 │
│  ◐ Project Desc  │  [Rich text content]       │  Source atoms   │
│  ○ Evaluation    │                            │  used:          │
│  ○ Budget Narr.  │                            │  • 2023 Annual  │
│  ─────────────── │                            │    Report p.4   │
│  Add section +   │                            │  • 2024 990     │
│                  │                            │  • Strategic    │
│                  │                            │    Plan p.12    │
│                  │                            │                 │
│                  │                            │  [Regenerate]   │
│                  │                            │  [Compliance ✓] │
│                  │                            │  [Sources]      │
│                  │                            │  [History]      │
└──────────────────┴───────────────────────────┴─────────────────┘
```

**Left panel:** Section list showing completion status (✓ Complete / ◐ Drafted / ○ Empty). Drag to reorder sections (dnd-kit).

**Center panel:** Tiptap rich text editor. Full formatting controls (bold, italic, lists, headers). Word count and limit displayed at the bottom.

**Right panel:** AI controls, source attribution, compliance, and version history.

### 2.2 Section Status

| Status | Icon | Meaning |
|---|---|---|
| Empty | ○ | No content yet |
| Generating | ⟳ | AI generation in progress |
| Drafted | ◐ | AI content generated, not reviewed |
| In Review | 👁 | Marked for human review |
| Complete | ✓ | Marked complete by staff |

---

## 3. Generate Flow

### 3.1 Triggering Generation

Staff click **[Generate]** in the AI panel. Before generation begins, a modal confirms:

```
┌──────────────────────────────────────────┐
│  Generate: Project Description           │
│                                          │
│  Emphasis                                │
│  ○ Community Impact                      │
│  ○ Artistic Excellence                   │
│  ● Balanced (recommended)                │
│  ○ Education & Youth                     │
│  ○ Innovation & Commissioning            │
│                                          │
│  Tone                                    │
│  ○ Foundation (warm, story-driven)       │
│  ○ Government (formal, factual)          │
│  ● Auto-detect from funder type          │
│                                          │
│  Additional context (optional)           │
│  ┌──────────────────────────────────┐    │
│  │ Focus on the Composer-in-Res     │    │
│  │ program specifically             │    │
│  └──────────────────────────────────┘    │
│                                          │
│  [Cancel]  [Generate →]                  │
└──────────────────────────────────────────┘
```

**Emphasis options** determine which narrative atoms receive higher retrieval weighting:
- Community Impact: weights atoms from community engagement, audience programs, accessibility
- Artistic Excellence: weights atoms about programming quality, guest artists, critical reception
- Education & Youth: weights atoms about education programs, youth audiences, school partnerships
- Innovation & Commissioning: weights atoms about world premieres, commissioned works, new music
- Balanced: no weighting bias; top-ranked atoms by semantic similarity only

**Tone auto-detection** uses the funder's type to select tone (see AI Engine Design, tone routing table).

**Additional context** is injected into the prompt as a user instruction appended to the system prompt.

### 3.2 Generation Progress

While generation runs (typically 15–45 seconds):
- Section shows a shimmer loading state in the editor
- Right panel shows: "Generating… retrieving relevant content"
- WebSocket `section.generation_progress` events update the progress bar

### 3.3 Post-Generation State

When generation completes:
- Text appears in the editor via a streaming effect (word-by-word)
- Section status → Drafted
- Right panel shows:
  - Source atoms used (list with document name and excerpt)
  - Compliance check result (auto-run after generation)
  - Word count vs. limit

---

## 4. Regeneration

Staff can regenerate a section at any time.

**Regenerate with same settings:** One-click regeneration using previously selected emphasis/tone.

**Regenerate with changes:** Opens the same confirmation modal (Section 3.1) pre-populated with prior settings.

**Undo regeneration:** Previous generation is stored in version history (Section 8). Restore with one click.

**Partial regeneration (Phase 3):** Staff can select a paragraph or sentence in the editor and click "Rewrite this" to regenerate just that passage within the existing context.

---

## 5. Source Attribution

The Source Attribution panel shows which narrative atoms were used to generate the current section content.

### 5.1 Atom List

Each used atom is shown as a card:
- Excerpt (first 100 characters of the atom text)
- Source: document name + page/section
- Similarity score (how strongly it matched the generation query)
- Toggle: include/exclude from next regeneration

### 5.2 Inline Attribution Highlights

In the editor, staff can toggle "Show sources" which highlights text in different colors corresponding to which atom it was derived from. Clicking a highlight shows the source atom in the right panel.

This is implemented as a custom Tiptap mark (`SourceAttributionMark`) applied by the AI service as part of the generation response metadata.

---

## 6. Compliance Checker

The compliance checker verifies that a section contains all required elements for the specific grant.

### 6.1 Required Elements

Required elements are extracted from the grant's application instructions by the AI engine when the application is created. Examples:

- "Must include description of target audience"
- "Must state number of performances"
- "Must include total project budget"
- "Must describe partnership with community organization"

### 6.2 Compliance Panel

```
┌──────────────────────────────────────┐
│  Compliance Check — Project Desc     │
│  Overall: 3/5 elements present       │
│  ────────────────────────────────    │
│  ✓ Target audience described         │
│  ✓ Number of performances stated     │
│  ✗ Total project budget missing      │
│    → Consider adding budget summary  │
│  ✓ Community benefit explained       │
│  ✗ Partnership not mentioned         │
│    → "Must reference community org"  │
│                                      │
│  [Run Compliance Check Again]        │
└──────────────────────────────────────┘
```

Missing elements show an inline suggestion for what to add.

### 6.3 Unsupported Claim Detection

A separate check flags any statements in the generated text that cannot be traced back to a source atom or structured data field. Flagged passages are highlighted in orange with tooltip: "Source not found — please verify this statement."

---

## 7. Narrative Atom Library (In-context)

During editing, staff can open the Narrative Atom Library as a right-side drawer. This allows them to:
- Search atoms by keyword or concept
- Drag an atom excerpt directly into the editor as a starting point
- Add atoms to the "Pin" list to force-include them in the next generation

Pinned atoms bypass relevance scoring and are always included in the context window for the next generation of that section.

---

## 8. Version History

Every saved state of a section is stored as a version.

Version history is accessible via the **[History]** button in the right panel.

The history view shows:
- Timestamp
- Who saved / generated
- Word count
- Generation settings (if AI-generated)
- "Restore" button (replaces current content; current content is saved as a new version first)

Up to 50 versions are stored per section. Versions older than 90 days and not marked as milestones are pruned. Users can mark a version as a milestone to preserve it indefinitely.

---

## 9. Collaborative Editing

The section editor supports multiple users viewing the same section simultaneously.

### 9.1 Presence

Active users in the current section are shown as avatars in the editor toolbar. Clicking an avatar highlights their cursor position in the text.

### 9.2 Edit Locking

Only one user can actively edit a section at a time. If a second user attempts to edit:
- Banner: "[Name] is currently editing this section. Click to request edit access."
- Original editor receives a notification: "[Name] is requesting to edit. [Yield] [Continue editing]"
- If original editor is inactive for > 5 minutes, the lock is released automatically.

### 9.3 Comments

Any user with comment permissions can add inline comments on selected text in the editor (Tiptap `Comment` extension). Comments support:
- @mention (notifies mentioned user via email + in-app)
- Reply threads
- Resolve (archived when resolved; can be reopened)

---

## 10. Word Count Management

The editor enforces word limits per section when limits are provided by the grant guidelines.

- **Counter:** Word count displayed live in the bottom bar of the editor
- **Warning:** Yellow when within 10% of limit
- **Over limit:** Red; generate disabled; must trim before submitting
- **Per-paragraph mode:** If guidelines specify limits by section element (e.g., "statement of need: max 250 words"), the section can be divided into labeled sub-fields with individual counters

---

*Last Updated: 2026-05-01*
