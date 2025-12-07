# AI Triage Engine (Analytics Intake)

This folder contains the Python code that enriches new intake requests in Google Sheets
with AI-generated triage information (summary, tags, priority, effort, risk notes).

## Setup

1. Create a Python virtual environment:

   ```bash
   cd ai-triage
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt