# Netlify 快速部署脚本
# 使用方法：在 netlify-deploy 文件夹内运行此脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Netlify 部署文件准备工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查当前目录
$currentDir = Get-Location
if (-not (Test-Path "index.html")) {
    Write-Host "❌ 错误：请在 netlify-deploy 文件夹内运行此脚本！" -ForegroundColor Red
    Write-Host "当前目录：$currentDir" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ 检测到 netlify-deploy 文件夹" -ForegroundColor Green
Write-Host ""

# 检查必要文件
$requiredFiles = @("index.html", "netlify.toml")
$missingFiles = @()

foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "❌ 缺少必要文件：" -ForegroundColor Red
    foreach ($file in $missingFiles) {
        Write-Host "   - $file" -ForegroundColor Red
    }
    exit 1
}

Write-Host "✅ 所有必要文件已存在" -ForegroundColor Green
Write-Host ""

# 创建 ZIP 文件
$zipPath = Join-Path (Split-Path $currentDir) "netlify-deploy.zip"

Write-Host "正在创建 ZIP 文件..." -ForegroundColor Yellow
try {
    # 删除旧的 ZIP 文件（如果存在）
    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }
    
    # 压缩当前目录的所有文件
    Compress-Archive -Path * -DestinationPath $zipPath -Force
    
    Write-Host "✅ ZIP 文件创建成功！" -ForegroundColor Green
    Write-Host "   位置：$zipPath" -ForegroundColor Cyan
    Write-Host ""
    
    # 显示文件大小
    $zipSize = (Get-Item $zipPath).Length / 1MB
    Write-Host "   大小：$([math]::Round($zipSize, 2)) MB" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "下一步操作：" -ForegroundColor Cyan
    Write-Host "1. 登录 Netlify: https://app.netlify.com" -ForegroundColor Yellow
    Write-Host "2. 进入你的站点 → Deploys 标签" -ForegroundColor Yellow
    Write-Host "3. 点击 'Trigger deploy' → 'Deploy site'" -ForegroundColor Yellow
    Write-Host "4. 选择 'Deploy manually'" -ForegroundColor Yellow
    Write-Host "5. 上传这个 ZIP 文件：$zipPath" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ 创建 ZIP 文件失败：" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

