"""
项目根目录入口文件
负责导入 Global_Phone_Sentiment/main.py 中定义的 FastAPI app

运行方式（本地）：
    uvicorn main:app --reload

运行方式（Render Start Command）：
    uvicorn main:app --host 0.0.0.0 --port $PORT
"""

from __future__ import annotations

import sys
import importlib.util
from pathlib import Path

# 仓库根目录（这个 main.py 所在目录）
ROOT_DIR = Path(__file__).resolve().parent

# 真正后端代码的位置：Global_Phone_Sentiment/main.py
BACKEND_MAIN_PATH = ROOT_DIR / "Global_Phone_Sentiment" / "main.py"

if not BACKEND_MAIN_PATH.exists():
    raise RuntimeError(f"后端入口文件不存在：{BACKEND_MAIN_PATH}")

# 把项目根目录加到 sys.path，方便内部再去找其它模块/文件
root_str = str(ROOT_DIR)
if root_str not in sys.path:
    sys.path.insert(0, root_str)

# 动态加载 Global_Phone_Sentiment/main.py 模块
# 使用完整的模块名，避免 dataclass 在动态导入时找不到 __module__
module_name = "Global_Phone_Sentiment.main"
spec = importlib.util.spec_from_file_location(
    module_name, BACKEND_MAIN_PATH
)
if spec is None or spec.loader is None:
    raise RuntimeError(f"无法从 {BACKEND_MAIN_PATH} 创建模块加载 spec")

# 创建模块并添加到 sys.modules，这样 dataclass 装饰器可以正确找到模块
module = importlib.util.module_from_spec(spec)
sys.modules[module_name] = module

# 设置模块的文件路径和包路径，确保 dataclass 能正常工作
module.__file__ = str(BACKEND_MAIN_PATH)
module.__package__ = "Global_Phone_Sentiment"

# 执行模块代码
spec.loader.exec_module(module)  # type: ignore[arg-type]

# 拿到 FastAPI app 实例
app = module.app

# 对外导出 app
__all__ = ["app"]
