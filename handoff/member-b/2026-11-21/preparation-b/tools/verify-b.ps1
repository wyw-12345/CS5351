param([switch]$Integrated, [switch]$AuditDependencies)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$priorLocation = Get-Location
$priorGit = $env:GIT_BIN
$verificationFailed = $false
try {
    Set-Location -LiteralPath $taskRoot
    $pythonExe = Join-Path $taskRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $pythonExe)) {
        $candidates = @(
            (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'),
            (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe')
        )
        $bootstrapPython = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
        if (-not $bootstrapPython) { throw 'Python 3.12 is required. Create .venv with your Python 3.12 installation first.' }
        & $bootstrapPython -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
        & $pythonExe -m pip install -r requirements-ci.txt
        if ($LASTEXITCODE -ne 0) { throw 'Pinned dependency installation failed.' }
    }
    $bundledGit = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe'
    if (Test-Path -LiteralPath $bundledGit) { $env:GIT_BIN = $bundledGit }
    $checks = @(
        @('-m', 'ruff', 'check', '.'),
        @('-m', 'mypy', 'tools'),
        @('-m', 'pip', 'check'),
        @('tools/check_suite.py', 'test/governance'),
        @('tools/gates.py', 'proposal'),
        @('tools/mutation_check.py')
    )
    if ($AuditDependencies) { $checks += ,@('-m', 'pip_audit', '-r', 'requirements-ci.txt') }
    if ($Integrated) {
        $checks += ,@('tools/gates.py', 'readiness')
        $checks += ,@('tools/gates.py', 'schema')
        $checks += ,@('tools/run_full.py')
    }
    foreach ($arguments in $checks) {
        Write-Output ('RUN ' + ($arguments -join ' '))
        & $pythonExe @arguments
        if ($LASTEXITCODE -ne 0) { $verificationFailed = $true }
    }
    if (-not $Integrated) { Write-Output 'Preparation checks only; application acceptance remains pending.' }
} finally {
    Set-Location -LiteralPath $priorLocation
    $env:GIT_BIN = $priorGit
}
if ($verificationFailed) { exit 1 }
exit 0
