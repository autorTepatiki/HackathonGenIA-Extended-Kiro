# Load Environment Variables from .env file
# Usage: .\load-env.ps1

$envFile = Join-Path $PSScriptRoot ".env"

if (-not (Test-Path $envFile)) {
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please create a .env file from the template:" -ForegroundColor Yellow
    Write-Host "  1. Copy .env.example to .env" -ForegroundColor Cyan
    Write-Host "     Copy-Item .env.example .env" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2. Edit .env and fill in your actual values" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  3. Run this script again to load the variables" -ForegroundColor Cyan
    Write-Host "     .\load-env.ps1" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

Write-Host "Loading environment variables from .env file..." -ForegroundColor Yellow
Write-Host ""

$loadedCount = 0
Get-Content $envFile | ForEach-Object {
    $line = $_.Trim()
    
    # Skip empty lines and comments
    if ($line -eq "" -or $line.StartsWith("#")) {
        return
    }
    
    # Parse key=value
    if ($line -match '^([^=]+)=(.*)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        
        # Remove quotes if present
        $value = $value -replace '^["'']|["'']$', ''
        
        # Set environment variable
        [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
        
        Write-Host "  ✓ Loaded: $key" -ForegroundColor Green
        $loadedCount++
    }
}

Write-Host ""
Write-Host "Successfully loaded $loadedCount environment variable(s)" -ForegroundColor Green
Write-Host ""
Write-Host "You can now run:" -ForegroundColor Yellow
Write-Host "  .\get-token.ps1    - Get authentication token" -ForegroundColor Cyan
Write-Host "  .\test-api.ps1     - Test all API endpoints" -ForegroundColor Cyan
Write-Host ""
