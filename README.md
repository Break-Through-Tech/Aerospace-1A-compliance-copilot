# Compliance Copilot: Auditing Software Requirements Against Engineering Standards

---

### 👥 **Team Members**

| Name             | GitHub Handle       | Contribution                                              |
|------------------|----------------------|-------------------------------------------------------------|
| See GitHub handle | @Binayak012          | Access Data — NASA NPR 7150.2D / SWEHB 5.09 corpus extraction |
| See GitHub handle | @Gabriel-Lopezz      | Access Data, Data Triage, Documentation                     |
| See GitHub handle | @sum09fairSaif       | Access Data, Data Triage                                    |
| See GitHub handle | @ycheng4-design      | Access Data, Documentation                                  |
| See GitHub handle | @0205prakriti        | Data Triage, Documentation                                  |
| See GitHub handle | @essey1              | Data Triage                                                 |
| See GitHub handle | @hemadharshinii-s    | Documentation                                                |

---

## 🎯 **Project Highlights**

This sprint (Weeks 1–2: **Access Data** + **Data Triage**) built the data foundation the Compliance Copilot will run on. No AI/ML model has been trained yet — that begins with the **Baseline Model** milestone in October (see [Next Steps](#-next-steps)). What was actually built and documented this sprint:

- Extracted a **structured, machine-readable corpus** of NASA compliance guidance: 34 clauses from **NPR 7150.2D Chapter 4** (§4.1–4.6) and 24 guidance concepts from **SWEHB 5.09** (Software Requirements Specification handbook), via a deterministic, re-runnable HTML-parsing script (`src/corpus/extract_npr_clauses.py`).
- Ran a **content-fidelity QA pass** verifying all 34 + 24 rows against the live NASA source pages, with zero discrepancies found (`data/npr7150_clauses_QA.md`) — verdict: ready for downstream use.
- Performed a **manual, requirement-by-requirement review** of a 54-requirement synthetic Software Requirements Specification (the Starhawk Mission Computer SRS), labeling each requirement **ACCEPTABLE** (35) or **NEEDS REVIEW** (19) against SWEHB 5.09's requirement-quality criteria (`docs/manual_requirement_review.csv`).
- Generalized the 19 NEEDS REVIEW findings into a **5-category requirement-quality taxonomy** — Undefined Term, Unquantified Performance Criterion, Unverifiable Behavior, Compound Requirement, Missing Numerical Bound — each with a definition, NASA basis, and detection questions (`docs/requirement_quality_taxonomy.md`).
- Produced **6 fully worked requirement rewrites** spanning all 5 taxonomy categories, following a strict no-fabrication rule: any missing number or definition is left as an explicit `[... TBD by stakeholder]` placeholder rather than invented (`docs/requirement_rewrites.md`).
- Wrote an **AI-review brainstorm** reasoning through what a future LLM-based requirement reviewer would need as input/output, grounded entirely in what the manual review actually found — not a hypothetical (`docs/ai_review_brainstorm.md`) — plus an early **tool-calling agent design** sketch for the November milestone (`docs/architecture/future_agent_design.md`).

---

## 👩🏽‍💻 **Setup and Installation**

1. **Clone the repository:**
   ```bash
   git clone <this-repo-url>
   cd Aerospace-1A-compliance-copilot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   (`pandas`, `requests`, `beautifulsoup4`, `lxml`)

3. **(Optional) Regenerate the corpus CSVs:**
   ```bash
   python3 src/corpus/extract_npr_clauses.py
   ```
   The `data/` folder already contains the pre-generated, QA-checked outputs (`npr7150_clauses.csv`, `swehb_5_09_guidance.csv`), so this step is not required to use the data — it exists purely for reproducibility, so anyone can regenerate the corpus from the live NASA source pages and confirm it matches. The script is idempotent and falls back to embedded reference data if the NASA sites are unreachable.

No model training or inference steps exist yet this sprint — there is no notebook or script to "run the model."

---

## 🏗️ **Project Overview**

This project is part of **Break Through Tech AI Studio**, Fall 2026, Aerospace track. Our host problem: in safety-critical software engineering — NASA space missions, medical devices, financial infrastructure — every software requirement must be manually audited, clause-by-clause, against strict compliance standards (e.g., NASA NPR 7150.2) before code can be written. Today this relies on a small pool of senior domain experts, creating a real operational bottleneck.

The long-term goal (per `Challenge-Project-Overview.md`) is an AI-powered **Compliance Copilot** that reads software requirements, retrieves relevant clauses from an engineering standard, judges whether each requirement satisfies that standard, and produces a structured, citation-grounded audit report — evolving from a non-agentic RAG pipeline (October) to a tool-calling LLM agent (November).

**This sprint's scope** was narrower and foundational: **Access Data** (Week 1) and **Data Triage** (Week 2). We did not build or benchmark any model. We built the structured NASA-guidance corpus the future pipeline will retrieve from, and we manually performed the kind of requirement review the future model will need to automate — both to understand the problem deeply and to leave behind a human-labeled reference the model's output can later be checked against.

---

## 📊 **Data Exploration**

**NASA guidance corpus** (`data/npr7150_clauses.csv`, `data/swehb_5_09_guidance.csv`):
- 34 NPR 7150.2D clauses, Chapter 4 only, spanning §4.1 (6 clauses) through §4.6 (5 clauses): §4.1→6, §4.2→2, §4.3→1, §4.4→7, §4.5→13, §4.6→5.
- 24 SWEHB 5.09 guidance concepts, spanning categories: characteristic (9), structure (5), management (5), safety (2), quality-attribute (1), interface (1), performance (1).
- Both were extracted from NASA's live HTML pages (NODIS for NPR, Confluence for SWEHB) using a deterministic parser, then independently spot-checked line-by-line against the live pages — 34/34 and 24/24 rows confirmed accurate (`data/npr7150_clauses_QA.md`).

**Key finding — NPR §4.1 is PROCESS-level, SWEHB 5.09 is where INDIVIDUAL-level citations come from.** We classified every corpus row by what it can actually be checked against (`docs/nasa_guidance_analysis.csv`, INDIVIDUAL / SET / PROCESS / MULTIPLE). Nearly all of NPR 7150.2D §4.1's clauses (e.g., SWE-050, SWE-051, SWE-053, SWE-054, SWE-055) are **PROCESS**: directives that the *project manager* run an activity (elicit, analyze, validate) across the whole requirement set — not something checkable by reading a single requirement sentence. By contrast, SWEHB 5.09's per-sentence characteristics (Specific, Testable, Measurable, Complete, Traceable, Performance Metric Guidance) are **INDIVIDUAL** — directly checkable against one requirement at a time. This was confirmed empirically, not assumed: of the 19 NEEDS REVIEW findings from our manual review (below), **zero cite an NPR 7150.2 clause** and every one cites an SWEHB 5.09 characteristic.

**Example SRS** (`data/Starhawk Mission Computer SRS.md`): a fictional Starhawk Mission Computer SRS containing 54 numbered requirements (`SFMC-REQ-001` – `SFMC-REQ-054`) across Navigation, Propulsion, Targeting/Weapons, Defensive, Communications, and Vehicle Health subsystems, plus an Emergency Operation, Performance, Reliability, Data, Security, and Constraints sections. A first-read pass produced raw observations before any grading (`docs/initial_srs_observations.md`); per-requirement applicable-clause filtering for all 54 requirements is in `data/srs_clause_triage.csv`.

---

## 🧠 **Model Development**

**No ML model has been built this sprint.** Per `Challenge-Project-Overview.md`'s milestone table, the first model ("start with rules, keywords, TF-IDF, etc. — no LLM yet") is the **Baseline Model** milestone (GitHub issue #2), planned for the following sprint and not yet started as of this documentation. A **Benchmark** milestone (issue #4), where the Challenge Advisor provides a seeded ground-truth benchmark with an accompanying Data Card, is also separate, not-yet-started work.

What this sprint did instead, in place of model development, was a **manual simulation of the review task** the future model will automate — see Results & Key Findings below — so that the taxonomy, schema, and evaluation approach the model will need are already grounded in real, human-reviewed examples rather than designed in the abstract.

---

## 📈 **Results & Key Findings**

Manual review of all 54 Starhawk SFMC requirements (`docs/manual_requirement_review.csv`):

| Assessment | Count |
|---|---|
| ACCEPTABLE | 35 |
| NEEDS REVIEW | 19 |
| **Total** | **54** |

The 19 NEEDS REVIEW requirements fall into exactly 5 recurring problem types (`docs/requirement_quality_taxonomy.md`):

| # | Category | Count |
|---|---|---|
| 1 | Undefined Term | 11 |
| 2 | Unquantified Performance Criterion | 4 |
| 3 | Unverifiable Behavior | 2 |
| 4 | Compound Requirement | 1 |
| 5 | Missing Numerical Bound | 1 |
| | **Total** | **19** |

Every NEEDS REVIEW finding cites a specific SWEHB 5.09 clause (never an NPR §4.1 PROCESS clause — see Data Exploration), matching the project's eventual success criterion that model verdicts must cite a specific, valid standard clause ID.

Six of the 19 requirements were also fully rewritten (`docs/requirement_rewrites.md`), spanning all 5 taxonomy categories. Where the actual fix requires a real engineering number or definition that no one has supplied (e.g., a targeting-accuracy threshold, an encryption standard), the rewrite leaves an explicit `[... TBD by stakeholder]` placeholder rather than inventing a value — the one exception is the Compound Requirement rewrite, which needed only a structural split, not a new fact.

These are **not model performance metrics** — there is no model yet. They are the human-labeled reference this sprint produced, which a future model's output can be checked against once the Baseline Model (issue #2) exists.

---

## 🚀 **Next Steps**

Per `Challenge-Project-Overview.md`'s milestone table:

- **September (remainder of sprint):** **Benchmark** — the Challenge Advisor provides a seeded ground-truth benchmark of requirement/clause pairs with `Meets` / `Partial` / `Gap` verdicts and an accompanying Data Card; **Baseline Model** — build a first model using rules, keywords, and TF-IDF (no LLM yet), and document its output, performance, and findings.
- **October:** Non-Agentic RAG Baseline & Schema Enforcement — build an in-memory vector index (FAISS/Chroma), implement deterministic retrieval with Pydantic-enforced JSON citations and verdicts, and evaluate initial precision/recall.
- **November:** Tool-Calling Agent & Automated Reporting — wrap the pipeline in an LLM agent with dedicated tools (`retrieve_clause`, `check_requirement`, `log_gap`) and generate full JSON/Markdown gap reports. An early design for this agent — tool schemas, a groundedness-gated retry loop, and the exact taxonomy/schema reused from this sprint's manual review — is already sketched in `docs/architecture/future_agent_design.md`, but no runtime code exists yet.
- **December:** Evaluation, Error Analysis & Stretch Horizons — quantitative Baseline vs. Agent comparison, qualitative error analysis, and stretch goals (LangGraph multi-agent refactoring, cross-standard generalization).

All Baseline Model and Benchmark work described above belongs to teammates' work in later sprints and had not started as of this documentation.

---

## 📝 **License**

This project is licensed under the MIT License.

---

## 📄 **References**

- NASA NPR 7150.2D, *Software Engineering Requirements*, Chapter 4 — https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7150_002D_&page_name=Chapter4
- NASA-HDBK-2203 Software Engineering and Assurance Handbook, Topic 5.09 — *SRS - Software Requirements Specification* — https://swehb.nasa.gov/spaces/SWEHBVD/pages/102695669/5.09+-+SRS+-+Software+Requirements+Specification

---

## 🙏 **Acknowledgements**

Thank you to our AI Studio Coach, Sai Duddu, and our Challenge Advisor for their guidance this sprint, and to Break Through Tech AI Studio for the program structure that made this project possible.
