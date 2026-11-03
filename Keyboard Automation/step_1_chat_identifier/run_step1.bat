@echo off
:: ============================================================================
:: Shortcut runner for Step 1: Scan Transcripts, Identify Chat & Focus Window
:: ============================================================================
call "%~dp0run_step1_find_and_focus.bat" %*
exit /b %ERRORLEVEL%
