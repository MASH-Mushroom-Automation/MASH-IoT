@echo off
setlocal

:: --- CONFIGURATION ---
set "PROJECT_FOLDER=rpi_gateway"
set "EXCLUDE_FILE=exclude.txt"
set "BUILD_DIR=build"
:: ---------------------

echo ========================================================
echo      RPI GATEWAY RELEASE BUILDER
echo ========================================================
echo.

:: 1. Ask for the version number
set /p VERSION="Enter the release version (e.g., 2.3.1): "

if "%VERSION%"=="" (
    echo Error: You must enter a version number.
    pause
    exit /b
)

:: 2. Create the build directory if it doesn't exist
if not exist "%BUILD_DIR%" (
    mkdir "%BUILD_DIR%"
    echo Created directory: %BUILD_DIR%
)

:: Set the full path for the output file
set "OUTPUT_FILE=%BUILD_DIR%\%PROJECT_FOLDER%-%VERSION%.tar.gz"

:: 3. Check/Create exclude file
if not exist "%EXCLUDE_FILE%" (
    echo Warning: "%EXCLUDE_FILE%" not found! Creating a default one...
    (
        echo venv
        echo __pycache__
        echo *.pyc
        echo .git
        echo .gitignore
        echo .vscode
        echo *.db
        echo test_improvements.py
        echo FIREBASE_CHECKLIST.md
        echo FIREBASE_INTEGRATION_GUIDE.md
        echo FIREBASE_QUICK_START.md
        echo %BUILD_DIR%
        echo build_release.bat
        echo exclude.txt
    ) > "%EXCLUDE_FILE%"
    echo Default "%EXCLUDE_FILE%" created.
)

echo.
echo Packaging "%PROJECT_FOLDER%"...
echo Destination: "%OUTPUT_FILE%"
echo Excluding files listed in "%EXCLUDE_FILE%"...
echo.

:: 4. Run the TAR command
:: We use the -f flag to specify the full output path inside the build folder
tar -czvf "%OUTPUT_FILE%" -X "%EXCLUDE_FILE%" "%PROJECT_FOLDER%"

echo.
if %ERRORLEVEL% EQU 0 (
    echo ========================================================
    echo  SUCCESS! 
    echo  File saved to: %OUTPUT_FILE%
    echo ========================================================
) else (
    echo ========================================================
    echo  FAILED! Something went wrong.
    echo ========================================================
)

pause