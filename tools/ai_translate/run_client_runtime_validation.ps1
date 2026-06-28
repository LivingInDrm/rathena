param(
    [string]$ClientExe = "D:\rag\2021-11-03_Ragexe_patched.exe",
    [string]$Output = "tmp\client_runtime_probe.json",
    [int]$WaitSeconds = 20
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$probeScript = Join-Path $PSScriptRoot "probe_client_runtime.py"

if (-not (Test-Path -LiteralPath $ClientExe)) {
    Write-Host "Client executable not found: $ClientExe" -ForegroundColor Red
    exit 2
}

Set-Location $repoRoot

$existing = Get-Process | Where-Object {
    $_.ProcessName -like "*Ragexe*" -or $_.ProcessName -like "*rAthena*"
}

if (-not $existing) {
    Write-Host "Starting client: $ClientExe"
    Start-Process -FilePath $ClientExe -WorkingDirectory (Split-Path -Parent $ClientExe)
} else {
    Write-Host "Client process already running; probing existing instance."
}

Write-Host "Waiting $WaitSeconds seconds before runtime probe..."
Start-Sleep -Seconds $WaitSeconds

python $probeScript --output $Output
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "Runtime probe passed. Output: $Output" -ForegroundColor Green
} else {
    Write-Host "Runtime probe did not pass. Check output: $Output" -ForegroundColor Yellow
}

exit $exitCode
