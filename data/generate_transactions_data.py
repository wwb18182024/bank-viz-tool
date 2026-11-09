"""Generate a synthetic retail-bank *transaction-level* dataset (AI-generated
test data). Complements sample_bank_customers.csv (customer profiles) with a
transaction log for behaviour-oriented visualisation testing."""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
N_CUSTOMERS = 800
N_TXNS = 8000

cust_ids = rng.integers(100000, 999999, size=N_CUSTOMERS)
channels = rng.choice(["branch", "ATM", "online", "mobile"], size=N_TXNS,
                      p=[0.15, 0.30, 0.25, 0.30])
txn_types = rng.choice(["deposit", "withdrawal", "transfer", "bill_payment"],
                       size=N_TXNS, p=[0.25, 0.30, 0.25, 0.20])
merchant_cat = rng.choice(
    ["groceries", "utilities", "restaurants", "travel", "retail", "healthcare", "none"],
    size=N_TXNS, p=[0.22, 0.18, 0.20, 0.08, 0.20, 0.07, 0.05])

# Log-normal amounts: most small, few large - typical bank transaction shape
amounts = np.round(rng.lognormal(mean=4.2, sigma=1.1, size=N_TXNS), 2)
amounts = np.clip(amounts, 1.5, 25000)

# Customers differ in activity: some power users generate more txns
customer_col = rng.choice(cust_ids, size=N_TXNS,
                          p=rng.dirichlet(np.ones(N_CUSTOMERS) * 0.35))

days = rng.integers(1, 181, size=N_TXNS)           # 180-day window
dates = (pd.Timestamp("2026-05-01") + pd.to_timedelta(days, unit="D")).strftime("%Y-%m-%d")
hours = rng.choice(range(7, 23), size=N_TXNS,
                   p=rng.dirichlet(np.ones(16) * 2.0))
minutes = rng.integers(0, 60, size=N_TXNS)

# International + fraud flags: rare, correlated with amount size
is_intl = (rng.random(N_TXNS) < 0.04).astype(int)
fraud_p = 0.002 + 0.03 * (amounts > 5000) * is_intl
is_flagged = (rng.random(N_TXNS) < fraud_p).astype(int)

df = pd.DataFrame({
    "transaction_id": [f"TXN{i:06d}" for i in range(N_TXNS)],
    "customer_id": customer_col,
    "txn_date": dates,
    "txn_hour": hours,
    "txn_minute": minutes,
    "channel": channels,
    "txn_type": txn_types,
    "merchant_category": merchant_cat,
    "amount": amounts,
    "is_international": is_intl,
    "is_flagged": is_flagged,
})
out = r"E:\bank-viz-tool\data\open_datasets\synthetic_bank_transactions.csv"
df.to_csv(out, index=False)
print("synthetic_bank_transactions.csv:", df.shape)
print("flagged rate:", df["is_flagged"].mean().round(4),
      "| intl rate:", df["is_international"].mean().round(4))
