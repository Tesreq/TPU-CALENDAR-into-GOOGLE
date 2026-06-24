$ErrorActionPreference = "Stop"

$scriptsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Split-Path -Parent $scriptsDir
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "TPU Calendar Sync.lnk"
$iconPath = Join-Path $projectDir "app\assets\avatar.ico"
$desktopScript = Join-Path $projectDir "scripts\desktop.py"
$pythonwPath = Join-Path $projectDir ".venv\Scripts\pythonw.exe"
$pythonPath = Join-Path $projectDir ".venv\Scripts\python.exe"
$batPath = Join-Path $projectDir "run_desktop.bat"

if (Test-Path $pythonwPath) {
    $targetPath = $pythonwPath
    $arguments = "`"$desktopScript`""
}
elseif (Test-Path $pythonPath) {
    $targetPath = $pythonPath
    $arguments = "`"$desktopScript`""
}
else {
    $targetPath = $batPath
    $arguments = ""
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetPath
$shortcut.Arguments = $arguments
$shortcut.WorkingDirectory = $projectDir
$shortcut.Description = "TPU Calendar Sync"

if (Test-Path $iconPath) {
    $shortcut.IconLocation = $iconPath
}

$shortcut.Save()

Write-Host "Ярлык создан:" $shortcutPath
