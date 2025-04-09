@echo off
@chcp 65001
REM Set the script path
@set script=../unichat/backend/http_server.py

@setlocal enabledelayedexpansion

REM Check if PyInstaller is installed
pyinstaller --version >nul 2>&1
if !errorlevel! neq 0 (
    echo PyInstaller is not installed. Please install it firstly.
    exit /b 1
)

@cls

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

pyivf-make_version --source-format yaml --metadata-source metadata.yml --outfile version_info.txt

set cenv_root="d:\programdata\anaconda3\envs\condaenv-unichat"

REM Launch pyinstaller
pyinstaller --onedir ^
            --specpath spec ^
            --name UniChat ^
            --noconfirm ^
            --add-binary "%cenv_root%\Scripts\pandoc.exe:bin" ^
            --collect-submodules pydantic ^
            --collect-submodules langchain.chains ^
            --exclude-module pyinstaller ^
            --exclude-module pillow ^
            --icon %CD%\resources\icon3.ico ^
            --version-file %CD%\version_info.txt ^
            %script%

cd %CD%
if exist "dist\unichat\backend" (
  rd /S /Q dist\unichat\backend
)
mkdir dist\unichat\backend
rem if exist "backend\.env" (
rem   copy %CD%\backend\.env %CD%\dist\unichat\backend
rem )
copy %CD%\backend\sta_config.toml %CD%\dist\unichat\backend
copy %CD%\backend\dyn_config.toml %CD%\dist\unichat\backend
copy %CD%\backend\factory.toml %CD%\dist\unichat\backend
python reset_config.py --dynamic-config %CD%\dist\unichat\backend\dyn_config.toml ^
                       --factory-config %CD%\dist\unichat\backend\factory.toml

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
mkdir dist\unichat\local_docs && copy docs\QA.md dist\unichat\local_docs

copy %CD%\enduser_manual.md %CD%\dist\unichat
copy %CD%\终端用户手册.md %CD%\dist\unichat
copy %CD%\LICENSE %CD%\dist\unichat
copy %CD%\metadata.yml %CD%\dist\unichat
