import pandas as pd
from sklearn.ensemble import IsolationForest
from rules_engine import apply_reconciliation_rules
from generate_evidence import create_pdf_report
import os

# Create output directory
os.makedirs("output", exist_ok=True)

try:
    # Load data
    print("Loading data files...")
    gl = pd.read_csv("input/GL_Trial_Balance_Nov2025.csv")
    sub = pd.read_csv("input/Subledger_Detail_Nov2025.csv")
    print(f"✓ Loaded GL: {gl.shape[0]} rows, Subledger: {sub.shape[0]} rows")

    # Apply rules-based reconciliation
    print("\nApplying reconciliation rules...")
    summary = apply_reconciliation_rules(gl, sub)
    print("\nRule-based Summary:")
    print(summary[['Account', 'GL_Balance', 'Subledger_Balance', 'Variance', 'Status']])

    # ML-based exception detection on transaction level
    print("\nRunning ML-based anomaly detection...")
    detail = sub.copy()
    iso = IsolationForest(contamination=0.05, random_state=42)
    detail['is_outlier'] = iso.fit_predict(detail[['Amount']].fillna(0))
    exceptions = detail[detail['is_outlier'] == -1]

    # Save results
    print("\nSaving results...")
    summary.to_csv("output/reconciliation_summary.csv", index=False)
    exceptions.to_excel("output/exceptions_to_review.xlsx", index=False)
    print("✓ Summary saved to output/reconciliation_summary.csv")
    print("✓ Exceptions saved to output/exceptions_to_review.xlsx")

    # Generate audit evidence PDF
    print("\nGenerating PDF report...")
    create_pdf_report(summary, exceptions)

    # Final summary
    print("\n" + "="*60)
    print("RECONCILIATION COMPLETE")
    print("="*60)
    print(f"✓ Auto-matched accounts: {len(summary[summary['Status']=='Matched'])}/{len(summary)}")
    print(f"✓ Exception accounts: {len(summary[summary['Status']=='Exception'])}/{len(summary)}")
    print(f"✓ Anomalous transactions flagged: {len(exceptions)}")
    print(f"\n→ Check the /output folder for detailed reports")
    print("="*60)

except FileNotFoundError as e:
    print(f"\n❌ Error: Required input file not found")
    print(f"   Details: {e}")
    print(f"\n   Please ensure the following files exist:")
    print(f"   - input/GL_Trial_Balance_Nov2025.csv")
    print(f"   - input/Subledger_Detail_Nov2025.csv")

except KeyError as e:
    print(f"\n❌ Error: Required column not found in data")
    print(f"   Details: {e}")
    print(f"\n   Please check that your CSV files have the expected column names")

except Exception as e:
    print(f"\n❌ An unexpected error occurred: {e}")
    import traceback
    traceback.print_exc()