@echo off
cd /d "%~dp0"

echo Clearing session log...
if not exist logs mkdir logs
type nul > logs\session.log

echo [1/4] Starting WebSearchAnalyst (port 8001)...
start "WebSearchAnalyst" powershell -NoExit -Command "python -m agentic_system_a2a.web_search_agent.a2a_server"
timeout /t 2 /nobreak > /dev/null

echo [2/4] Starting PaperAnalyst (port 8002)...
start "PaperAnalyst" powershell -NoExit -Command "python -m agentic_system_a2a.paper_agent.a2a_server"
timeout /t 2 /nobreak > /dev/null

echo [3/4] Starting SnsAnalyst (port 8003)...
start "SnsAnalyst" powershell -NoExit -Command "python -m agentic_system_a2a.sns_agent.a2a_server"

echo Waiting for worker agents to be ready...
timeout /t 5 /nobreak > /dev/null

echo [4/4] Starting MainAgent (port 8000)...
start "MainAgent" powershell -NoExit -Command "python -m agentic_system_a2a.main_agent.a2a_server"

echo.
echo All agents started.
echo   MainAgent       : http://localhost:8000
echo   WebSearchAnalyst: http://localhost:8001
echo   PaperAnalyst    : http://localhost:8002
echo   SnsAnalyst      : http://localhost:8003
echo.
echo Session log : logs\session.log
echo Agent logs  : logs\{mainagent,websearchanalyst,...}.log
echo.
echo Close the individual windows to stop each agent.
