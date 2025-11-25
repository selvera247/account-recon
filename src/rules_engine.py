import pandas as pd

def apply_reconciliation_rules(gl_df, sub_df):
    # Normalize keys
    gl_df = gl_df.copy()
    sub_df = sub_df.copy()

    # Map subledger to GL accounts (customize per company)
    account_mapping = {
        "Deferred Revenue - Current": "2200",
        "Deferred Revenue - Long Term": "2210",
        "Accounts Receivable": "1200",
        "Bank - Operating - USD": "1010"
    }

    results = []

    for acct_name, acct_num in account_mapping.items():
        gl_bal = gl_df[gl_df['Account_Number'] == acct_num]['Balance_Nov302025'].iloc[0]

        if "Deferred" in acct_name:
            sub_bal = sub_df[sub_df['Recognition_Status'].str.contains('Deferred|Partially', na=False)]['Amount'].sum()
        elif "Receivable" in acct_name:
            sub_bal = sub_df[sub_df['Source'] == 'AR Invoice']['Amount'].sum()
        elif "Bank" in acct_name:
            sub_bal = sub_df[sub_df['Item_or_Account'].str.contains('Bank', na=False)]['Amount'].sum()
        else:
            sub_bal = 0

        variance = abs(gl_bal - sub_bal)
        tolerance = abs(gl_bal) * 0.005  # 0.5% tolerance
        status = "Matched" if variance <= max(tolerance, 10) else "Exception"

        results.append({
            "Account": acct_name,
            "GL_Balance": gl_bal,
            "Subledger_Balance": sub_bal,
            "Variance": gl_bal - sub_bal,
            "Status": status
        })

    return pd.DataFrame(results)
