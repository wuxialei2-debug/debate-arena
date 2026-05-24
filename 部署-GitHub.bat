@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   AI思想家辩论场 — 一键部署
echo ========================================
echo.

:: Step 0: 确保 gh 在 PATH 中
set "GH=C:\Program Files\GitHub CLI\gh.exe"
if not exist "%GH%" (
    echo [0/3] 正在安装 GitHub CLI...
    winget install --id GitHub.cli --accept-source-agreements --accept-package-agreements
    if not exist "%GH%" (
        echo 安装失败，请手动下载: https://cli.github.com/
        echo 安装后重新双击此脚本
        pause
        exit /b 1
    )
)
set "PATH=%PATH%;C:\Program Files\GitHub CLI"

echo.
echo [1/3] 登录 GitHub...
echo 即将弹出浏览器，请点击蓝色的 "Authorize github" 按钮
gh auth login --hostname github.com --web --git-protocol https
if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo   登录失败！改为手动方式：
    echo   1. 打开 https://github.com/settings/tokens
    echo   2. 点 "Generate new token (classic)"
    echo   3. 勾选 repo、read:org 两个权限
    echo   4. 生成后复制 token 粘贴到下方
    echo ========================================
    echo.
    set /p TOKEN="粘贴你的 GitHub Token: "
    echo !TOKEN!| gh auth login --hostname github.com --git-protocol https --with-token
    if !errorlevel! neq 0 (
        echo Token 登录也失败了，请检查后重试
        pause
        exit /b 1
    )
)

echo.
echo [2/3] 创建仓库并推送...
gh repo create debate-arena --public --source=. --push --description "AI思想家辩论场"
if %errorlevel% neq 0 (
    echo 远程仓库可能已存在，尝试直接推送...
    git remote remove origin 2>nul
    git remote add origin https://github.com/wuxialei2-debug/debate-arena.git
    git push -u origin main
)

echo.
echo [3/3] 开启 GitHub Pages...
gh api -X POST "repos/wuxialei2-debug/debate-arena/pages" -f "source[branch]=main" -f "source[path]=/" 2>nul
if %errorlevel% neq 0 (
    echo Pages 可能已开启，请在网页上手动操作：
    echo   https://github.com/wuxialei2-debug/debate-arena/settings/pages
    echo   Source 选 "Deploy from a branch"
    echo   Branch 选 "main" 保存
)

echo.
echo ========================================
echo   完成！
echo.
echo   你的公网链接：
echo   https://wuxialei2-debug.github.io/debate-arena/
echo.
echo   如果打不开，等 1-2 分钟刷新
echo ========================================

pause
