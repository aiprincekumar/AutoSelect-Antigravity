@echo off
REM ============================================================================
REM Step 0: AntiGravity Detector - Testing Runner Alias (10s Timer Dashboard)
REM Points directly to canonical runner: run_step0.bat with --mode test --interactive
REM ============================================================================

call "%~dp0run_step0.bat" --mode test --interactive %*
exit /b %ERRORLEVEL%
