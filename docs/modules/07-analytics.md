# Module 07 — Analytics & Reporting

**Project:** OrchestraGrant Platform  
**Version:** 1.0  
**Last Updated:** 2026-05-01

---

## 1. Purpose

The Analytics module transforms the organization's grant data into actionable intelligence. It answers the questions every ED and Development Director needs to answer: Are we winning at the right rate? Are we diversified? Where is revenue trending? What are we leaving on the table?

---

## 2. Dashboard — Primary KPIs

The main analytics dashboard loads on login for admin and staff users. It shows the most important metrics at a glance.

### 2.1 KPI Cards (Top Row)

| KPI | Description | Time Period |
|---|---|---|
| Active Applications | Count of applications in non-terminal stages | Current |
| Total Requested (Pipeline) | Sum of requested amounts in active pipeline | Current |
| Total Awarded (YTD) | Sum of awarded amounts in current fiscal year | YTD |
| Win Rate | Awarded / (Awarded + Declined) | Rolling 12 months |
| Active Awards | Count of awards currently in grant period | Current |
| Upcoming Deadlines | Count of deadlines in next 30 days | Next 30 days |

### 2.2 Revenue Trend Chart

Line chart: Total granted revenue by fiscal year for last 5 fiscal years + current year (projected based on pipeline).

Series:
- Actual awarded (prior years)
- Projected awarded (current year, based on pipeline with probability weights)
- Budget target (from org financial profile, if entered)

---

## 3. Win Rate Analytics

### 3.1 Overall Win Rate

Simple calculation:
```
Win Rate = Awards / (Awards + Declines)
```

Displayed as a gauge (0–100%) with color bands:
- < 25%: red (industry average for competitive grants)
- 25–40%: yellow (average)
- > 40%: green (strong)

Context note: "Industry average for competitive grants is 20–30%."

### 3.2 Win Rate Breakdown

Win rate segmented by:

**By funder type:**
| Funder Type | Applications | Awards | Win Rate |
|---|---|---|---|
| Federal | 8 | 3 | 37.5% |
| State | 12 | 7 | 58.3% |
| Foundation | 22 | 6 | 27.3% |
| Community Foundation | 4 | 2 | 50.0% |

**By grant type:**
| Grant Type | Applications | Awards | Win Rate |
|---|---|---|---|
| General Operating | 15 | 8 | 53.3% |
| Project | 25 | 9 | 36.0% |
| Education | 6 | 1 | 16.7% |

**By amount requested range:**

**By year applied:**

Clicking any row expands to show the individual applications in that segment.

### 3.3 Streak Tracking

Displayed on funder detail page:
- Current streak: "3 consecutive awards from IL Arts Council"
- Win/loss history (last 5 cycles): colored dots (green = awarded, red = declined, gray = N/A)

---

## 4. Revenue Forecasting

### 4.1 Pipeline-Weighted Forecast

The revenue forecast applies probability weights to applications in the pipeline:

| Stage | Default Probability Weight |
|---|---|
| CONSIDERING | 15% |
| IN_PROGRESS | 25% |
| STAFF_REVIEW | 40% |
| DIRECTOR_REVIEW | 50% |
| BOARD_REVIEW | 60% |
| READY_TO_SUBMIT | 75% |
| SUBMITTED | Org's historical win rate for this funder type |
| UNDER_REVIEW | Org's historical win rate for this funder type |

Staff can override the probability weight for individual applications if they have funder intelligence suggesting higher/lower likelihood.

### 4.2 Forecast Scenarios

Three scenarios displayed:
- **Conservative:** 50th percentile of weighted amounts
- **Expected:** Probability-weighted sum
- **Optimistic:** 75th percentile assuming above-average win rate

### 4.3 Monthly Cash Flow Projection

Bar chart showing expected grant revenue by month for the next 12 months, based on:
- Award amounts from active awards (when payments are typically disbursed)
- Probability-weighted amounts from the pipeline (at expected submission + decision dates)

---

## 5. Funder Concentration Analysis

### 5.1 Revenue by Funder

