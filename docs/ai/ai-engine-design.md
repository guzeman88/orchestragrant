# AI Engine Design

**Project:** OrchestraGrant Platform  
**Version:** 1.0  
**Last Updated:** 2026-05-01

---

## 1. Overview

The AI Engine is the core intelligence layer of OrchestraGrant. It performs three primary functions:

1. **Document Intelligence** — Parse, extract, and semantically index all organizational documents
2. **Narrative Generation** — Produce publication-quality grant application sections grounded in organizational truth
3. **Quality Assurance** — Verify generated content against grant requirements and flag issues

All AI generation is built on Retrieval-Augmented Generation (RAG): every claim in a generated output must be traceable to a source document. The system does not generate facts — it retrieves and synthesizes them.

---

## 2. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                      DOCUMENT INGESTION                          │
│                                                                  │
│  Upload → Parse (LlamaParse) → Clean → Chunk → Embed → Store   │
│               (pdfplumber fallback)      (OpenAI)  (pgvector)   │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      NARRATIVE ATOM LIBRARY                      │
│                                                                  │
│  pgvector table: narrative_atoms                                 │
│  - Source document reference                                     │
│  - Section type classification                                   │
│  - Text content (512 token chunks, 64 token overlap)            │
│  - 3072-dim embedding vector                                     │
│  - Metadata: fiscal year, funder, grant type context            │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    RAG GENERATION PIPELINE                       │
│                                                                  │
│  1. Receive generation request (grant_id, section_key, prefs)   │
│  2. Build retrieval query from section intent                    │
│  3. Semantic search → top-k atoms                               │
│  4. Structured data fetch (financials, programs, board)         │
│  5. Construct prompt with context + constraints                  │
│  6. LLM call (GPT-4o) → structured JSON output                  │
│  7. Compliance check against grant requirements                  │
│  8. Store draft + version + source citations                     │
│  9. Return to client                                             │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    QUALITY ASSURANCE LAYER                       │
│                                                                  │
│  - Compliance checker (required elements coverage)              │
│  - Word/character limit enforcement                              │
│  - Source attribution (which atom → which paragraph)            │
│  - Unsupported claim detection                                   │
│  - Readability scoring                                           │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Document Ingestion Pipeline

### 3.1 Supported File Types

| Type | Parser | Notes |
|---|---|---|
| PDF (digital/born-digital) | LlamaParse (primary) | Best results for complex layouts |
| PDF (scanned) | LlamaParse with OCR | Slower; flag low-confidence output |
| DOCX / DOC | python-docx | Direct XML extraction |
| TXT | Direct read | No parsing needed |
| XLSX | openpyxl | Extracts financial data as structured JSON, not prose |

### 3.2 Chunking Strategy

Grant applications have distinct narrative sections. The chunking strategy respects this structure:

**Step 1: Structural chunking (preferred)**
- For parsed PDFs and Word docs with headings: split at heading boundaries
- Each section becomes one or more atoms
- Preserve the section title as metadata

**Step 2: Sentence-boundary chunking (fallback)**
- For unstructured text: use `spacy` sentence tokenizer
- Target chunk size: 400–600 tokens
- Overlap: 64 tokens between adjacent chunks (ensures context continuity)

**Step 3: Section type classification**
- Each chunk is classified by section type using a zero-shot LLM classifier
- Section types: `org_history`, `project_description`, `community_need`, `evaluation_plan`, `budget_narrative`, `dei_statement`, `biographical`, `acknowledgements`, `other`
- This classification drives retrieval targeting

### 3.3 Embedding Generation

```python
# Pseudocode for embedding pipeline
async def embed_document_chunks(chunks: list[TextChunk], org_id: str):
    embeddings = await openai.embeddings.create(
        model="text-embedding-3-large",
        input=[chunk.content for chunk in chunks],
        dimensions=3072
    )
    
    atoms = [
        NarrativeAtom(
            org_id=org_id,
            document_id=chunk.document_id,
            source_type=chunk.source_type,
            section_type=chunk.classified_section_type,
            content=chunk.content,
            word_count=len(chunk.content.split()),
            chunk_index=i,
            embedding=embeddings.data[i].embedding,
            metadata=chunk.metadata
        )
        for i, chunk in enumerate(chunks)
    ]
    
    await db.bulk_insert(NarrativeAtom, atoms)
```

