import pandas as pd
from weasyprint import HTML
import os

def create_pdf_report(summary_df, exceptions_df, month="November 2025"):
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #34495e; margin-top: 30px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th {{ background-color: #3498db; color: white; padding: 12px; text-align: left; }}
            td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            .timestamp {{ color: #7f8c8d; font-style: italic; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <h1>Account Reconciliation Report - {month}</h1>
        <h2>Summary</h2>
        {summary_df.to_html(index=False, escape=False)}
        <h2>Exceptions Requiring Review ({len(exceptions_df)} transactions)</h2>
        {exceptions_df.to_html(index=False, escape=False)}
        <p class="timestamp">Generated automatically on {pd.Timestamp('now').strftime('%Y-%m-%d %H:%M')}</p>
    </body>
    </html>
    """

    HTML(string=html_content).write_pdf("output/Reconciliation_Evidence_Nov2025.pdf")
    print("✓ Evidence PDF generated → output/Reconciliation_Evidence_Nov2025.pdf")