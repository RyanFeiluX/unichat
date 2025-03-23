@echo off
@chcp 65001
REM Set the script path
@set script=../unichat/backend/rag-service.py

REM Check if PyInstaller is installed
pyinstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstaller is not installed. Please install it firstly.
    exit /b 1
)

REM Check if the script file exists
if not exist %script% (
    echo Script file %script% not found.
    exit /b 1
)

REM Build all
if "%1%"=="all" (
  rd /S /Q dist
  rd /S /Q build
)

REM Launch pyinstaller
pyinstaller --onedir ^
            --specpath spec ^
            --name unichat ^
            --noconfirm ^
            --collect-all pydantic ^
            --collect-submodules langchain.chains ^
            --exclude-module pyinstaller,pillow ^
            -i %CD%\resources\icon2.ico ^
            %script%

cd %CD%
if exist "dist\unichat\backend" (
  rd /S /Q dist\unichat\backend
)
mkdir dist\unichat\backend
if exist "backend\.env" (
  copy %CD%\backend\.env %CD%\dist\unichat\backend
)
copy %CD%\backend\sta_config.toml %CD%\dist\unichat\backend\sta_config.toml
copy %CD%\backend\factory.toml %CD%\dist\unichat\backend\dyn_config.toml
if exist "dist\unichat\frontend" (
  rd /S /Q dist\unichat\frontend
)
mkdir dist\unichat\frontend && copy frontend\* dist\unichat\frontend
if exist "dist\unichat\docs" (
  rd /S /Q dist\unichat\docs
)
mkdir dist\unichat\docs && copy docs\QA.md dist\unichat\docs\QA.md
