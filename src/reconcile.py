import pandas as pd
from sklearn.ensemble import IsolationForest
from rules_engine import apply_reconciliation_rules
from generate_evidence import create_pdf_report
import os

os.makedirs("output", exist_ok=True)

# Load data
gl = pd.read_csv("input/GL_Trial_Balance_Nov2025.csv")
sub = pd.read_csv("input/Subledger_Detail_Nov2025.csv")

print(f"Loaded GL: {gl.shape}, Subledger: {sub.shape}")

# Apply rules
summary = apply_reconciliation_rules(gl, sub)
print("\nRule-based Summary:")
print(summary[['Account', 'GL_Balance', 'Subledger_Balance', 'Variance', 'Status']])

# ML-based exception detection on transaction level
detail = sub.copy()
detail['variance'] = detail['Amount'].abs()
iso = IsolationForest(contamination=0.05, random_state=42)
detail['is_outlier'] = iso.fit_predict(detail[['Amount']].fillna(0))
exceptions = detail[detail['is_outlier'] == -1]

# Save results
summary.to_csv("output/reconciliation_summary.csv", index=False)
exceptions.to_excel("output/exceptions_to_review.xlsx", index=False)

# Generate audit evidence
create_pdf_report(summary, exceptions)

print(f"\nDone! Auto-matched: {len(summary[summary['Status']=='Matched'])} accounts")
print(f"Exceptions flagged: {len(exceptions)} transactions → check /output folder")
