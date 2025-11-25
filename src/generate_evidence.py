from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
import os

def create_pdf_report(summary_df, exceptions_df, month="November 2025"):
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template.html') if os.path.exists('template.html') else None

    html_content = f"""
    <h1>Account Reconciliation - {month}</h1>
    <h2>Summary</h2>
    {summary_df.to_html(index=False)}
    <h2>Exceptions Requiring Review ({len(exceptions_df)})</h2>
    {exceptions_df.to_html(index=False)}
    <p>Generated automatically on {pd.Timestamp('now').strftime('%Y-%m-%d %H:%M')}</p>
    """

    HTML(string=html_content).write_pdf("output/Reconciliation_Evidence_Nov2025.pdf")
    print("Evidence PDF generated → output/Reconciliation_Evidence_Nov2025.pdf")
