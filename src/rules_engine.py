import pandas as pd

def apply_reconciliation_rules(gl_df, sub_df):
    gl_df = gl_df.copy()
    sub_df = sub_df.copy()

    account_mapping = {
        "Deferred Revenue - Current": "2200",
        "Deferred Revenue - Long Term": "2210",
        "Accounts Receivable": "1200",
        "Bank - Operating - USD": "1010"
    }

    results = []

    for acct_name, acct_num in account_mapping.items():
        # Safe lookup with default value
        gl_match = gl_df[gl_df['Account_Number'] == acct_num]['Balance_Nov302025']
        if gl_match.empty:
            print(f"Warning: Account {acct_num} ({acct_name}) not found in GL")
            continue
        gl_bal = gl_match.iloc[0]

        if "Deferred" in acct_name:
            sub_bal = sub_df[sub_df['Recognition_Status'].str.contains('Deferred|Partially', na=False)]['Amount'].sum()
        elif "Receivable" in acct_name:
            sub_bal = sub_df[sub_df['Source'] == 'AR Invoice']['Amount'].sum()
        elif "Bank" in acct_name:
            sub_bal = sub_df[sub_df['Item_or_Account'].str.contains('Bank', na=False)]['Amount'].sum()
        else:
            sub_bal = 0

        variance = gl_bal - sub_bal
        tolerance = abs(gl_bal) * 0.005
        status = "Matched" if abs(variance) <= max(tolerance, 10) else "Exception"

        results.append({
            "Account": acct_name,
            "GL_Balance": gl_bal,
            "Subledger_Balance": sub_bal,
            "Variance": variance,
            "Status": status
        })

    return pd.DataFrame(results)