@echo off
echo Testando endpoints do backend...
echo.

echo [1/5] Health check...
curl -s http://localhost:8000/health
echo.
echo.

echo [2/5] Contando notificacoes nao lidas...
curl -s http://localhost:8000/api/notifications/count/unread
echo.
echo.

echo [3/5] Listando notificacoes...
curl -s http://localhost:8000/api/notifications?limit=5
echo.
echo.

echo [4/5] Testando busca global (lead)...
curl -s "http://localhost:8000/api/search?q=lead"
echo.
echo.

echo [5/5] Testando interactions...
curl -s http://localhost:8000/api/interactions?limit=3
echo.
echo.

echo Testes concluidos!
pause
