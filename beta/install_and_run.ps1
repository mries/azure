# LogShell — Windows PowerShell launcher
# Run this script once to install deps, then use logshell.py directly.

Write-Host "LogShell Setup" -ForegroundColor Cyan

# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python not found. Please install from https://python.org" -ForegroundColor Red
    exit 1
}

Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install rich prompt_toolkit

Write-Host ""
Write-Host "Done! Usage examples:" -ForegroundColor Green
Write-Host "  python logshell.py                       # start shell in current dir"
Write-Host "  python logshell.py logs.tar.gz           # extract and enter archive"
Write-Host "  python logshell.py support_bundle.tar.xz # same for .tar.xz"
Write-Host ""

# If an argument was passed to this script, forward it
if ($args.Count -gt 0) {
    python logshell.py $args[0]
} else {
    python logshell.py
}
