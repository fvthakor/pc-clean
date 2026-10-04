# ========================================================
# PcClean Local Verification & Pre-Commit Script
# Runs tests, linting, formatting check, and security audit
# ========================================================

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " Running PcClean Verification Suite" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# 1. Ruff Linting
Write-Host "`n[1/4] Running Ruff Lint Check..." -ForegroundColor Yellow
ruff check .
if ($LASTEXITCODE -ne 0) {
    Write-Error "Ruff lint check failed. Fix errors using 'ruff check --fix .'"
    exit $LASTEXITCODE
}
Write-Host "Lint check passed." -ForegroundColor Green

# 2. Ruff Format Check
Write-Host "`n[2/4] Running Ruff Format Check..." -ForegroundColor Yellow
ruff format --check .
if ($LASTEXITCODE -ne 0) {
    Write-Error "Ruff formatting check failed. Run 'ruff format .' to apply formatting."
    exit $LASTEXITCODE
}
Write-Host "Format check passed." -ForegroundColor Green

# 3. Pytest with Coverage
Write-Host "`n[3/4] Running Pytest Suite with Coverage..." -ForegroundColor Yellow
python -m pytest tests/ --cov=app --cov=services --cov=models --cov=utils --cov=pcclean --cov-report=term
if ($LASTEXITCODE -ne 0) {
    Write-Error "Test suite failed."
    exit $LASTEXITCODE
}
Write-Host "All tests passed." -ForegroundColor Green

# 4. Bandit Security Check
Write-Host "`n[4/4] Running Bandit Security Scan..." -ForegroundColor Yellow
bandit -r app/ services/ utils/ pcclean/ -ll -x tests/
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Bandit reported warnings or issues."
} else {
    Write-Host "Security scan passed clean." -ForegroundColor Green
}

Write-Host "`n========================================================" -ForegroundColor Green
Write-Host " All checks passed! Ready for commit/PR." -ForegroundColor Green
Write-Host "========================================================`n" -ForegroundColor Green
