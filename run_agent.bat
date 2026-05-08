@echo off
cd /d "%~dp0"

echo ===== %date% %time% start ===== >> agent_log.txt

set PYTHONUNBUFFERED=1

where python >nul 2>&1
if %ERRORLEVEL%==0 (
  set PYTHON_CMD=python
) else (
  set PYTHON_CMD=py
)

%PYTHON_CMD% -u agent.py >> agent_log.txt 2>&1
echo after agent.py exitcode=%ERRORLEVEL% >> agent_log.txt

%PYTHON_CMD% -u generate_site.py >> agent_log.txt 2>&1
echo after generate_site.py exitcode=%ERRORLEVEL% >> agent_log.txt

echo ===== %date% %time% end ===== >> agent_log.txt
