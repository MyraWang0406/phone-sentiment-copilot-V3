# GitHub + Netlify 部署指南

## 📋 当前项目结构

根据你的 GitHub 仓库 `https://github.com/MyraWang0406/international-car-auto-sentiment`，项目应该在**根目录**，而不是 `frontend` 子目录。

## 🔍 检查当前结构

你的项目结构应该是：

```
international-car-auto-sentiment/  (GitHub 仓库根目录)
├── src/
├── public/  (如果有)
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
├── netlify.toml
└── ...
```

## ✅ 部署步骤

### 步骤1：确保所有文件在正确位置

如果项目在 `frontend` 子目录，需要：

**选项A：将 frontend 目录内容移到根目录**
```bash
# 在项目根目录执行
cd frontend
# 将所有文件复制到上一级目录
# (注意：不要复制 node_modules)
```

**选项B：保持 frontend 目录，修改 Netlify 配置**
在 Netlify 设置中：
- Base directory: `frontend`
- Build command: `cd frontend && npm run build`
- Publish directory: `frontend/dist`

### 步骤2：提交到 GitHub

```bash
# 确保在正确的目录（项目根目录或 frontend 目录）
git add .
git commit -m "Fix: 修复部署配置"
git push origin main
```

### 步骤3：在 Netlify 中配置

1. 访问 https://app.netlify.com/
2. 点击 "Add new site" → "Import an existing project"
3. 选择 GitHub，授权后选择仓库
4. **重要配置**：
   - **Base directory**: 
     - 如果项目在根目录：留空
     - 如果项目在 frontend 子目录：填写 `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `dist`（如果在根目录）或 `frontend/dist`（如果在子目录）

### 步骤4：检查 netlify.toml

确保 `netlify.toml` 文件在正确位置：
- 如果在根目录：`./netlify.toml`
- 如果在 frontend 子目录：`./frontend/netlify.toml`

## 🐛 常见部署问题

### 问题1：Netlify 找不到 package.json
**原因**：Base directory 设置错误
**解决**：检查项目结构，正确设置 Base directory

### 问题2：构建成功但页面空白
**原因**：路由配置问题
**解决**：确保 `netlify.toml` 中有 redirects 配置

### 问题3：资源404错误
**原因**：路径问题
**解决**：检查 `vite.config.ts`，确保 base 路径正确

## 📝 快速检查清单

- [ ] 所有源代码文件已提交到 GitHub
- [ ] `package.json` 存在且正确
- [ ] `netlify.toml` 存在且配置正确
- [ ] `.gitignore` 包含 `node_modules` 和 `dist`
- [ ] 本地 `npm run build` 可以成功构建
- [ ] Netlify 的 Base directory 设置正确
- [ ] Netlify 的 Publish directory 设置为 `dist`

## 🚀 验证部署

部署成功后，访问 Netlify 提供的 URL，检查：
1. 页面正常加载
2. 三个 Tab 可以切换
3. 数据正常显示
4. 所有交互功能正常

