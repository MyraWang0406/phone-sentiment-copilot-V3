# 快速启动指南

## 📋 项目信息

**项目入口文件**: `frontend/src/pages/Dashboard.tsx`  
**开发运行命令**: `npm run dev` (或 `pnpm dev` / `yarn dev`)

## 🚀 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:5173 即可看到品牌舆情看板。

## 📁 项目结构说明

```
frontend/
├── src/
│   ├── pages/
│   │   └── Dashboard.tsx          # ⭐ 主入口页面
│   ├── components/dashboard/      # 所有看板组件
│   ├── data/                      # Mock数据（后续替换为真实API）
│   ├── types/                     # TypeScript类型定义
│   └── utils/                     # 工具函数
```

## 🔄 接入真实API

当需要接入真实后端API时，只需修改 `src/utils/dataLoader.ts`：

```typescript
export async function loadSummary(category: 'phone' | 'car' | 'device'): Promise<DashboardSummary> {
  const response = await fetch(`/api/summary/${category}`)
  return response.json()
}

export async function loadComments(category: 'phone' | 'car' | 'device'): Promise<UnifiedComment[]> {
  const response = await fetch(`/api/comments/${category}`)
  return response.json()
}
```

## 📊 数据结构

所有数据类型定义在 `src/types/index.ts` 中：

- `DashboardSummary` - 顶层汇总数据
- `BrandRow` - 品牌行数据
- `UnifiedComment` - 统一评论格式
- `CommentFilters` - 筛选条件

Mock数据文件：
- `phones_summary.json` / `cars_summary.json` / `devices_summary.json`
- `phones_comments_sample.json` / `cars_comments_sample.json` / `devices_comments_sample.json`

## 🎨 样式说明

- 使用 Tailwind CSS，配置在 `tailwind.config.js`
- 主色调：蓝色系（primary-500, primary-600等）
- 响应式：支持1366×768及以上分辨率

## ⚙️ 技术栈

- React 18 + TypeScript
- Tailwind CSS
- Headless UI（Tab、Listbox等组件）
- Vite（构建工具）

## 📝 注意事项

1. 确保 Node.js 版本 >= 16
2. 首次运行需要安装依赖
3. Mock数据已包含示例，可直接查看效果
4. AI分析功能当前为Mock实现，后续接入真实大模型API
