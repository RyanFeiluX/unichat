@echo off
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
            --exclude-module pyinstaller ^
            --add-data "%CD%\dist\unichat\frontend:frontend" ^
            %script%

cd %CD% && copy %CD%\backend\.env %CD%\dist\unichat\.env
if exist "dist\unichat\frontend" (
  rd /S /Q dist\unichat\frontend
)
mkdir dist\unichat\frontend && copy frontend\* dist\unichat\frontend
if exist "dist\unichat\docs" (
  rd /S /Q dist\unichat\docs
)
mkdir dist\unichat\docs && copy docs\* dist\unichat\docs
