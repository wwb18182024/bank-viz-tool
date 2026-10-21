"""Shared pytest fixtures — a small synthetic retail-bank dataset."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def bank_df() -> pd.DataFrame:
    rng = np.random.default_rng(7)
    n = 300
    churn = rng.integers(0, 2, n)
    return pd.DataFrame(
        {
            "CustomerID": [f"C{i:04d}" for i in range(n)],
            "Age": rng.integers(18, 75, n),
            "Geography": rng.choice(["France", "Spain", "Germany"], n),
            "Gender": rng.choice(["Male", "Female"], n),
            "Balance": np.round(rng.gamma(2, 20000, n), 2),
            "NumOfProducts": rng.integers(1, 4, n),
            "EstimatedSalary": np.round(rng.normal(60000, 20000, n), 2),
            "TransactionCount": rng.poisson(35, n),
            "TransactionAmount": np.round(rng.gamma(2, 500, n), 2),
            "CreditLimit": np.round(rng.normal(15000, 5000, n), 2),
            "Churn": churn,
        }
    )