**Batch size:** 100 chunks per OpenAI API call (rate limit safe)  
**Retry:** Exponential backoff with jitter; max 3 retries  
**Error handling:** Failed chunks are logged; document status updated to `partial_index` if > 20% fail

---

## 4. RAG Generation Pipeline

### 4.1 Retrieval

For each grant section to be generated, the system constructs a targeted retrieval query:

```python
SECTION_RETRIEVAL_QUERIES = {
    "org_history": "organizational history founding mission growth milestones",
    "project_description": "project program description activities timeline",
    "community_need": "community need problem statement gap audience served",
    "evaluation_plan": "evaluation plan outcomes metrics measurement success",
    "budget_narrative": "budget expenses costs financial breakdown",
    "dei_statement": "diversity equity inclusion demographics representation",
    "biographical": "artistic director conductor staff biography credentials",
}

async def retrieve_atoms(
    org_id: str,
    section_key: str,
    grant_description: str,
    top_k: int = 8
) -> list[NarrativeAtom]:
    # Combine section intent with grant-specific context
    query = f"{SECTION_RETRIEVAL_QUERIES[section_key]} {grant_description}"
    
    query_embedding = await embed_text(query)
    
    atoms = await db.execute("""
        SELECT *, 1 - (embedding <=> $1) AS similarity
        FROM narrative_atoms
        WHERE org_id = $2
        ORDER BY embedding <=> $1
        LIMIT $3
    """, query_embedding, org_id, top_k)
    
    return atoms
```

**Retrieval parameters:**
- `top_k = 8` for standard sections
- `top_k = 4` for short sections (under 200 words)
- Minimum similarity threshold: 0.72 (cosine similarity)
- If fewer than 2 atoms meet threshold: flag section as low-confidence

### 4.2 Structured Data Injection

In addition to retrieved narrative atoms, each generation call receives structured data directly from the database:

```python
async def build_structured_context(org_id: str, grant: Grant) -> dict:
    return {
        "org": await get_org_profile(org_id),
        "financials": await get_latest_financials(org_id, years=3),
        "board": await get_active_board_members(org_id),
        "staff": await get_staff_members(org_id),
        "recent_season": await get_most_recent_season(org_id),
        "programs": await get_programs(org_id),
        "grant_history": await get_application_history(org_id, grant.funder_id),
    }
```

### 4.3 Prompt Construction

Each section uses a structured prompt template. The prompt has four parts:

**Part 1: System Prompt (role + funder tone)**
```
You are a professional grant writer specializing in performing arts organizations.
You are writing a grant application for {org_name}, a per-service orchestra based in {city}.

FUNDER CONTEXT:
- Funder: {funder_name} ({funder_type})
- Funder priorities: {funder_priorities}
- Tone guidance: {tone_instructions}

CRITICAL RULES:
- Every factual claim must be derived from the provided context documents.
- Do not invent statistics, attendance figures, dates, or program names.
- If context is insufficient to make a claim, omit it or indicate "to be completed."
- Write in the third person about the organization.
- Never use the phrases "world-class," "unique," or "innovative" without evidence.
```

**Part 2: Grant Requirements**
```
SECTION REQUIREMENTS:
- Section: {section_name}
- Required elements: {required_elements_list}
- Word limit: {word_limit} (strict maximum)
- Character limit: {char_limit}
- Special instructions: {funder_specific_guidance}
```

**Part 3: Context**
```
RETRIEVED CONTEXT FROM PRIOR APPLICATIONS AND ORG DOCUMENTS:
[Atom 1 — source: 2024 NEA application, section: org_history]
{atom_1_content}

[Atom 2 — source: org_profile, section: mission]
{atom_2_content}
...

STRUCTURED ORG DATA:
- Annual operating budget (FY2025): $420,000
- Annual attendance: 8,500
- Participants served through education programs: 3,200
- Board size: 14 members
- Ensemble size: 35-55 musicians (per-service)
- Founded: 2005
```

