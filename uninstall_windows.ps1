# Embedding API - Windows 卸载脚本

$TaskName = "EmbedAPI"

Write-Host "=== Embedding API Windows Uninstaller ===" -ForegroundColor Cyan

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($task) {
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Scheduled task '$TaskName' removed." -ForegroundColor Green
} else {
    Write-Host "Task '$TaskName' not found." -ForegroundColor Yellow
}
