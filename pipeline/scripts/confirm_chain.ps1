# Apply the verified solution repairs, then confirm them with the independent
# checker (question text + solution, as the app compiles them) on 4 workers at
# below-normal priority, then regenerate the old-solution report.
# Usage (repo root): powershell -ExecutionPolicy Bypass -File pipeline/scripts/confirm_chain.ps1
param([switch]$SkipApply)
$ErrorActionPreference = "Continue"
$py = ".venv\Scripts\python.exe"
$log = "pipeline/confirm.log"

function Run-Step($label, $argList) {
    "=== $label  $(Get-Date -Format 'HH:mm:ss')" | Out-File -Append -Encoding utf8 $log
    $p = Start-Process -FilePath $py -ArgumentList $argList -RedirectStandardOutput "pipeline/confirm_step.out" -RedirectStandardError "pipeline/confirm_step.err" -PassThru -NoNewWindow
    try { $p.PriorityClass = 'BelowNormal' } catch {}
    $null = $p.Handle  # PowerShell 5.1: without this ExitCode comes back null after the process ends
    Start-Sleep -Seconds 2
    Get-Process python* -ErrorAction SilentlyContinue | ForEach-Object { try { $_.PriorityClass = 'BelowNormal' } catch {} }
    $p.WaitForExit()
    Get-Content "pipeline/confirm_step.out" | Out-File -Append -Encoding utf8 $log
    $err = Get-Content "pipeline/confirm_step.err"
    if ($err) { "--- stderr:" | Out-File -Append -Encoding utf8 $log; $err | Select-Object -Last 20 | Out-File -Append -Encoding utf8 $log }
    $code = $p.ExitCode
    if ($null -eq $code) { $code = 0 }
    "exit $code" | Out-File -Append -Encoding utf8 $log
    return $code
}

"START $(Get-Date)" | Out-File -Encoding utf8 $log
if (-not $SkipApply) {
    $rc = Run-Step "apply" @("pipeline/scripts/fix_old_solutions.py", "apply")
    if ($rc -ne 0) { "ABORT: apply failed" | Out-File -Append -Encoding utf8 $log; exit 1 }
} else {
    "apply skipped (already applied)" | Out-File -Append -Encoding utf8 $log
}

$rc = Run-Step "confirm (drop fixed rows from the check CSV)" @("pipeline/scripts/confirm_fixed_solutions.py")
if ($rc -ne 0) { "ABORT: confirm failed" | Out-File -Append -Encoding utf8 $log; exit 1 }
$ids = (Get-Content "pipeline/confirm_step.out" | Select-Object -Last 1)

$rc = Run-Step "check_old_solutions on the fixed ids, 4 workers" @("pipeline/scripts/check_old_solutions.py", "--ids", $ids, "--workers", "4")
$rc = Run-Step "report_old_solutions" @("pipeline/scripts/report_old_solutions.py")
"DONE $(Get-Date)" | Out-File -Append -Encoding utf8 $log
