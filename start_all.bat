@echo off
chcp 65001 > nul

echo [1/3] FastAPI Backend (8888) starting...
start "Backend" cmd /k "cd /d %~dp0backend && python main.py"

timeout /t 3 /nobreak > nul

echo [2/3] MCP SSE Server (8889) starting...
start "MCP_SSE" cmd /k "cd /d %~dp0mcp_server && python main.py"

timeout /t 2 /nobreak > nul

echo [3/3] Vue2 Frontend (3000) starting...
start "Frontend" cmd /k "cd /d %~dp0frontend && npm run serve"

echo.
echo ==================================================
echo   Backend API : http://localhost:8888/docs
echo   MCP SSE     : http://localhost:8889/sse
echo   Frontend    : http://localhost:3000
echo ==================================================
pause