# 启动后端（使用当前 PATH 中的 Python，不依赖虚拟环境）
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$env:PYTHONPATH = "$root\backend;$root"

$pythonArgs = @("-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--reload", "--host", "127.0.0.1", "--port", "8000")
if (Get-Command python -ErrorAction SilentlyContinue) {
    & python @pythonArgs
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 @pythonArgs
} else {
    throw "未找到 Python。请安装 Python 3 并加入 PATH，或使用 Windows 的 py 启动器。"
}
