# Render 部署说明

## ✅ 项目准备情况

### 已完成的配置
- ✅ FastAPI 入口：`main:app`（在 `main.py` 第 984 行）
- ✅ CORS 已配置：允许所有来源，为 Netlify 前端做好准备
- ✅ `requirements.txt` 已准备完成
- ✅ `render.yaml` 配置文件已创建

### 部署入口信息
- **ASGI 入口模块**：`main:app`
- **FastAPI 应用实例**：`main.py` 中的 `app` 变量

---

## 📋 部署步骤（按顺序执行）

### 第一步：将项目推送到 GitHub

如果你的项目还没有推送到 GitHub，请按以下步骤操作：

```bash
# 1. 初始化 Git 仓库（如果还没有）
git init

# 2. 添加所有文件
git add .

# 3. 提交代码
git commit -m "Initial commit: FastAPI backend for Render deployment"

# 4. 在 GitHub 上创建一个新仓库，然后关联远程仓库
# 注意：请将下面的 URL 替换为你实际的 GitHub 仓库地址
git remote add origin https://github.com/你的用户名/你的仓库名.git

# 5. 推送代码到 GitHub
git branch -M main
git push -u origin main
```

**重要提示**：
- 请确保将所有必要的文件都提交了，包括：
  - `main.py`
  - `requirements.txt`
  - `render.yaml`
  - `Global_Phone_Sentiment/` 目录（包含 CSV 数据和 config.py）
  - 根目录的 CSV 数据文件
- 如果项目已经推送到 GitHub，可以直接跳到第二步

---

### 第二步：登录 Render 并创建 Web Service

1. **登录 Render**
   - 访问 https://render.com
   - 使用 GitHub 账号登录（推荐）

2. **创建新服务**
   - 点击右上角的 **"New +"** 按钮
   - 选择 **"Web Service"**

3. **连接 GitHub 仓库**
   - 在 "Connect a repository" 页面，选择你的 GitHub 仓库
   - 如果还没有授权，点击 "Configure account" 授权 Render 访问你的 GitHub

4. **配置服务（如果 Render 自动识别了 render.yaml）**
   - Render 会自动检测到 `render.yaml` 文件
   - 直接点击 **"Apply"** 或 **"Create Web Service"** 即可
   - 所有配置会自动从 `render.yaml` 读取

5. **手动配置（如果 Render 没有自动识别 render.yaml）**
   - **Name**：`phone-sentiment-api`（或你喜欢的名称）
   - **Region**：选择 `Frankfurt` 或 `Singapore`（推荐选择离你较近的地区）
   - **Branch**：选择 `main` 或 `master`
   - **Root Directory**：留空（使用项目根目录）
   - **Runtime**：选择 `Python 3`
   - **Build Command**：`pip install -r requirements.txt`
   - **Start Command**：`uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**：选择 `Free`（免费计划）
   - **Auto-Deploy**：选择 `Yes`（代码推送后自动部署）

6. **点击 "Create Web Service"**
   - Render 会开始构建和部署你的服务
   - 这个过程可能需要 3-5 分钟

---

### 第三步：等待部署完成

1. **查看部署日志**
   - 在 Render Dashboard 中，点击你的服务
   - 在 "Events" 或 "Logs" 标签页查看部署进度
   - 等待看到 "Your service is live" 的提示

2. **检查部署状态**
   - 如果部署成功，状态会显示为 "Live"
   - 如果部署失败，查看日志找出错误原因

3. **复制服务 URL**
   - 部署成功后，Render 会提供一个 URL
   - 格式类似：`https://phone-sentiment-api.onrender.com`
   - **请复制这个 URL，后面会用到**

---

### 第四步：测试 API

部署成功后，可以访问以下地址测试：

- **API 根路径**：`https://你的服务名.onrender.com/`
- **API 文档**：`https://你的服务名.onrender.com/docs`
- **健康检查**：`https://你的服务名.onrender.com/health`
- **统计数据**：`https://你的服务名.onrender.com/stats`

如果这些地址都能正常访问，说明部署成功！

