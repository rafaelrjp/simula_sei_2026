@echo off
REM ==========================================================================
REM  simula_sei_2026 - gerador de massa sintetica do SEI dirigido pelo DW
REM
REM  Uso:
REM    script.bat [-anos N^|todos] [-massa F] [-seed S] [--force] [--confirmar] ACAO
REM
REM  Exemplos:
REM    script.bat PREPARAR
REM    script.bat -anos 2 -massa 0.5 CARREGAR
REM    script.bat -anos todos -massa 1 DUMPAR
REM    script.bat -anos 2 -massa 0.005 VALIDAR
REM    script.bat APAGAR --confirmar
REM ==========================================================================
setlocal
set "SCRIPT_DIR=%~dp0"

where python >nul 2>nul
if %ERRORLEVEL%==0 (
    python "%SCRIPT_DIR%simula.py" %*
) else (
    py "%SCRIPT_DIR%simula.py" %*
)
endlocal
