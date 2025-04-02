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
            --name UniChat ^
            --noconfirm ^
            --collect-all pydantic ^
            --collect-submodules langchain.chains ^
            --exclude-module pyinstaller,pillow ^
            -i %CD%\resources\icon3.ico ^
            %script%

cd %CD%
rem if exist "dist\unichat\backend" (
rem   rd /S /Q dist\unichat\backend
rem )
rem mkdir dist\unichat\backend
rem if exist "backend\.env" (
rem   copy %CD%\backend\.env %CD%\dist\unichat\backend
rem )
copy %CD%\backend\sta_config.toml %CD%\dist\unichat\backend\sta_config.toml
copy %CD%\backend\factory.toml %CD%\dist\unichat\backend\dyn_config.toml
copy %CD%\backend\factory.toml %CD%\dist\unichat\backend\dyn_config.toml
if exist "dist\unichat\frontend" (
  rd /S /Q dist\unichat\frontend
)
mkdir dist\unichat\frontend && copy frontend\* dist\unichat\frontend
if exist "dist\unichat\resources" (
  rd /S /Q dist\unichat\resources
)
mkdir dist\unichat\resources && copy resources\* dist\unichat\resources
if exist "dist\unichat\local_docs" (
  rd /S /Q dist\unichat\local_docs
)
mkdir dist\unichat\local_docs && copy docs\QA.md dist\unichat\local_docs\QA.md

copy %CD%\README.md %CD%\dist\unichat\README.md
copy %CD%\LICENCE %CD%\dist\unichat\LICENCE
