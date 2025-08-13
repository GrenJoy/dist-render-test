Write-Host "Setting up Git repository for disc-render..." -ForegroundColor Green

# Check if git is installed
try {
    $gitVersion = git --version
    Write-Host "Git version: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "Git is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Git from https://git-scm.com/" -ForegroundColor Yellow
    Read-Host "Press Enter to continue..."
    exit 1
}

# Initialize git repository
Write-Host "Initializing git repository..." -ForegroundColor Yellow
git init

# Add remote origin
Write-Host "Adding remote origin..." -ForegroundColor Yellow
git remote add origin https://github.com/GrenJoy/disc-render.git

# Add all files
Write-Host "Adding all files..." -ForegroundColor Yellow
git add .

# Make initial commit
Write-Host "Making initial commit..." -ForegroundColor Yellow
git commit -m "Initial commit: Fix deployment compatibility issues"

# Set upstream branch
Write-Host "Setting upstream branch..." -ForegroundColor Yellow
git branch -M main
git push -u origin main

Write-Host "Git repository setup complete!" -ForegroundColor Green
Write-Host "You can now use: git push origin main" -ForegroundColor Cyan
Read-Host "Press Enter to continue..."
