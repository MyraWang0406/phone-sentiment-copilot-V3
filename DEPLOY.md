# 部署说明

## 📦 部署到 GitHub

### 1. 初始化 Git 仓库（如果还没有）

```bash
cd frontend
git init
git add .
git commit -m "Initial commit: Brand Sentiment Dashboard"
```

### 2. 连接到 GitHub 仓库

```bash
git remote add origin https://github.com/MyraWang0406/international-car-auto-sentiment.git
git branch -M main
git push -u origin main
```

## 🚀 部署到 Netlify

### 方法一：通过 Netlify 网站（推荐）

1. 访问 [Netlify](https://app.netlify.com/)
2. 点击 "Add new site" → "Import an existing project"
3. 选择 "GitHub" 并授权
4. 选择仓库：`MyraWang0406/international-car-auto-sentiment`
5. 配置构建设置：
   - **Base directory**: `frontend`（如果项目在 frontend 子目录）
   - **Build command**: `npm run build`
   - **Publish directory**: `dist`
6. 点击 "Deploy site"

### 方法二：通过 Netlify CLI

```bash
# 安装 Netlify CLI
npm install -g netlify-cli

# 登录
netlify login

# 部署
cd frontend
netlify deploy --prod
```

### 方法三：直接拖拽 dist 文件夹

1. 先构建项目：`npm run build`
2. 访问 [Netlify Drop](https://app.netlify.com/drop)
3. 将 `frontend/dist` 文件夹拖拽到页面

## ⚙️ Netlify 配置

项目已包含 `netlify.toml` 配置文件：

```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[build.environment]
  NODE_VERSION = "18"
```

## 🔧 如果项目在根目录

如果你的 GitHub 仓库根目录就是前端项目（不是 frontend 子目录），则：

1. 在 Netlify 中设置：
   - **Base directory**: 留空
   - **Build command**: `npm run build`
   - **Publish directory**: `dist`

2. 或者修改 `netlify.toml`：
```toml
[build]
  command = "npm run build"
  publish = "dist"
```

## 📝 注意事项

1. **确保所有文件已提交**：包括 `package.json`、`vite.config.ts`、`tsconfig.json` 等
2. **检查 node_modules**：确保 `.gitignore` 包含 `node_modules`
3. **环境变量**：如果有环境变量，需要在 Netlify 后台设置
4. **构建日志**：如果部署失败，查看 Netlify 的构建日志

## 🐛 常见问题

### 问题1：构建失败 - 找不到模块
**解决**：确保 `package.json` 中所有依赖都已正确安装

### 问题2：页面空白
**解决**：检查 `netlify.toml` 中的 redirects 配置是否正确

### 问题3：资源404错误
**解决**：确保 `vite.config.ts` 中的 base 路径配置正确（通常不需要设置）

## ✅ 验证部署

部署成功后，访问 Netlify 提供的 URL，检查：
- [ ] 页面正常加载
- [ ] Tab 切换正常
- [ ] 数据正常显示
- [ ] 所有功能正常

