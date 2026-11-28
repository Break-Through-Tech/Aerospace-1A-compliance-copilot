# Compliance Copilot: Auditing Software Requirements Against Engineering Standards

An AI-assisted first-pass auditor that checks a Software Requirements Specification (SRS) against
NASA's software engineering standard, **NPR 7150.2D**, and produces structured, cited findings that
an engineer can verify.

Built by Team Aerospace 1A for the Break Through Tech AI Studio, Fall 2026.

---

### 👥 **Team Members**

| Name          | GitHub Handle  | Contribution |
|---------------|----------------|--------------|
| Sumehra Saif  | @sum09fairSaif | TODO |
| Binayak Subedi | TODO          | TODO |
| Essey Tesfamichael Araya | TODO | TODO |
| Gabriel       | TODO           | TODO |
| Prakriti      | TODO           | TODO |
| Hemadharshini | TODO           | TODO |
| Yichen        | TODO           | TODO |
| Leilt         | TODO           | TODO |

---

## 🎯 **Project Highlights**

- Extracted and cleaned **100 SWE requirement clauses** (Sections 3.1–5.5) from the NPR 7150.2D PDF,
  joined them with Appendix C applicability data, and identified **16 clauses an SRS can address**.
- Built a **non-LLM baseline** (keyword rules + TF-IDF retrieval + explicit evidence checks) as
  reusable, tested Python code in [`src/compliance_copilot/`](src/compliance_copilot/).
- Built a **ChromaDB vector store** of 144 documents (100 clause bodies + 44 notes) embedded with
  Qwen3-Embedding-0.6B, with tests that check storage, cosine similarity and repeatable retrieval.
- Built a **RAG pipeline** that retrieves NASA clauses for each requirement and asks an LLM
  (`openai/gpt-oss-120b` via Groq) for a verdict, validated with **Pydantic schemas** that require
  at least one cited clause.
- Implemented the advisor's **Output Contract v1** as Pydantic models and checked them against the
  Data Card's sample report.

---

## 🏗️ **Project Overview**

In safety-critical software (space missions, medical devices, financial systems), every requirement
must be reviewed clause by clause against a compliance standard before code is written. That review
depends on a small group of senior experts and takes weeks. Compliance Copilot aims to produce a
fast, structured first-pass report that any engineer can inspect.

The project has two stages:

1. **Non-agentic baseline:** a deterministic retrieval pipeline that finds relevant standard clauses
   and judges each requirement, with every verdict citing a clause ID.
2. **Tool-calling LLM agent** (in progress): an agent with `retrieve_clause`, `check_requirement` and
   `log_gap` tools that runs the audit and writes JSON and Markdown gap reports.

See [Challenge-Project-Overview.md](Challenge-Project-Overview.md) for the full brief, success
criteria and milestones.

### Progress

| Month | Milestone | Status |
|-------|-----------|--------|
| September | Data access, clause extraction, triage, non-LLM baseline | ✅ Done |
| October | Chroma vector store, RAG pipeline, Pydantic schema enforcement | ✅ Done; Output Contract v1 review in progress |
| November | Tool-calling agent, rate-limit handling, JSON/Markdown reports | 🔄 In progress |
| December | Benchmark evaluation, error analysis, stretch goals | ⏳ Planned |

---

## 📊 **Data**

