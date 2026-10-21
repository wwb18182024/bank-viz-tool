"""Generate a synthetic retail-bank customer dataset for demos and tests.

No real customer data is used anywhere in this project.
Output: data/sample_bank_customers.csv (2,000 customers)
"""
from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(2026)
N = 2000


def generate() -> pd.DataFrame:
    geography = RNG.choice(["France", "Spain", "Germany"], N, p=[0.5, 0.25, 0.25])
    gender = RNG.choice(["Male", "Female"], N, p=[0.52, 0.48])
    age = np.clip(RNG.normal(39, 14, N), 18, 85).astype(int)
    tenure = RNG.integers(0, 11, N)
    # Churn more likely in Germany, for older customers and low product counts
    churn_logit = (
        -1.6
        + 0.55 * (geography == "Germany")
        + 0.03 * (age - 39)
        - 0.45 * (tenure > 5)
        + 0.6 * (RNG.random(N) < 0.25)
    )
    churn = (RNG.random(N) < 1 / (1 + np.exp(-churn_logit))).astype(int)

    balance = np.where(RNG.random(N) < 0.23, 0.0, np.round(RNG.gamma(2.2, 32000, N), 2))
    num_products = RNG.choice([1, 2, 3, 4], N, p=[0.45, 0.38, 0.12, 0.05])
    has_card = RNG.integers(0, 2, N)
    active_member = RNG.integers(0, 2, N)
    estimated_salary = np.round(np.clip(RNG.normal(65000, 28000, N), 12000, 200000), 2)
    credit_score = np.clip(RNG.normal(650, 95, N), 350, 850).astype(int)
    credit_limit = np.round(np.clip(credit_score * 28 + RNG.normal(0, 2500, N), 1000, 45000), 2)
    transaction_count = np.clip(
        RNG.poisson(np.where(active_member == 1, 45, 18) - 3 * num_products), 0, 250
    )
    transaction_amount = np.round(
        np.clip(RNG.gamma(2.0, 380, N) * (0.7 + 0.6 * active_member), 0, 25000), 2
    )
    complaints = RNG.choice([0, 1], N, p=[0.86, 0.14])

    df = pd.DataFrame(
        {
            "CustomerID": [f"CUST{i:05d}" for i in range(1, N + 1)],
            "CreditScore": credit_score,
            "Geography": geography,
            "Gender": gender,
            "Age": age,
            "Tenure": tenure,
            "Balance": balance,
            "NumOfProducts": num_products,
            "HasCrCard": has_card,
            "IsActiveMember": active_member,
            "EstimatedSalary": estimated_salary,
            "CreditLimit": credit_limit,
            "TransactionCount": transaction_count,
            "TransactionAmount": transaction_amount,
            "Complaints": complaints,
            "Churn": churn,
        }
    )
    return df


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "data" / "sample_bank_customers.csv"
    out.parent.mkdir(exist_ok=True)
    df = generate()
    df.to_csv(out, index=False)
    print(f"Wrote {out} with {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"Churn rate: {df['Churn'].mean():.1%}")
