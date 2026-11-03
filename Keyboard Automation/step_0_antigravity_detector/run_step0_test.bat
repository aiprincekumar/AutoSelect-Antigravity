@echo off
REM ============================================================================
REM Step 0: AntiGravity Detector - Testing Runner Alias
REM Points directly to canonical runner: run_step0.bat
REM ============================================================================

call "%~dp0run_step0.bat" %*
exit /b %ERRORLEVEL%
