# Embedding API - Windows 安装脚本
# 以管理员权限运行: Right-click -> Run with PowerShell (Admin)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TaskName = "EmbedAPI"
$VenvPython = Join-Path $ScriptDir ".venv\Scripts\python.exe"
$SystemPython = "python"
$MainScript = Join-Path $ScriptDir "main.py"

Write-Host "=== Embedding API Windows Installer ===" -ForegroundColor Cyan

# 创建虚拟环境（如果不存在）
if (-not (Test-Path (Join-Path $ScriptDir ".venv"))) {
    Write-Host "Creating virtual environment..."
    & $SystemPython -m venv (Join-Path $ScriptDir ".venv")
    & $VenvPython -m pip install -r (Join-Path $ScriptDir "requirements.txt")
}

$PythonExe = if (Test-Path $VenvPython) { $VenvPython } else { $SystemPython }

# 加载配置
$Port = "8786"
$ConfigFile = Join-Path $ScriptDir "config.env"
if (Test-Path $ConfigFile) {
    Get-Content $ConfigFile | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
            [Environment]::SetEnvironmentVariable($Matches[1].Trim(), $Matches[2].Trim(), "Process")
            if ($Matches[1].Trim() -eq "EMBED_PORT") { $Port = $Matches[2].Trim() }
        }
    }
}

# 删除旧的计划任务
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Removing existing scheduled task..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# 创建计划任务（开机自启）
Write-Host "Creating scheduled task for auto-start..."
$Action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument $MainScript `
    -WorkingDirectory $ScriptDir

$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -RestartCount 3 `
    -ExecutionTimeLimit (New-TimeSpan -Days 365)

$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Embedding API Service on port $Port"

# 立即启动
Write-Host "Starting service..."
Start-ScheduledTask -TaskName $TaskName

Start-Sleep -Seconds 3

# 验证
try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 10
    Write-Host "`nService is running!" -ForegroundColor Green
    Write-Host "  Health: $($response.status)"
    Write-Host "  Model:  $($response.model)"
} catch {
    Write-Host "`nService may still be loading (first run downloads the model)." -ForegroundColor Yellow
    Write-Host "  Check: http://127.0.0.1:$Port/health"
}

Write-Host "`n--- Management ---"
Write-Host "  Status:  Get-ScheduledTask -TaskName $TaskName"
Write-Host "  Stop:    Stop-ScheduledTask -TaskName $TaskName"
Write-Host "  Start:   Start-ScheduledTask -TaskName $TaskName"
Write-Host "  Remove:  .\uninstall_windows.ps1"
