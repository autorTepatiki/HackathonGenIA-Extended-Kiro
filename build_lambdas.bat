@echo off
REM Build script for Lambda deployment packages (Windows)
REM This script creates deployment packages for both Lambda functions

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   Lambda Deployment Package Builder
echo ============================================================
echo.

REM Get script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Define directories
set "SRC_DIR=%SCRIPT_DIR%src"
set "INFRA_DIR=%SCRIPT_DIR%infra"

REM Create infra directory if it doesn't exist
if not exist "%INFRA_DIR%" mkdir "%INFRA_DIR%"

REM Initialize counters
set SUCCESS_COUNT=0
set TOTAL_COUNT=2

REM Build Authorizer Lambda
call :build_lambda "authorizer" "%SRC_DIR%\authorizer"
if !ERRORLEVEL! equ 0 set /a SUCCESS_COUNT+=1

REM Build Customer CRUD Lambda
call :build_lambda "crud" "%SRC_DIR%\customers"
if !ERRORLEVEL! equ 0 set /a SUCCESS_COUNT+=1

REM Print summary
echo.
echo ============================================================
echo   Build Summary
echo ============================================================
echo.
echo Total packages: %TOTAL_COUNT%
echo Successful: %SUCCESS_COUNT%
set /a FAILED_COUNT=%TOTAL_COUNT%-%SUCCESS_COUNT%
echo Failed: %FAILED_COUNT%
echo.

if %SUCCESS_COUNT% equ %TOTAL_COUNT% (
    echo [SUCCESS] All Lambda packages built successfully!
    echo.
    echo Deployment packages are ready in: %INFRA_DIR%
    echo.
    echo Next steps:
    echo   1. cd infra
    echo   2. terraform init
    echo   3. terraform plan
    echo   4. terraform apply
    exit /b 0
) else (
    echo [ERROR] Some packages failed to build. Please check the errors above.
    exit /b 1
)

:build_lambda
set "LAMBDA_NAME=%~1"
set "SOURCE_DIR=%~2"
set "OUTPUT_FILE=%INFRA_DIR%\%LAMBDA_NAME%.zip"

echo.
echo ============================================================
echo   Building %LAMBDA_NAME% Lambda package
echo ============================================================
echo.

REM Check if source directory exists
if not exist "%SOURCE_DIR%" (
    echo [ERROR] Source directory not found: %SOURCE_DIR%
    exit /b 1
)

REM Check if requirements.txt exists
if not exist "%SOURCE_DIR%\requirements.txt" (
    echo [ERROR] requirements.txt not found in %SOURCE_DIR%
    exit /b 1
)

REM Create temporary build directory
set "BUILD_DIR=%TEMP%\lambda_build_%LAMBDA_NAME%_%RANDOM%"
mkdir "%BUILD_DIR%"

echo Installing dependencies...

REM Install dependencies
python -m pip install -r "%SOURCE_DIR%\requirements.txt" -t "%BUILD_DIR%" --quiet
if !ERRORLEVEL! neq 0 (
    echo [ERROR] Failed to install dependencies
    rmdir /s /q "%BUILD_DIR%"
    exit /b 1
)
echo [OK] Dependencies installed

REM Copy Lambda source files
echo Copying Lambda source files...
copy "%SOURCE_DIR%\*.py" "%BUILD_DIR%\" >nul
if !ERRORLEVEL! neq 0 (
    echo [ERROR] Failed to copy source files
    rmdir /s /q "%BUILD_DIR%"
    exit /b 1
)

REM Create zip file
echo Creating deployment package...

REM Remove old zip if exists
if exist "%OUTPUT_FILE%" del /f "%OUTPUT_FILE%"

REM Use PowerShell to create zip (available on Windows 10+)
powershell -Command "Compress-Archive -Path '%BUILD_DIR%\*' -DestinationPath '%OUTPUT_FILE%' -Force"
if !ERRORLEVEL! neq 0 (
    echo [ERROR] Failed to create zip file
    rmdir /s /q "%BUILD_DIR%"
    exit /b 1
)

REM Get file size
for %%A in ("%OUTPUT_FILE%") do set SIZE=%%~zA
set /a SIZE_MB=!SIZE! / 1048576
echo [OK] Package created: %LAMBDA_NAME%.zip (!SIZE_MB! MB)

REM Cleanup
rmdir /s /q "%BUILD_DIR%"

exit /b 0