---

### 第五步：更新前端 API 地址

1. **打开前端文件**
   - 编辑 `netlify-deploy/index.html` 文件
   - 找到第 1042 行左右，找到这一行：
     ```javascript
     const API_BASE = "https://your-backend-api.com";
     ```

2. **更新为 Render 的 URL**
   - 将 `API_BASE` 改为你的 Render 服务 URL，例如：
     ```javascript
     const API_BASE = "https://phone-sentiment-api.onrender.com";
     ```
   - **注意**：不要加末尾的斜杠 `/`

3. **保存文件**

4. **部署前端到 Netlify**
   - 将整个 `netlify-deploy` 文件夹压缩成 ZIP
   - 访问 https://app.netlify.com
   - 点击 "Add new site" → "Deploy manually"
   - 拖拽 ZIP 文件上传
   - 等待部署完成

---

## 🔧 本地测试命令

在部署到 Render 之前，建议先在本地测试：

### Windows PowerShell 命令

```powershell
# 1. 创建虚拟环境
python -m venv .venv

# 2. 激活虚拟环境
.venv\Scripts\Activate.ps1

# 如果上面的命令报错，可以尝试：
# .venv\Scripts\activate.bat

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 测试访问

启动后，访问以下地址：
- http://localhost:8000/ - API 根路径
- http://localhost:8000/docs - API 文档
- http://localhost:8000/health - 健康检查

---

## ⚠️ 重要提示

### 1. 数据文件
- 确保所有 CSV 数据文件都在项目中并提交到 GitHub
- Render 会从 GitHub 拉取代码，所以数据文件也需要在仓库里

### 2. 免费计划限制
- Render 免费计划有资源限制
- 如果服务 15 分钟没有活动，会自动休眠
- 首次访问休眠后的服务可能需要等待 30-60 秒唤醒

### 3. 端口配置
- Render 使用环境变量 `$PORT` 来指定端口
- 启动命令已配置为使用 `$PORT`，无需修改

### 4. CORS 配置
- 后端已配置允许所有来源（`allow_origins=["*"]`）
- 这样 Netlify 前端可以正常访问后端 API

---

## 🐛 故障排查

### 部署失败

**检查点：**
1. 查看 Render 的 Build Logs，找出错误信息
2. 确认 `requirements.txt` 中的依赖版本兼容
3. 确认 `render.yaml` 格式正确（YAML 格式）
4. 确认所有必要的文件都已提交到 GitHub

### API 无法访问

**检查点：**
1. 确认服务状态是 "Live"
2. 检查健康检查路径 `/health` 是否能访问
3. 查看 Render 的 Runtime Logs 查看错误信息
4. 确认端口配置正确（使用 `$PORT`）

### 数据加载失败

**检查点：**
1. 确认 CSV 文件已提交到 GitHub
2. 检查文件路径是否正确（相对路径）
3. 查看 Runtime Logs 查看具体错误信息

### 前端无法连接后端

**检查点：**
1. 确认前端 `API_BASE` 地址正确（没有末尾斜杠）
2. 确认后端 CORS 已配置
3. 检查浏览器控制台是否有 CORS 错误
4. 确认后端服务是 "Live" 状态

---

## 📝 文件清单

### 已创建/修改的文件：

1. **`render.yaml`** ✅（新建）
   - Render 部署配置文件
   - 定义了构建命令、启动命令、环境变量等

2. **`requirements.txt`** ✅（已存在，已确认完整）
   - 包含所有必要的 Python 依赖

3. **`main.py`** ✅（无需修改）
   - FastAPI 入口已在 `main:app`
   - CORS 已配置

4. **`RENDER_部署说明.md`** ✅（新建，本文档）

---

## 🎉 完成！

部署成功后，你的 API 将可以通过 Render 提供的 URL 访问。

记住：
- **入口模块**：`main:app`
- **服务 URL**：部署后会在 Render Dashboard 显示
- **所有路由**：默认对公网开放（通过 `render.yaml` 配置）

如有问题，请查看 Render 的日志或参考本文档的故障排查部分。