**Part 4: Output Instructions**
```
Generate the {section_name} section.

Return a JSON object with this exact shape:
{
  "content": "<the generated section text>",
  "word_count": <integer>,
  "source_citations": [
    { "atom_id": "<uuid>", "paragraph_index": <int>, "excerpt": "<first 20 words of paragraph>" }
  ],
  "confidence": "high" | "medium" | "low",
  "confidence_reason": "<brief explanation if not high>"
}
```

### 4.4 Tone Routing

Funder type determines the emphasis weight applied to the prompt:

| Funder Type | Primary Emphasis | Secondary Emphasis |
|---|---|---|
| Federal (NEA, NEH) | Artistic merit + broad public benefit | Accessibility + education |
| State arts council | Geographic community impact | Organizational stability |
| Private foundation (arts) | Artistic excellence + vision | Community + education |
| Community foundation | Community need + local impact | Diversity + reach |
| Corporate | Economic impact + community visibility | Education + brand alignment |
| Education funder | Learning outcomes + curriculum | Access + youth |
| DEI-focused funder | Equity + representation | Community + access |

Tone routing is encoded in the system prompt as "emphasis weight" instructions.

### 4.5 LLM API Integration

```python
class LLMClient:
    """
    Abstraction layer over multiple LLM providers with retry,
    fallback, rate limiting, and cost tracking.
    """
    
    PRIMARY_MODEL = "gpt-4o"
    FALLBACK_MODEL = "claude-3-5-sonnet-20241022"
    
    async def generate(
        self,
        messages: list[Message],
        response_schema: dict,
        max_tokens: int = 4096,
        temperature: float = 0.4,   # Low for factual accuracy
    ) -> GenerationResult:
        
        for provider in [self._call_openai, self._call_anthropic]:
            try:
                result = await provider(messages, response_schema, max_tokens, temperature)
                await self._log_usage(result)
                return result
            except RateLimitError:
                await self._wait_for_rate_limit_reset()
                continue
            except ProviderError as e:
                logger.warning(f"Provider error, trying fallback: {e}")
                continue
        
        raise AllProvidersFailedError("All LLM providers exhausted")
```

**Temperature:** 0.4 for narrative generation (controlled creativity, factual grounding)  
**Temperature for compliance check:** 0.0 (deterministic)  
**Max tokens:** 4096 per section (sufficient for the longest grant sections)  
**Structured output:** OpenAI JSON mode / Anthropic tool_use to enforce output schema

---

## 5. Compliance Checker

The compliance checker verifies that generated content addresses all required elements from the grant record.

### 5.1 Required Elements Schema

Each grant record stores `required_sections` as structured JSON:

```json
[
  {
    "section_key": "org_history",
    "section_name": "Organizational History",
    "required_elements": [
      "founding year and founding mission",
      "growth and development narrative",
      "key achievements or milestones",
      "current programming scope"
    ],
    "word_limit": 400,
    "required": true
  }
]
```

### 5.2 Compliance Check Process

```python
async def check_compliance(
    content: str,
    required_elements: list[str],
    section_name: str
) -> ComplianceResult:
    
    prompt = f"""
    You are auditing a grant application section for compliance with funder requirements.
    
    SECTION: {section_name}
    
    REQUIRED ELEMENTS (the application MUST address all of these):
    {json.dumps(required_elements, indent=2)}
    
    APPLICATION CONTENT:
    {content}
    
    For each required element, determine: present | partial | missing
    Return a JSON object with this exact shape:
    {{
        "compliance_score": <0-100 integer>,
        "elements": [
            {{
                "element": "<element text>",
                "status": "present" | "partial" | "missing",
                "evidence": "<quoted excerpt from content that addresses this element, or null>",
                "suggestion": "<brief suggestion if partial or missing>"
            }}
        ],
        "overall_assessment": "<one sentence summary>"
    }}
    """
    
    result = await llm_client.generate(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    
    return ComplianceResult(**result)
```

