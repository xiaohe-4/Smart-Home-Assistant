# 智家能一键启动：准备环境、打开后端和前端，并打开浏览器。
param(
    [switch]$Check
)

$ErrorActionPreference = "Stop"

function Get-ProjectRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

function Test-TcpPort {
    param([int]$Port)
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $task = $client.ConnectAsync("127.0.0.1", $Port)
        if (-not $task.Wait(400)) {
            return $false
        }
        return $task.IsCompleted -and -not $task.IsFaulted
    } catch {
        return $false
    } finally {
        try { $client.Dispose() } catch { }
    }
}

function Get-Py3Executable {
    # 不从控制台读取路径。用户名含中文时，控制台代码页会把 sys.executable 读坏。
    $outFile = Join-Path $env:TEMP "zhijia-py-path.txt"
    $previous = $env:ZHIJIA_PY_OUT
    try {
        if (Test-Path -LiteralPath $outFile) {
            Remove-Item -LiteralPath $outFile -Force
        }
        $env:ZHIJIA_PY_OUT = $outFile
        & py -3 -c "import os,sys; open(os.environ['ZHIJIA_PY_OUT'],'w',encoding='utf-8').write(sys.executable)" 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $outFile)) {
            return $null
        }
        $exe = [System.IO.File]::ReadAllText($outFile, (New-Object System.Text.UTF8Encoding $false)).Trim()
        if ($exe -and (Test-Path -LiteralPath $exe)) {
            return $exe
        }
        return $null
    } catch {
        return $null
    } finally {
        if ($null -eq $previous) {
            Remove-Item Env:ZHIJIA_PY_OUT -ErrorAction SilentlyContinue
        } else {
            $env:ZHIJIA_PY_OUT = $previous
        }
        if (Test-Path -LiteralPath $outFile) {
            Remove-Item -LiteralPath $outFile -Force -ErrorAction SilentlyContinue
        }
    }
}

function Test-AppImports {
    param([string]$Exe)
    $previous = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $Exe -c "import fastapi, uvicorn, sqlalchemy" 2>$null | Out-Null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    } finally {
        $ErrorActionPreference = $previous
    }
}

function Resolve-Python {
    param([string]$Root)

    $candidates = New-Object System.Collections.Generic.List[string]
    $venv = Join-Path $Root ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $venv) {
        $candidates.Add((Resolve-Path -LiteralPath $venv).Path)
    }
    $py3 = Get-Py3Executable
    if ($py3) {
        $candidates.Add($py3)
    }
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd -and $pythonCmd.Source -and (Test-Path -LiteralPath $pythonCmd.Source)) {
        $candidates.Add($pythonCmd.Source)
    }

    $ordered = @($candidates | Select-Object -Unique)
    foreach ($exe in $ordered) {
        if (Test-AppImports $exe) {
            return $exe
        }
    }

    $target = $ordered | Select-Object -First 1
    if (-not $target) {
        throw "未找到 Python。请安装 Python 3.10 及以上，并确认 py 或 python 可用。"
    }

    Write-Host "[准备] 正在安装 Python 依赖，请稍候..." -ForegroundColor Yellow
    & $target -m pip install -r (Join-Path $Root "backend\requirements.txt")
    if ($LASTEXITCODE -ne 0) {
        throw "Python 依赖安装失败。可查看上方 pip 输出。"
    }
    if (-not (Test-AppImports $target)) {
        throw "依赖安装后仍无法导入 fastapi / uvicorn。请检查 Python 环境。"
    }
    return $target
}

function Resolve-Npm {
    $npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if ($npm -and $npm.Source) {
        return $npm.Source
    }
    throw "未找到 npm。请安装 Node.js 18 及以上，并重新打开此脚本。"
}

function Start-DevWindow {
    param(
        [string]$Title,
        [string]$Command
    )
    $arg = "title $Title & $Command"
    Start-Process -FilePath "$env:SystemRoot\System32\cmd.exe" -ArgumentList @("/k", $arg) | Out-Null
}

