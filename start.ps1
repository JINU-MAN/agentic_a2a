$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host "[1/4] Starting WebSearchAnalyst (port 8001)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m agentic_system_a2a.web_search_agent.a2a_server" -WorkingDirectory $Root

Start-Sleep -Seconds 2

Write-Host "[2/4] Starting PaperAnalyst (port 8002)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m agentic_system_a2a.paper_agent.a2a_server" -WorkingDirectory $Root

Start-Sleep -Seconds 2

Write-Host "[3/4] Starting SnsAnalyst (port 8003)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m agentic_system_a2a.sns_agent.a2a_server" -WorkingDirectory $Root

Write-Host "Waiting for worker agents to be ready..."
Start-Sleep -Seconds 5

Write-Host "[4/4] Starting MainAgent (port 8000)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m agentic_system_a2a.main_agent.a2a_server" -WorkingDirectory $Root

Write-Host ""
Write-Host "All agents started."
Write-Host "  MainAgent       : http://localhost:8000"
Write-Host "  WebSearchAnalyst: http://localhost:8001"
Write-Host "  PaperAnalyst    : http://localhost:8002"
Write-Host "  SnsAnalyst      : http://localhost:8003"
Write-Host ""
Write-Host "Close the individual windows to stop each agent."
