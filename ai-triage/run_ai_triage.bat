@echo off
REM Run AI triage script from this folder, using local venv

cd /d %~dp0
call venv\Scripts\activate
python ai_triage.py