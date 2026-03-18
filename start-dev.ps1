$ErrorActionPreference = "Stop"

$repoRoot = $PSScriptRoot
$envFile = Join-Path $repoRoot ".env"

function Get-EnvInjectionPrefix {
    param([string]$FilePath)

    if (-not (Test-Path $FilePath)) {
        return ""
    }

    $commands = @()
    Get-Content $FilePath | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) {
            return
        }
        $parts = $line.Split("=", 2)
        if ($parts.Count -ne 2) {
            return
        }
        $key = $parts[0].Trim()
        $value = $parts[1]
        $escaped = $value.Replace("'", "''")
        $commands += "`$env:$key='$escaped'"
    }

    if ($commands.Count -eq 0) {
        return ""
    }

    return ($commands -join "; ") + "; "
}

$envPrefix = Get-EnvInjectionPrefix -FilePath $envFile

$backendCommand = @(
    $envPrefix
    "Set-Location '$repoRoot\backend'; "
    "python -m uvicorn app.main:app --reload"
) -join ""

$frontendCommand = @(
    $envPrefix
    "Set-Location '$repoRoot\frontend'; "
    "npm run dev"
) -join ""

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand

Write-Host "Frontend: http://localhost:3000"
Write-Host "API docs: http://localhost:8000/docs"
