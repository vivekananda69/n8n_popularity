@echo off

REM change directory to project
cd /d "C:\Users\sai chandu\OneDrive\Desktop\n8n\n8n_popularity"

REM call venv python to run manage.py and append logs
"C:\Users\sai chandu\OneDrive\Desktop\n8n\venv\Scripts\python.exe" manage.py fetch_workflows >> "C:\Users\sai chandu\OneDrive\Desktop\n8n\n8n_popularity\logs\fetch.log" 2>&1
