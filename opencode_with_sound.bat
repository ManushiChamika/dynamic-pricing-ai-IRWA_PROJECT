@echo off
REM Wrapper script for opencode with sound notification
REM Run opencode with all arguments, then play sound on completion

REM Run opencode with passed arguments
opencode %*

REM Play sound after execution
powershell -c "[console]::beep(800, 1200)"

echo Sound notification played.