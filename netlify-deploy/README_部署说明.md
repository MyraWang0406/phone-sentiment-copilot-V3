# Netlify 部署说明

## 📦 部署包内容

这个 `netlify-deploy` 文件夹包含可以直接部署到 Netlify 的前端文件。

## ⚠️ 部署前必做

### 1. 修改 Render 后端地址

**重要**：前端已配置为通过 Netlify 代理访问 Render 后端，无需修改 `index.html`。

只需修改 `netlify.toml` 文件中的 Render 后端地址：

打开 `netlify.toml` 文件，找到以下配置：

```toml
# 代理 /api/* 路径
[[redirects]]
  from = "/api/*"
  to = "https://phone-sentiment-copilot.onrender.com/api/:splat"
  status = 200
  force = true

# 代理 /opinions 路径
[[redirects]]
  from = "/opinions*"
  to = "https://phone-sentiment-copilot.onrender.com/opinions:splat"
  status = 200
  force = true

# 代理 /copilot 路径
[[redirects]]
  from = "/copilot"
  to = "https://phone-sentiment-copilot.onrender.com/copilot"
  status = 200
  force = true
```

**将 `https://phone-sentiment-copilot.onrender.com` 替换为你的实际 Render 后端地址**。

例如，如果你的 Render 后端地址是 `https://your-api.onrender.com`，则将所有 `phone-sentiment-copilot.onrender.com` 替换为 `your-api.onrender.com`。

⚠️ **注意**：
- 本地调试时，前端会自动使用 `http://127.0.0.1:8000`
- 线上部署时，前端使用相对路径，通过 Netlify 代理访问 Render 后端
- 这种方式避免了 CORS 跨域问题

## 🚀 部署步骤

### 方式一：通过 Netlify 网站（推荐）

1. **登录 Netlify**
   - 访问 https://app.netlify.com
   - 使用 GitHub/GitLab/Bitbucket 账号登录，或注册新账号

2. **创建新站点**
   - 点击 "Add new site" → "Deploy manually"（手动部署）
   - 或者点击 "Import from Git" 连接你的代码仓库

3. **上传文件**
   - 如果是手动部署：
     - 将整个 `netlify-deploy` 文件夹压缩成 ZIP
     - 拖拽 ZIP 文件到 Netlify 上传区域
   - 如果是从 Git 部署：
     - 选择仓库和分支
     - **Build command** 留空或填写：`echo "No build needed"`
     - **Publish directory** 填写：`netlify-deploy`

4. **部署设置**
   - 确保 "Publish directory" 设置为 `.`（当前目录）或 `netlify-deploy`
   - 点击 "Deploy site"

5. **完成部署**
   - 等待部署完成（通常 1-2 分钟）
   - Netlify 会自动分配一个域名，例如：`https://your-site-name.netlify.app`
   - 可以点击 "Site settings" → "Change site name" 自定义域名

### 方式二：通过 Netlify CLI

1. **安装 Netlify CLI**
   ```bash
   npm install -g netlify-cli
   ```

2. **登录 Netlify**
   ```bash
   netlify login
   ```

3. **进入部署文件夹**
   ```bash
   cd netlify-deploy
   ```

4. **部署**
   ```bash
   netlify deploy --prod
   ```

## 🌐 自定义域名

1. 在 Netlify 网站进入你的站点
2. 点击 "Site settings" → "Domain management"
3. 点击 "Add custom domain"
4. 输入你的域名并按照提示配置 DNS

## 🔧 环境变量配置（可选）

如果需要通过环境变量动态配置 API 地址：

1. 在 Netlify 网站进入站点设置
2. 点击 "Environment variables"
3. 添加变量：
   - Key: `VITE_API_BASE`
   - Value: `https://your-backend-api.com`

然后需要修改 `index.html` 中的代码来读取环境变量。

## 📝 注意事项

1. **CORS 跨域问题**
   - 前端部署在 Netlify，后端在另一个域名
   - 需要在后端 FastAPI 代码中配置 CORS
   - 在 `main.py` 中确认已添加：
     ```python
     from fastapi.middleware.cors import CORSMiddleware
     app.add_middleware(
         CORSMiddleware,
         allow_origins=["*"],  # 生产环境建议指定具体域名
         allow_credentials=True,
         allow_methods=["*"],
         allow_headers=["*"],
     )
     ```

2. **HTTPS 和 HTTP**
   - Netlify 默认使用 HTTPS
   - 如果后端使用 HTTP，可能遇到混合内容问题
   - 建议后端也使用 HTTPS

3. **API 地址更新**
   - 修改 API 地址后需要重新部署
   - 可以通过 Netlify 的重新部署功能快速更新

## 🐛 故障排查

### 前端加载但数据显示不出来
- 检查浏览器控制台（F12）是否有 CORS 错误
- 确认 API 地址是否正确
- 确认后端服务是否正常运行

### 部署失败
- 检查文件是否都在 `netlify-deploy` 文件夹中
- 确认 `netlify.toml` 配置是否正确

### API 请求失败
- 检查后端是否允许跨域请求
- 确认后端 API 地址可以正常访问
- 检查网络防火墙设置

## 📞 需要帮助？

如果遇到问题，请检查：
1. 后端服务是否正常运行
2. API 地址配置是否正确
3. 浏览器控制台的错误信息
4. Netlify 部署日志

---

**部署完成后，记得测试所有功能是否正常！** ✨

