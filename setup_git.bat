@echo off
echo Setting up Git repository for disc-render...

REM Check if git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Git is not installed or not in PATH
    echo Please install Git from https://git-scm.com/
    pause
    exit /b 1
)

REM Initialize git repository
echo Initializing git repository...
git init

REM Add remote origin
echo Adding remote origin...
git remote add origin https://github.com/GrenJoy/disc-render.git

REM Add all files
echo Adding all files...
git add .

REM Make initial commit
echo Making initial commit...
git commit -m "Initial commit: Fix deployment compatibility issues"

REM Set upstream branch
echo Setting upstream branch...
git branch -M main
git push -u origin main

echo Git repository setup complete!
echo You can now use: git push origin main
pause
