from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture
def project_root():
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def clauses(project_root):
    return pd.read_csv(project_root / "data/processed/srs_addressable_clauses.csv")
