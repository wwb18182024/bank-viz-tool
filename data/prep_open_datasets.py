"""Convert the three downloaded open bank datasets into clean CSVs with
human-readable column names, then verify each through the BankViz metadata
engine. Outputs land in data/open_datasets/ next to this script's folder."""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "backend"))

from app.core.metadata import extract_metadata  # noqa: E402

OUT = HERE / "open_datasets"

# ---- Fetch raw sources if missing (idempotent) -----------------------------
import subprocess  # noqa: E402
import zipfile  # noqa: E402

def fetch(name: str, url: str) -> None:
    if not (OUT / name).exists():
        subprocess.run(["curl", "-sL", "--max-time", "180", "-o", str(OUT / name), url],
                       check=True)
        print("downloaded:", name)

fetch("german.data", "https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/german/german.data")
fetch("australian.dat", "https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/australian/australian.dat")
fetch("kaggle_churn_raw.csv", "https://raw.githubusercontent.com/YBI-Foundation/Dataset/main/Bank%20Churn%20Modelling.csv")
if not (OUT / "bank_marketing_x/bank-full.csv").exists():
    subprocess.run(["curl", "-sL", "--max-time", "180", "-o", str(OUT / "bank_marketing.zip"),
                    "https://archive.ics.uci.edu/static/public/222/bank+marketing.zip"], check=True)
    zipfile.ZipFile(OUT / "bank_marketing.zip").extractall(OUT / "bank_marketing_x")
    zipfile.ZipFile(OUT / "bank_marketing_x/bank.zip").extractall(OUT / "bank_marketing_x")
if not (OUT / "credit_default_x/default of credit card clients.xls").exists():
    subprocess.run(["curl", "-sL", "--max-time", "300", "-o", str(OUT / "credit_default.zip"),
                    "https://archive.ics.uci.edu/static/public/350/default+of+credit+card+clients.zip"], check=True)
    zipfile.ZipFile(OUT / "credit_default.zip").extractall(OUT / "credit_default_x")

# ---- 1. German Credit (UCI 144) -------------------------------------------
german_cols = [
    "checking_account", "duration_months", "credit_history", "purpose",
    "credit_amount", "savings_account", "employment_years", "installment_rate",
    "personal_status", "other_debtors", "residence_years", "property",
    "age", "other_installment_plans", "housing", "existing_credits",
    "job", "dependents", "telephone", "foreign_worker", "default",
]
df = pd.read_csv(OUT / "german.data", sep=r"\s+", header=None, names=german_cols)
df["default"] = (df["default"] == 2).astype(int)  # 2 = bad -> churn-style 0/1 flag
df.to_csv(OUT / "german_credit.csv", index=False)
print("german_credit.csv:", df.shape)

# ---- 2. Bank Marketing (UCI 222) ------------------------------------------
bm = pd.read_csv(OUT / "bank_marketing_x/bank-full.csv", sep=";")
bm = bm.rename(columns={"y": "subscribed_term_deposit"})
bm["subscribed_term_deposit"] = (bm["subscribed_term_deposit"] == "yes").astype(int)
bm.to_csv(OUT / "bank_marketing.csv", index=False)
print("bank_marketing.csv:", bm.shape)

# ---- 3. Credit Card Default (UCI 350, xls) --------------------------------
xls = pd.read_excel(OUT / "credit_default_x/default of credit card clients.xls",
                    header=1, engine="xlrd")
xls = xls.rename(columns={xls.columns[0]: "customer_id"})
pay_cols = {f"PAY_{i}": f"payment_status_month{'_'+str(i) if i else 's_ago'}" for i in range(6)}
bill_cols = {f"BILL_AMT{i}": f"bill_amount_month{i}" for i in range(1, 7)}
pay_amt = {f"PAY_AMT{i}": f"payment_amount_month{i}" for i in range(1, 7)}
xls = xls.rename(columns={**pay_cols, **bill_cols, **pay_amt,
                          "default payment next month": "default_next_month"})
xls.to_csv(OUT / "credit_card_default.csv", index=False)
print("credit_card_default.csv:", xls.shape)

# ---- 4. Australian Credit Approval (UCI statlog, anonymised attributes) ----
au_cols = [f"a{i}" for i in range(1, 15)] + ["approved"]
au = pd.read_csv(OUT / "australian.dat", sep=r"\s+", header=None, names=au_cols)
au.to_csv(OUT / "australian_credit.csv", index=False)
print("australian_credit.csv:", au.shape)

# ---- 5. Bank Customer Churn (Kaggle Churn Modelling, GitHub mirror) --------
ch = pd.read_csv(OUT / "kaggle_churn_raw.csv")
ch = ch.drop(columns=["Surname"])  # customer surnames: not needed, drop for privacy hygiene
ch.columns = [c.strip().lower().replace(" ", "_") for c in ch.columns]
ch = ch.rename(columns={"has_credit_card": "has_cr_card",
                        "is_active_member": "is_active_member",
                        "estimated_salary": "estimated_salary",
                        "num_of_products": "num_of_products"})
ch.to_csv(OUT / "kaggle_churn_modelling.csv", index=False)
print("kaggle_churn_modelling.csv:", ch.shape)

# ---- Verify each through the BankViz metadata engine ----------------------
print("\n=== metadata engine verification ===")
for f in ["german_credit.csv", "bank_marketing.csv", "credit_card_default.csv",
          "australian_credit.csv", "kaggle_churn_modelling.csv",
          "synthetic_bank_transactions.csv"]:
    d = pd.read_csv(OUT / f)
    meta = extract_metadata(d)
    sem = [f"{c['name']}:{c['semantic_type'][:4]}" for c in meta["columns"]]
    print(f"\n{f} -> {meta['n_rows']} rows x {meta['n_columns']} cols")
    print("  ", ", ".join(sem))
