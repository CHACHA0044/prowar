import pandas as pd
import numpy as np

df = pd.read_csv("transactions.csv")
print("=== DATASET VALIDATION ===")
print("Row count:", len(df))
print("Columns:", list(df.columns))
print("Data types:\n", df.dtypes)
print("Null counts:\n", df.isnull().sum())
print("Duplicate txn_id count:", df["txn_id"].duplicated().sum())
print("Negative/zero amount count:", (df["amount"] <= 0).sum())
print("Min amount:", df["amount"].min(), "Max amount:", df["amount"].max())
print("Timestamp min:", df["timestamp"].min(), "max:", df["timestamp"].max())
print("Unique senders:", df["sender_id"].nunique(), "Unique receivers:", df["receiver_id"].nunique())
print("Channels:", df["channel"].value_counts().to_dict())
print("Fraud count:", int((df["is_fraud"] == 1).sum()), f"({(df['is_fraud'] == 1).mean():.4%})")
print("AML count:", int((df["is_aml_pattern"] == 1).sum()), f"({(df['is_aml_pattern'] == 1).mean():.4%})")
print("Overlap fraud & AML:", int(((df["is_fraud"] == 1) & (df["is_aml_pattern"] == 1)).sum()))
print("Edge case count:", int((df["is_edge_case"] == 1).sum()))
print("Pattern types:\n", df["pattern_type"].value_counts().to_dict())
print("Sender balance consistency check (sender_balance_before < amount):",
      int((df["sender_balance_before"].dropna() < df.loc[df["sender_balance_before"].notnull(), "amount"]).sum()))

