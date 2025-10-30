# Docling 应用打包指南

本指南介绍如何为 Docling 项目创建 macOS 和 Windows 的可执行应用程序。

## 🎯 项目概述

Docling 是一个强大的文档处理工具，支持多种文件格式的转换和处理。本项目已配置了完整的 CI/CD 流程，可以自动构建跨平台的可执行应用程序。

## 📦 支持的平台

- **macOS**: 应用包 (.app) 和 DMG 安装包
- **Windows**: 可执行文件 (.exe) 和 ZIP 压缩包

## 🛠️ 构建系统

### GitHub Actions 自动构建

项目使用 GitHub Actions 进行自动构建，配置文件位于 `.github/workflows/build-apps.yml`。

#### 触发条件
- 推送到 `main` 分支
- 创建标签 (v*)
- 手动触发 (workflow_dispatch)
- Pull Request

#### 构建作业
1. **build-macos**: 在 macOS 环境中构建
2. **build-windows**: 在 Windows 环境中构建  
3. **release**: 发布构建产物（仅在创建标签时）

### 本地构建

#### 环境要求
- Python 3.9+
- PyInstaller
- 项目依赖 (通过 `pip install -e .` 安装)

#### macOS 本地构建
```bash
# 安装依赖
pip install pyinstaller
pip install -e .

# 构建可执行文件
pyinstaller --onefile \
  --name docling-macos \
  --console \
  --collect-all docling \
  --collect-all docling_core \
  --collect-all docling_parse \
  --collect-all docling_ibm_models \
  --add-data "docling:docling" \
  docling/cli/main.py

# 创建应用包
mkdir -p "Docling.app/Contents/MacOS"
mkdir -p "Docling.app/Contents/Resources"
cp dist/docling-macos "Docling.app/Contents/MacOS/docling"

# 创建 Info.plist
# (参见 GitHub Actions 工作流中的完整配置)

# 创建 DMG (需要 create-dmg)
brew install create-dmg
create-dmg --volname "Docling" "Docling-macOS.dmg" "Docling.app"
```

#### Windows 本地构建
```cmd
# 安装依赖
pip install pyinstaller
pip install -e .

# 构建可执行文件
pyinstaller --onefile ^
  --name docling-windows ^
  --console ^
  --collect-all docling ^
  --collect-all docling_core ^
  --collect-all docling_parse ^
  --collect-all docling_ibm_models ^
  --add-data "docling;docling" ^
  docling/cli/main.py

# 创建发布包
mkdir dist-windows
copy dist\\docling-windows.exe dist-windows\\
copy install-windows.ps1 dist-windows\\

# 创建 ZIP 包
powershell Compress-Archive -Path dist-windows\\* -DestinationPath Docling-Windows.zip
```

## 📁 构建产物

### macOS
- `docling-macos`: 命令行可执行文件
- `Docling.app`: macOS 应用包
- `Docling-macOS.dmg`: DMG 安装包

### Windows  
- `docling-windows.exe`: Windows 可执行文件
- `docling.bat`: 批处理包装器
- `install-windows.ps1`: PowerShell 安装脚本
- `Docling-Windows.zip`: 完整发布包

## 🚀 使用方法

### 自动发布流程
1. 确保所有更改已提交到 `main` 分支
2. 创建版本标签:
   ```bash
   git tag v2.58.0
   git push origin v2.58.0
   ```
3. GitHub Actions 将自动构建并发布到 GitHub Releases

### 手动触发构建
1. 访问 GitHub 仓库的 Actions 页面
2. 选择 "Build Applications" 工作流
3. 点击 "Run workflow" 按钮

## 📋 文件说明

### 核心文件
- `.github/workflows/build-apps.yml`: GitHub Actions 工作流配置
- `install-windows.ps1`: Windows 安装脚本
- `docling/cli/main.py`: 应用程序入口点
- `pyproject.toml`: 项目配置和依赖

### 构建配置
- PyInstaller 使用 `--collect-all` 收集所有必需的模块
- `--add-data` 包含数据文件
- `--onefile` 创建单文件可执行程序

## 🔧 故障排除

### 常见问题

1. **模块未找到错误**
   - 确保使用 `--collect-all` 参数
   - 检查隐藏导入是否正确配置

2. **数据文件缺失**
   - 使用 `--add-data` 参数包含必要的数据文件
   - 验证文件路径是否正确

3. **权限问题 (macOS)**
   - 确保可执行文件有执行权限: `chmod +x`
   - 检查应用包结构是否正确

4. **Windows 安全警告**
   - 可执行文件未签名，可能触发安全警告
   - 用户需要选择"仍要运行"或"更多信息" -> "仍要运行"

### 调试技巧

1. **测试构建**
   ```bash
   # 测试可执行文件
   ./dist/docling-macos --version
   ./dist/docling-windows.exe --version
   ```

2. **检查依赖**
   ```bash
   # 列出 PyInstaller 收集的模块
   pyinstaller --collect-all docling --log-level DEBUG docling/cli/main.py
   ```

3. **验证应用包**
   ```bash
   # macOS 应用包结构
   find Docling.app -type f
   
   # 测试应用包
   Docling.app/Contents/MacOS/docling --version
   ```

## 📝 版本信息

- Docling: 2.58.0
- Python: 3.9+
- PyInstaller: 6.16.0+
- 支持的操作系统: macOS 10.15+, Windows 10+

## 🔗 相关链接

- [Docling 项目主页](https://github.com/DS4SD/docling)
- [PyInstaller 文档](https://pyinstaller.readthedocs.io/)
- [GitHub Actions 文档](https://docs.github.com/en/actions)

---

*最后更新: 2024-10-30*