Pie chart + table: grant revenue by funder, last 3 fiscal years.

Identifies over-reliance: if any single funder represents > 30% of grant revenue, display a concentration risk warning.

### 5.2 Funder Relationship Matrix

Table showing the org's relationship with each funder they've worked with:

| Funder | First Applied | Times Applied | Awards | Total Awarded | Last Award |
|---|---|---|---|---|---|
| IL Arts Council | 2018 | 8 | 6 | $72,500 | 2025 |
| Knight Foundation | 2020 | 3 | 1 | $45,000 | 2024 |
| NEA | 2019 | 5 | 2 | $46,000 | 2023 |

### 5.3 Diversification Recommendations

AI-generated text recommendation:
> "Your grant revenue is currently concentrated in 2 funders (IL Arts Council + NEA = 68% of last year's grant revenue). Based on your profile and the grant database, there are 14 foundations you've never applied to that fund orchestras with your budget profile. Consider expanding your application pipeline to include [list of top 5 recommendations]."

---

## 6. Application ROI Analysis

Each application represents a staff investment. ROI analysis helps staff prioritize future applications.

### 6.1 ROI Calculation

```
Application ROI = (Award Amount - Staff Time Cost) / Staff Time Cost
```

Staff time cost is estimated based on:
- Hours logged in task management (Phase 3 feature when time-tracking is added)
- Until then: estimated from section word count × configurable "minutes per word" setting (default: 5 min/100 words)

### 6.2 ROI Table

| Grant | Requested | Awarded | Est. Hours | Est. Cost | ROI |
|---|---|---|---|---|---|
| NEA Art Works | $50,000 | $22,000 | 40h | $1,600 | 13.75x |
| IL Arts Council | $15,000 | $10,000 | 15h | $600 | 15.67x |
| Foundation X | $30,000 | $0 | 35h | $1,400 | -100% |

High ROI funders are candidates for expanded applications. Low ROI funders are candidates for review.

---

## 7. Peer Benchmarking

### 7.1 Data Source

990 data from Candid API for comparable orchestras:
- NTEE code A69 (Symphony Orchestras & Chamber Music)
- Budget range: 50%–200% of org's budget
- Same primary state

### 7.2 Benchmarking Metrics

| Metric | Your Org | Peer Average | Top Quartile |
|---|---|---|---|
| Grant revenue % of total budget | 38% | 32% | 48% |
| Grant revenue per FTE | $45K | $38K | $62K |
| Total funders (last 3 years) | 12 | 9 | 18 |
| Win rate | 41% | 29% | 52% |
| Average award size | $18,200 | $14,500 | $25,000 |

Disclaimer: "Benchmarks derived from publicly available IRS 990 data. Comparable organizations are selected by NTEE code and budget range."

---

## 8. Gap Analysis

The gap analysis identifies grant opportunities the org is eligible for but has never applied to.

### 8.1 Gap Analysis Report

Compares:
- All grants in the database where org is eligible (pre-screened)
- Applications in org's history

Gaps = eligible grants with no application history.

Sorted by:
- Grant amount (largest first)
- Relevance score
- Ease of application (estimated hours based on section requirements)

### 8.2 Gap Analysis Output

```
Untapped Eligible Grants (27 grants, ~$1.2M total available)

High Priority Gaps:
1. NEA Challenge America ($10K) — Applied by 94% of similar orchestras; 
   you've never applied. Low effort (1 section, < 1,000 words).
2. Doris Duke Charitable Foundation Arts ($100K) — Eligible based on 
   profile; 0 applications in your history.
3. American Music Center Project Grant ($25K) — Good fit for your 
   commissioning work.
```

---

## 9. Analytics Export

All charts and tables can be exported:
- CSV / Excel for tables
- PNG / SVG for charts
- PDF for the full dashboard (board report format)

The board report PDF export includes:
- Pipeline summary
- YTD awarded vs. budget target
- Win rate
- Active awards status
- Upcoming deadlines

Designed to be shared directly with the board at development committee meetings.

---

*Last Updated: 2026-05-01*