function Wait-Ports {
    param([int]$Seconds = 45)
    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        $backendUp = Test-TcpPort 8000
        $frontendUp = Test-TcpPort 5174
        if ($backendUp -and $frontendUp) {
            return $true
        }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

try {
    $root = Get-ProjectRoot
    Set-Location $root
    try {
        $Host.UI.RawUI.WindowTitle = "智家能一键启动"
    } catch {
        # 非交互宿主没有窗口标题，忽略即可。
    }

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  智家能  一键启动" -ForegroundColor Cyan
    Write-Host "  前端  http://127.0.0.1:5174/" -ForegroundColor Cyan
    Write-Host "  接口  http://127.0.0.1:8000/docs" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    $python = Resolve-Python $root
    $npm = Resolve-Npm
    $db = Join-Path $root "data\smart_energy.db"
    $model = Join-Path $root "models\forecast.joblib"
    $nodeModules = Join-Path $root "frontend\node_modules"
    $needBootstrap = -not (Test-Path $db)
    $needTrain = (Test-Path $db) -and -not (Test-Path $model)
    $needNpm = -not (Test-Path $nodeModules)
    $backendUp = Test-TcpPort 8000
    $frontendUp = Test-TcpPort 5174

    Write-Host "[Python] $python"
    Write-Host "[npm]    $npm"
    if ($needBootstrap) {
        Write-Host "[数据]   还没有数据库，启动前会生成演示数据并训练模型"
    } elseif ($needTrain) {
        Write-Host "[模型]   还没有 forecast.joblib，启动前会训练模型"
    } else {
        Write-Host "[数据]   数据库和模型已就绪"
    }
    if ($backendUp) {
        Write-Host "[后端]   8000 端口已在监听，不再重复启动"
    }
    if ($frontendUp) {
        Write-Host "[前端]   5174 端口已在监听，不再重复启动"
    }

    if ($Check) {
        Write-Host ""
        Write-Host "检查完成，未启动服务。" -ForegroundColor Green
        exit 0
    }

    if ($needNpm) {
        Write-Host "[准备] 正在安装前端依赖..." -ForegroundColor Yellow
        & $npm install --prefix (Join-Path $root "frontend")
        if ($LASTEXITCODE -ne 0) {
            throw "npm install 失败。"
        }
    }

    if ($needBootstrap) {
        Write-Host "[准备] 首次运行：生成数据、入库并训练模型。这一步只需一次，可能要几分钟。" -ForegroundColor Yellow
        & $python (Join-Path $root "scripts\bootstrap.py")
        if ($LASTEXITCODE -ne 0) {
            throw "数据初始化失败。请查看上方输出。"
        }
    } elseif ($needTrain) {
        Write-Host "[准备] 正在训练模型..." -ForegroundColor Yellow
        & $python (Join-Path $root "scripts\train_models.py")
        if ($LASTEXITCODE -ne 0) {
            throw "模型训练失败。请查看上方输出。"
        }
    }

    if (-not $backendUp) {
        Write-Host "[启动] 后端窗口  http://127.0.0.1:8000/docs"
        $backendCmd = "cd /d `"$root`" & set `"PYTHONPATH=$root\backend;$root`" & `"$python`" -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000"
        Start-DevWindow "智家能-后端" $backendCmd
    }

    if (-not $frontendUp) {
        Write-Host "[启动] 前端窗口  http://127.0.0.1:5174/"
        $frontend = Join-Path $root "frontend"
        $frontendCmd = "cd /d `"$frontend`" & call npm run dev"
        Start-DevWindow "智家能-前端" $frontendCmd
    }

    Write-Host "[等待] 服务就绪后打开浏览器..."
    $ready = Wait-Ports 60
    Start-Process "http://127.0.0.1:5174/" | Out-Null

    Write-Host ""
    if ($ready) {
        Write-Host "已打开浏览器。" -ForegroundColor Green
    } else {
        Write-Host "等待超过 60 秒，仍尝试打开了浏览器。" -ForegroundColor Yellow
        Write-Host "如果页面打不开，请看「智家能-后端」和「智家能-前端」窗口里的报错，然后刷新。" -ForegroundColor Yellow
    }
    Write-Host "关闭那两个窗口即停止服务。关闭本窗口不会停止服务。"
    Write-Host "家庭说明页： http://127.0.0.1:5174/guide"
    exit 0
} catch {
    Write-Host ""
    Write-Host "[错误] $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
