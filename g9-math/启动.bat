@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 初三数学 - 本地服务（关掉这个窗口就停止）

where python >nul 2>&1
if %errorlevel%==0 (
    python serve.py
    goto done
)

where py >nul 2>&1
if %errorlevel%==0 (
    py serve.py
    goto done
)

echo.
echo 没找到 Python。请先安装 Python 3（https://www.python.org/downloads/），
echo 安装时勾选 "Add python.exe to PATH"，然后再双击本文件。
echo.

:done
pause