| Source | Location | Use |
|--------|----------|-----|
| NASA NPR 7150.2D (PDF) | [notebooks/N_PR_7150_002D_.pdf](notebooks/N_PR_7150_002D_.pdf) | The compliance standard (answer key) |
| NASA-HDBK-2203 §5.09 (SRS guidance) | [data/NASA-HDBK-2203_5.09_SRS.html](data/NASA-HDBK-2203_5.09_SRS.html), a snapshot saved on 2026-11-21 from [swehb.nasa.gov](https://swehb.nasa.gov/spaces/SWEHBVD/pages/102695669/5.09+-+SRS+-+Software+Requirements+Specification) | Reference guidance for requirement quality |
| Starhawk Mission Computer SRS | [data/Starhawk Mission Computer SRS.md](data/Starhawk%20Mission%20Computer%20SRS.md) | Synthetic SRS to audit (54 numbered requirements, `SFMC-REQ-xxx`) |
| SRS-addressable clauses | [data/processed/](data/processed/) | 16 clauses exported from the notebook (incl. SWE-054/055 for the Data Card's core scope), with a hash manifest |
| Advisor Data Card | [Data Card/](Data%20Card/) | 37 benchmark cases (11 calibration with labels, 26 holdout), Output Contract v1 schema, sample report and validator |

**Preparation steps** (in [Aerospace_1A.ipynb](notebooks/Aerospace_1A.ipynb)):

- Extract clauses with `pdfplumber` and regex, then join Appendix C attributes (applicability by
  software class).
- Tag each clause with a functional category and the action verbs it requires.
- Run QA checks: find clauses that swallowed the next clause (2+ SWE tags), compare body and
  Appendix C counts, and split merged clauses back into separate rows.
- Mark which clauses an SRS can provide evidence for (`direct` / `partial`).

Team observations on the SRS are in [data/initial_srs_observations.md](data/initial_srs_observations.md).

---

## 🧠 **Model Development**

### 1. Non-LLM baseline (September)

- **18 keyword rules** flag ambiguous wording in requirements.
- **TF-IDF retrieval** fitted on the 16 SRS-addressable clauses returns up to 3 candidate clauses per
  requirement, ranked by cosine similarity.
- **Evidence checks** for 7 provisions (SWE-034, 050, 052, 053, 157, 184, 210) return `Meets`,
  `Partial`, `Gap` or `REVIEW`.

Details, rules and limits: [docs/baseline.md](docs/baseline.md). Short notebook:
[TF_IDF_Baseline_Model.ipynb](notebooks/TF_IDF_Baseline_Model.ipynb).

### 2. Vector store and RAG (October)

- Each clause and note becomes a document tagged with SWE ID, clause ID, section and category.
- Documents are embedded with **Qwen3-Embedding-0.6B** (GPU when available, otherwise CPU, which is
  slower) and stored in an in-memory **ChromaDB** collection using cosine distance.
- `retrieve_unique_clauses()` returns the top-k different clauses, so a clause can't fill several
  places through its notes.
- The first LLM loop asked for `COMPLIANT` / `NON_COMPLIANT` verdicts. It was replaced by the
  Output Contract review below and removed from the notebook (see git history before `3e50cae`).

### 3. Output Contract v1 review (current pipeline)

- Pydantic models (`SRSEvidence`, `NASAReference`, `QualityIssue`, `SWELink`, `RequirementReview`)
  match the advisor's contract, reject fields that aren't in it, and enforce its cross-field rules.
- Each requirement review sends the LLM the full SRS, the 5 most relevant NASA-HDBK-2203 §5.09
  passages (sections 1 and 3), and the six core NPR §4.1 clauses (SWE-050, 051, 184, 053, 054,
  055) ranked by relevance.
- Every answer is validated against `RequirementReview` and checked for grounding: citations must
  come from the passages sent (or the Handbook section one level above one), and SRS quotes must
  appear word for word in the SRS.
- A failed answer is retried up to 3 times; after that the requirement is marked "Not assessed"
  (`UNDETERMINED`) and the run continues.
- Fixed settings (`openai/gpt-oss-120b` on Groq, temperature 0, seed 42). Every LLM call is logged
  with the model fingerprint, tokens used and outcome.
- A full run saves all 54 reviews to `results/<run name>.jsonl` and can resume if interrupted. A
  comparison cell reports how many decisions change between two runs.

---

## 📈 **Results & Key Findings**

**Baseline pipeline** (Starhawk SRS, `top_k=3`):

- 54 requirements × 16 clauses → 64 candidate pairs; 17 requirements have no lexical match.
- Keyword rules flag 17 requirements.
- Document checks: 4 gaps, 3 partial-evidence results, 9 reviews.

These are pipeline counts, not accuracy. TF-IDF misses related words (for example,
`authenticate` vs. `authentication`) and abstract NASA wording.

**Vector store:** all 144 documents, metadata and embeddings verified; similarity scores match an
independent cosine calculation, and repeated queries return identical results.

**Output Contract review (non-agentic RAG baseline, 2026-11-28):** on the advisor's 7 calibration
requirement cases, precision 100% (5 of 5) and recall 83% (5 of 6); 87–91% of answers had all
citations grounded; across two runs the verdict was the same for all 52 requirements assessed in
both. Only 7
cases have answers, so these are a first indication. Details, failure cases and recommendations:
[docs/rag_baseline_results.md](docs/rag_baseline_results.md).

---

## 👩🏽‍💻 **Setup and Installation**

### Baseline (local, no API key)

Requires Python 3.9+.

```sh
git clone https://github.com/Break-Through-Tech/Aerospace-1A-compliance-copilot.git
cd Aerospace-1A-compliance-copilot
python -m pip install -r requirements-dev.txt   # includes PyTorch for the vector search: a large download
python scripts/run_baseline.py        # writes results to output/baseline/
python -m pytest -q                   # runs the test suite
```

To evaluate against a labeled benchmark CSV:

```sh
python scripts/run_baseline.py --benchmark data/benchmark.csv --split test
```

### Main notebook (Google Colab)

1. Open [notebooks/Aerospace_1A.ipynb](notebooks/Aerospace_1A.ipynb) in Colab.
2. Set **Runtime → Change runtime type → T4 GPU** (recommended: the embedding model also runs on a CPU,
   but much more slowly).
3. Add your OpenAI API key as a Colab secret named `OPENAI_API_KEY`. To use Groq instead, set
   `LLM_PROVIDER = "groq"` in the API client cell and add a `GROQ_API_KEY` secret.
4. Run all cells in order. The September cells extract clauses; the October cells build the vector
   store and run the RAG pipeline.

A full run over all 54 requirements takes about 6 minutes with OpenAI. The free Groq tier's
tokens-per-minute limit is too small for these prompts.

### Repository layout

```
├── Data Card/             Advisor benchmark, Output Contract v1 schema, sample report, validator
├── data/                  Starhawk SRS, team observations, processed clause export
├── docs/baseline.md       Baseline design, rules and outputs
├── notebooks/             Main notebook, TF-IDF baseline notebook, NPR 7150.2D PDF
├── scripts/               run_baseline.py, import_clauses.py
├── src/compliance_copilot/  Baseline package (data, retrieval, pipeline, evaluation) and vector_store (Chroma search)
└── tests/                 pytest suite
```

---

## 🚀 **Next Steps**

- Fix the grounding failures and define the issue codes in the prompt, then re-run and re-measure
  (see [docs/rag_baseline_results.md](docs/rag_baseline_results.md)).
- Ask the advisor to score the 26 holdout cases, and generate `report.json` (#25).
- Wrap the pipeline in a tool-calling agent (`retrieve_clause`, `check_requirement`, `log_gap`) with
  caching and batching for rate limits.
- Generate full JSON and Markdown gap reports.
- Compare baseline vs. agent and run error analysis; stretch goals include a LangGraph multi-agent
  version or applying the approach to another standard.

---

## 📝 **License**

To be decided, pending Challenge Advisor approval.

---

## 📄 **References**

- NASA, [NPR 7150.2D: NASA Software Engineering Requirements](https://nodis3.gsfc.nasa.gov/npg_img/N_PR_7150_002D_/N_PR_7150_002D_.pdf)
- NASA, [NASA-HDBK-2203 §5.09: SRS – Software Requirements Specification](https://swehb.nasa.gov/spaces/SWEHBVD/pages/102695669/5.09+-+SRS+-+Software+Requirements+Specification)
- [ChromaDB](https://docs.trychroma.com/), [Pydantic](https://docs.pydantic.dev/), [Qwen3-Embedding](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B), [Groq](https://console.groq.com/docs)

---

## 🙏 **Acknowledgements**

Thank you to our Challenge Advisor, our AI Studio Coach Sai Duddu, and the Break Through Tech AI
Studio team for their guidance and support.