**Compliance score bands:**
- 90–100: Ready to submit
- 75–89: Minor gaps, review recommended
- 50–74: Significant gaps, revision required
- < 50: Major revision required

---

## 6. Unsupported Claim Detection

After generation, a secondary pass detects claims that lack supporting source material:

```python
CLAIM_PATTERNS = [
    r"\d+[\,\.]?\d*\s*(people|participants|students|audience|attendees)",
    r"\$[\d\,]+",
    r"(founded|established|created)\s+in\s+\d{4}",
    r"\d+\s+(years|seasons|concerts|performances)",
    r"\d+\s*(percent|%)",
]

async def detect_unsupported_claims(
    content: str,
    structured_context: dict,
    atom_sources: list[NarrativeAtom]
) -> list[UnsupportedClaim]:
    # Extract all factual claims from content matching patterns
    claims = extract_claims(content, CLAIM_PATTERNS)
    
    unsupported = []
    for claim in claims:
        # Check if claim value matches any structured data field
        if not is_in_structured_data(claim, structured_context):
            # Check if claim is in any retrieved atom
            if not is_in_atoms(claim, atom_sources):
                unsupported.append(UnsupportedClaim(
                    text=claim.text,
                    position=claim.position,
                    severity="warning"
                ))
    
    return unsupported
```

---

## 7. Budget Narrative Generation

Budget narrative is handled differently from prose sections — it's tightly coupled to actual financial data:

1. Fetch grant budget template from grant record (line item structure)
2. Fetch org's current-year operating budget from `org_financials`
3. Generate project-specific budget if project grant (user provides project budget in application workspace)
4. Generate budget narrative:
   - For each budget line, write a 2–3 sentence justification
   - Reference the dollar amount and how it relates to the project/org mission
   - Note any matching funds or in-kind contributions

---

## 8. Report Generation

Post-award report generation follows the same RAG pattern but with different source material:

**Source material for reports:**
- Award impact data records (`award_impact_data` table)
- Expenditure log (`award_expenditures`)
- Funder's reporting template (from grant record)
- Original application sections (for consistency of framing)
- Season/program data from the grant period

**Report types:**
- Interim report: covers activities to date, spending to date, adjusted outlook
- Final report: comprehensive outcomes, full financial accounting, lessons learned, continuation plans

---

## 9. Model Cost Management

All LLM calls are logged with token counts. Cost tracking per organization per month:

| Operation | Estimated Tokens | Estimated Cost |
|---|---|---|
| Single section generation | ~3,000 input + ~800 output | ~$0.05 |
| Full application (8 sections) | ~24,000 input + ~6,400 output | ~$0.40 |
| Compliance check (per section) | ~1,500 input + ~400 output | ~$0.02 |
| Report generation | ~4,000 input + ~1,200 output | ~$0.07 |

Cost soft cap per org per month: $50 (configurable by subscription tier)  
Alert at 80% of cap; block new generation jobs at 100% until next billing cycle.

---

## 10. Evaluation & Quality Monitoring

### 10.1 Automated Evaluation (offline, weekly)

- Sample 5% of all generated sections
- Run GPT-4o judge evaluation:
  - Factual consistency score (vs. source atoms): 0–10
  - Funder requirement coverage: 0–10
  - Writing quality: 0–10
  - Hallucination detection: boolean
- Alert engineering if mean scores drop below thresholds

### 10.2 User Feedback Loop

- Users can rate any generated section (1–5 stars) with optional comment
- Rating stored in `generation_jobs.output_meta`
- Weekly report: average rating per section type, per funder type
- Sections with < 3 stars trigger prompt engineering review

### 10.3 A/B Prompt Testing

- System supports prompt variant flags per `generation_job`
- New prompt versions deployed to 10% of traffic
- Statistical significance test on quality scores before full rollout

---

*Last Updated: 2026-05-01*
