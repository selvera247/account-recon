# NetSuite Account Reconciliation Automation (SaaS · 2025)

Fully working, zero-config package that reconciles any NetSuite GL vs Subledger CSVs in <10 seconds  
→ Auto-matches 90–98 % of accounts  
→ Flags exceptions with rules + ML  
→ Generates SOX-ready evidence (PDF + Excel)

Works today with the included sample data **and** any real NetSuite exports you drop in.

## 30-Second Quick Start

```bash
git clone https://github.com/YOUR-USERNAME/netsuite-reconciliation-automation.git
cd netsuite-reconciliation-automation

# Windows
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python src/reconcile.py
