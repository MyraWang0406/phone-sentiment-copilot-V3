# Deta Space 部署命令清单

## ✅ 项目准备情况

### 已完成的配置
- ✅ FastAPI 入口：`main:app`（在 `main.py` 第 984 行）
- ✅ CORS 已配置：允许所有来源（第 986-992 行）
- ✅ `requirements.txt` 已准备完成
- ✅ `Spacefile` 已创建

### 部署入口信息
- **ASGI 入口模块**：`main:app`
- **FastAPI 应用实例**：`main.py` 中的 `app` 变量

---

## 📋 部署步骤

### 第一步：本地测试（可选，但推荐）

在项目根目录执行以下命令：

```bash
# 1. 创建虚拟环境（Windows PowerShell）
python -m venv .venv

# 2. 激活虚拟环境（Windows PowerShell）
.venv\Scripts\Activate.ps1

# 或者使用 CMD：
# .venv\Scripts\activate.bat

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动本地服务器
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

测试访问：
- 前端：http://localhost:8000/
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

---

### 第二步：初始化 Deta Space 应用

在项目根目录执行：

```bash
# 初始化 Deta Space 项目
space new
```

**说明**：
- 如果 `space new` 自动生成了 `Spacefile`，**请用我们手动创建的 `Spacefile` 覆盖它**
- 我们创建的 `Spacefile` 已经配置好了入口、公共路由等

---

### 第三步：部署到 Deta Space

```bash
# 部署到 Deta Space
space push
```

**部署过程**：
- 会显示上传进度
- 会自动安装 `requirements.txt` 中的依赖
- 可能需要等待 1-3 分钟完成部署

---

### 第四步：查看部署结果

部署成功后，Deta Space 会显示：

1. **部署 URL**：形如 `https://xxxxx.deta.space`
   - 这是你的 API 根地址
   - 例如：`https://abc123-def456.deta.space`

2. **访问地址**：
   - API 根路径：`https://xxxxx.deta.space/`
   - API 文档：`https://xxxxx.deta.space/docs`
   - 健康检查：`https://xxxxx.deta.space/health`
   - 统计数据：`https://xxxxx.deta.space/stats`

---

## 🔧 后续操作

### 更新 Netlify 前端 API 地址

部署成功后，需要更新 Netlify 前端的 API 地址：

1. 打开 `netlify-deploy/index.html`
2. 找到第 1042 行：
   ```javascript
   const API_BASE = "https://your-backend-api.com";
   ```
3. 将其改为你的 Deta Space URL，例如：
   ```javascript
   const API_BASE = "https://abc123-def456.deta.space";
   ```
4. 重新部署 Netlify 前端

---

## ⚠️ 重要提示

1. **数据文件**：确保 CSV 数据文件已上传到 Deta Space
   - `Global_Phone_Sentiment/data_bilibili_v2.csv`
   - `Global_Phone_Sentiment/data_bilibili.csv`
   - `Global_Phone_Sentiment/data_gsmarena_notebookcheck.csv`
   - `data_reddit_2111.csv`
   - `data_reddit_20251206_103022.csv`
   - `data_reddit_comments_20251206_105256.csv`

2. **路径问题**：Deta Space 中文件路径可能与本地不同
   - 如果遇到 CSV 文件找不到的问题，可能需要调整路径
   - 检查 `main.py` 中的 `ROOT_DIR` 和 `GLOBAL_SENTIMENT_DIR` 路径

3. **首次启动**：部署后首次访问可能会较慢
   - 因为需要加载所有 CSV 数据
   - 后续访问会更快（数据已加载到内存）

---

## 🐛 故障排查

### 部署失败
- 检查 `Spacefile` 格式是否正确（YAML 格式）
- 确认 `requirements.txt` 中的依赖版本兼容
- 查看 Deta Space 日志：`space logs`

### API 无法访问
- 检查 `Spacefile` 中的 `public_routes` 是否设置为 `["*"]`
- 确认部署状态：在 Deta Space Dashboard 查看

### 数据加载失败
- 检查 CSV 文件是否已上传
- 查看日志：`space logs` 查看错误信息
- 检查文件路径是否正确

---

## 📝 文件清单

### 已创建/修改的文件：

1. **`Spacefile`** ✅（新建）
   - Deta Space 配置文件
   - 定义了入口：`main:app`
   - 配置了公共路由：`["*"]`

2. **`requirements.txt`** ✅（已更新）
   - 添加了注释说明
   - 包含所有必要依赖

3. **`main.py`** ✅（无需修改）
   - FastAPI 入口已在 `main:app`
   - CORS 已配置

4. **`DETA_部署命令清单.md`** ✅（新建，本文档）

---

## 🎉 完成！

部署成功后，你的 API 将可以通过 Deta Space 提供的 URL 访问。

记住：
- **入口模块**：`main:app`
- **API 根路径**：部署后会显示在你的 Deta Space Dashboard
- **所有路由**：默认对公网开放

如有问题，请查看 Deta Space 文档或运行 `space logs` 查看日志。

