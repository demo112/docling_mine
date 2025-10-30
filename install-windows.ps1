# Docling Windows安装脚本
# PowerShell脚本用于安装和配置Docling

param(
    [string]$InstallPath = "$env:LOCALAPPDATA\Docling",
    [switch]$AddToPath = $false
)

Write-Host "🚀 Docling Windows安装程序" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green

# 创建安装目录
if (!(Test-Path $InstallPath)) {
    Write-Host "📁 创建安装目录: $InstallPath" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
}

# 检查是否存在可执行文件
$CliExePath = Join-Path $InstallPath "docling-windows.exe"
$UiExePath = Join-Path $InstallPath "docling-ui-windows.exe"

if ((Test-Path $CliExePath) -or (Test-Path $UiExePath)) {
    Write-Host "⚠️  检测到现有安装，将进行覆盖" -ForegroundColor Yellow
}

# 复制文件（假设在当前目录中）
$CurrentDir = Get-Location
$SourceCliExe = Join-Path $CurrentDir "docling-windows.exe"
$SourceUiExe = Join-Path $CurrentDir "docling-ui-windows.exe"
$SourceCliBat = Join-Path $CurrentDir "docling-cli.bat"
$SourceUiBat = Join-Path $CurrentDir "docling-ui.bat"

# 复制CLI应用
if (Test-Path $SourceCliExe) {
    Write-Host "📦 复制CLI可执行文件..." -ForegroundColor Yellow
    Copy-Item $SourceCliExe $InstallPath -Force
} else {
    Write-Host "⚠️  未找到docling-windows.exe文件" -ForegroundColor Yellow
}

# 复制UI应用
if (Test-Path $SourceUiExe) {
    Write-Host "📦 复制UI可执行文件..." -ForegroundColor Yellow
    Copy-Item $SourceUiExe $InstallPath -Force
} else {
    Write-Host "⚠️  未找到docling-ui-windows.exe文件" -ForegroundColor Yellow
}

# 复制批处理文件
if (Test-Path $SourceCliBat) {
    Write-Host "📦 复制CLI批处理文件..." -ForegroundColor Yellow
    Copy-Item $SourceCliBat $InstallPath -Force
}

if (Test-Path $SourceUiBat) {
    Write-Host "📦 复制UI批处理文件..." -ForegroundColor Yellow
    Copy-Item $SourceUiBat $InstallPath -Force
}

# 检查是否至少有一个应用被安装
if (!(Test-Path $CliExePath) -and !(Test-Path $UiExePath)) {
    Write-Host "❌ 未找到任何Docling可执行文件" -ForegroundColor Red
    exit 1
}

# 创建桌面快捷方式
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$WshShell = New-Object -comObject WScript.Shell

# 为CLI应用创建快捷方式
if (Test-Path $CliExePath) {
    $CliShortcutPath = Join-Path $DesktopPath "Docling CLI.lnk"
    $CliShortcut = $WshShell.CreateShortcut($CliShortcutPath)
    $CliShortcut.TargetPath = $CliExePath
    $CliShortcut.WorkingDirectory = $InstallPath
    $CliShortcut.Description = "Docling CLI - 命令行文档处理工具"
    $CliShortcut.Save()
    Write-Host "🔗 创建CLI桌面快捷方式: $CliShortcutPath" -ForegroundColor Green
}

# 为UI应用创建快捷方式
if (Test-Path $UiExePath) {
    $UiShortcutPath = Join-Path $DesktopPath "Docling UI.lnk"
    $UiShortcut = $WshShell.CreateShortcut($UiShortcutPath)
    $UiShortcut.TargetPath = $UiExePath
    $UiShortcut.WorkingDirectory = $InstallPath
    $UiShortcut.Description = "Docling UI - 可视化文档处理工具"
    $UiShortcut.Save()
    Write-Host "🔗 创建UI桌面快捷方式: $UiShortcutPath" -ForegroundColor Green
}

