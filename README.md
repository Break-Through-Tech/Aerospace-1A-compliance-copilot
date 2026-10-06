# Aerospace Compliance Copilot

A Break Through Tech AI Studio project that reviews a synthetic software
requirements specification against NASA NPR 7150.2D clauses. See the
[challenge overview](Challenge-Project-Overview.md) for the project goals and
planned RAG and tool-calling agent stages.

The current non-LLM baseline uses TF-IDF retrieval, keyword checks, and limited
rules for inspecting SRS evidence. It preserves clause citations and abstains
when evidence is insufficient. Verdicts apply to named evidence provisions;
they do not establish complete NASA compliance.

## Run the baseline

From the repository root in a Python environment:

```sh
python -m pip install -r requirements-dev.txt
python scripts/run_baseline.py
python -m pytest -q
```

Validated inputs are committed under `data/processed/`. Rebuild them offline from
the bundled NASA PDF and Starhawk SRS with:

```sh
python scripts/prepare_data.py
```

Open [Baseline_Model.ipynb](notebooks/Baseline_Model.ipynb) for the short experiment.
The original [Aerospace_1A.ipynb](notebooks/Aerospace_1A.ipynb) retains the team's
extraction, cleaning, and initial keyword exploration.

[Baseline documentation](docs/baseline.md) explains the Mermaid workflow, rules,
outputs, limitations, and benchmark schema. Results go to `output/baseline/`.
The advisor's benchmark and Data Card are still needed for measured precision
and recall; ordinary runs report that dependency explicitly.
