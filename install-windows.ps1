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
$ExePath = Join-Path $InstallPath "docling-windows.exe"
if (Test-Path $ExePath) {
    Write-Host "⚠️  检测到现有安装，将进行覆盖" -ForegroundColor Yellow
}

# 复制文件（假设在当前目录中）
$CurrentDir = Get-Location
$SourceExe = Join-Path $CurrentDir "docling-windows.exe"
$SourceBat = Join-Path $CurrentDir "docling.bat"

if (Test-Path $SourceExe) {
    Write-Host "📦 复制可执行文件..." -ForegroundColor Yellow
    Copy-Item $SourceExe $InstallPath -Force
} else {
    Write-Host "❌ 未找到docling-windows.exe文件" -ForegroundColor Red
    exit 1
}

if (Test-Path $SourceBat) {
    Write-Host "📦 复制批处理文件..." -ForegroundColor Yellow
    Copy-Item $SourceBat $InstallPath -Force
}

# 创建桌面快捷方式
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "Docling.lnk"

$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $ExePath
$Shortcut.WorkingDirectory = $InstallPath
$Shortcut.Description = "Docling - 文档处理工具"
$Shortcut.Save()

Write-Host "🔗 创建桌面快捷方式: $ShortcutPath" -ForegroundColor Green

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
if (Test-Path "$ShortcutPath") {
    Remove-Item "$ShortcutPath" -Force
    Write-Host "✅ 已删除桌面快捷方式" -ForegroundColor Green
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
Write-Host "🖥️  桌面快捷方式: $ShortcutPath" -ForegroundColor Blue
Write-Host "🗑️  卸载脚本: $UninstallPath" -ForegroundColor Blue
Write-Host ""
Write-Host "使用方法:" -ForegroundColor Yellow
Write-Host "  命令行: $ExePath --help" -ForegroundColor White
Write-Host "  或双击桌面快捷方式" -ForegroundColor White
Write-Host ""

# 测试安装
Write-Host "🧪 测试安装..." -ForegroundColor Yellow
try {
    $TestResult = & $ExePath --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 安装测试成功" -ForegroundColor Green
        Write-Host $TestResult -ForegroundColor Gray
    } else {
        Write-Host "⚠️  安装测试失败，但文件已复制" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  无法测试安装，但文件已复制" -ForegroundColor Yellow
}