# 添加到PATH（可选）
if ($AddToPath) {
    $CurrentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    if ($CurrentPath -notlike "*$InstallPath*") {
        Write-Host "🔧 添加到用户PATH环境变量..." -ForegroundColor Yellow
        $NewPath = "$CurrentPath;$InstallPath"
        [Environment]::SetEnvironmentVariable("PATH", $NewPath, "User")
        Write-Host "✅ 已添加到PATH，重启命令行后生效" -ForegroundColor Green
    } else {
        Write-Host "ℹ️  PATH中已存在安装目录" -ForegroundColor Blue
    }
}

# 创建卸载脚本
$UninstallScript = @"
# Docling卸载脚本
Write-Host "🗑️  卸载Docling..." -ForegroundColor Yellow

# 删除安装目录
if (Test-Path "$InstallPath") {
    Remove-Item "$InstallPath" -Recurse -Force
    Write-Host "✅ 已删除安装目录" -ForegroundColor Green
}

# 删除桌面快捷方式
`$DesktopPath = [Environment]::GetFolderPath("Desktop")
`$CliShortcutPath = Join-Path `$DesktopPath "Docling CLI.lnk"
`$UiShortcutPath = Join-Path `$DesktopPath "Docling UI.lnk"

if (Test-Path `$CliShortcutPath) {
    Remove-Item `$CliShortcutPath -Force
    Write-Host "✅ 已删除CLI桌面快捷方式" -ForegroundColor Green
}

if (Test-Path `$UiShortcutPath) {
    Remove-Item `$UiShortcutPath -Force
    Write-Host "✅ 已删除UI桌面快捷方式" -ForegroundColor Green
}

# 从PATH中移除（如果存在）
`$CurrentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if (`$CurrentPath -like "*$InstallPath*") {
    `$NewPath = `$CurrentPath -replace [regex]::Escape(";$InstallPath"), ""
    `$NewPath = `$NewPath -replace [regex]::Escape("$InstallPath;"), ""
    `$NewPath = `$NewPath -replace [regex]::Escape("$InstallPath"), ""
    [Environment]::SetEnvironmentVariable("PATH", `$NewPath, "User")
    Write-Host "✅ 已从PATH中移除" -ForegroundColor Green
}

Write-Host "🎉 Docling已成功卸载" -ForegroundColor Green
"@

$UninstallPath = Join-Path $InstallPath "uninstall.ps1"
$UninstallScript | Out-File -FilePath $UninstallPath -Encoding UTF8

Write-Host ""
Write-Host "🎉 安装完成！" -ForegroundColor Green
Write-Host "📍 安装位置: $InstallPath" -ForegroundColor Blue
Write-Host "🗑️  卸载脚本: $UninstallPath" -ForegroundColor Blue
Write-Host ""

if (Test-Path $CliExePath) {
    Write-Host "📱 CLI应用已安装" -ForegroundColor Green
    Write-Host "  命令行: $CliExePath --help" -ForegroundColor White
    Write-Host "  批处理: docling-cli.bat" -ForegroundColor White
    Write-Host "  桌面快捷方式: Docling CLI" -ForegroundColor White
}

if (Test-Path $UiExePath) {
    Write-Host "🖥️  UI应用已安装" -ForegroundColor Green
    Write-Host "  可执行文件: $UiExePath" -ForegroundColor White
    Write-Host "  批处理: docling-ui.bat" -ForegroundColor White
    Write-Host "  桌面快捷方式: Docling UI" -ForegroundColor White
    Write-Host "  注意: UI应用启动后会在浏览器中打开" -ForegroundColor Yellow
}

Write-Host ""

# 测试安装
Write-Host "🧪 测试安装..." -ForegroundColor Yellow

# 测试CLI应用
if (Test-Path $CliExePath) {
    try {
        $CliTestResult = & $CliExePath --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ CLI应用测试成功" -ForegroundColor Green
            Write-Host $CliTestResult -ForegroundColor Gray
        } else {
            Write-Host "⚠️  CLI应用测试失败，但文件已复制" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️  CLI应用测试失败，但文件已复制" -ForegroundColor Yellow
    }
}

# 测试UI应用（只检查文件存在性）
if (Test-Path $UiExePath) {
    Write-Host "✅ UI应用文件已安装" -ForegroundColor Green
    Write-Host "  注意: UI应用需要手动启动，启动后会在浏览器中打开" -ForegroundColor Yellow
}