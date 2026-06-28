param(
    [string]$ClientExe = "D:\rag\2021-11-03_Ragexe_patched.exe",
    [string]$Output = "tmp\client_runtime_probe.json",
    [int]$WaitSeconds = 20,
    [int]$StartTimeoutSeconds = 5,
    [switch]$AutoStart,
    [switch]$NoStart,
    [string]$PythonExe = "python"
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
    if ($NoStart -or -not $AutoStart) {
        Write-Host "No client process detected; start the client manually or rerun with -AutoStart." -ForegroundColor Yellow
    } else {
        Write-Host "Starting client: $ClientExe"
        $clientDir = Split-Path -Parent $ClientExe
        $launchJob = Start-Job -ScriptBlock {
            param($ExePath, $WorkingDirectory)
            Start-Process -FilePath $ExePath -WorkingDirectory $WorkingDirectory
        } -ArgumentList $ClientExe, $clientDir

        $completedJob = Wait-Job -Job $launchJob -Timeout $StartTimeoutSeconds
        if ($completedJob) {
            Receive-Job -Job $launchJob | Out-Null
        } else {
            Stop-Job -Job $launchJob -ErrorAction SilentlyContinue
            Write-Host "Client auto-start did not finish within $StartTimeoutSeconds seconds; continue probing or start it manually." -ForegroundColor Yellow
        }
        Remove-Job -Job $launchJob -Force -ErrorAction SilentlyContinue
    }
} else {
    Write-Host "Client process already running; probing existing instance."
}

if ($WaitSeconds -gt 0) {
    Write-Host "Waiting $WaitSeconds seconds before runtime probe..."
    Start-Sleep -Seconds $WaitSeconds
}

& $PythonExe $probeScript --output $Output
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "Runtime probe passed. Output: $Output" -ForegroundColor Green
} else {
    Write-Host "Runtime probe did not pass. Check output: $Output" -ForegroundColor Yellow
}

exit $exitCode
