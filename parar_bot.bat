@echo off
chcp 65001 >nul
title Parar Porquinho IA
cd /d "%~dp0"
echo ==================================================
echo         PARANDO O PORQUINHO IA
echo ==================================================
echo.
echo Procurando processos em execucao...
powershell -Command "$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*bot.py*' }; if ($procs) { foreach ($p in $procs) { Stop-Process -Id $p.ProcessId -Force; Write-Host ('Processo ' + $p.ProcessId + ' finalizado com sucesso!') } } else { Write-Host 'Nenhum processo do bot.py em execucao no momento.' }"
echo.
echo Concluido!
timeout /t 3 >nul
