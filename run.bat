@echo off
cd /d "%~dp0"

if exist config.env (
    for /f "usebackq tokens=1,* delims==" %%a in ("config.env") do (
        set "line=%%a"
        if not "!line:~0,1!"=="#" (
            if not "%%a"=="" set "%%a=%%b"
        )
    )
)

if exist .venv\Scripts\python.exe (
    echo Using virtual environment
    .venv\Scripts\python.exe main.py
) else (
    echo Using system Python
    python main.py
)
