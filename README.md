# 品牌舆情看板

基于 React + TypeScript + Tailwind CSS 的品牌舆情分析看板。

## 技术栈

- **React 18** - UI框架
- **TypeScript** - 类型安全
- **Tailwind CSS** - 样式框架
- **Headless UI** - 无样式组件库
- **Vite** - 构建工具

## 项目结构

```
frontend/
├── src/
│   ├── components/
│   │   └── dashboard/
│   │       ├── TabsRoot.tsx          # Tab切换根组件
│   │       ├── SummaryCards.tsx      # KPI卡片
│   │       ├── BrandTable.tsx        # 品牌表格
│   │       ├── CommentsFilter.tsx    # 评论筛选器
│   │       ├── CommentsTable.tsx     # 评论表格
│   │       └── AIInsightPanel.tsx    # AI分析面板
│   ├── pages/
│   │   └── Dashboard.tsx             # 主页面
│   ├── data/                         # Mock数据
│   │   ├── phones_summary.json
│   │   ├── cars_summary.json
│   │   ├── devices_summary.json
│   │   ├── phones_comments_sample.json
│   │   ├── cars_comments_sample.json
│   │   └── devices_comments_sample.json
│   ├── types/
│   │   └── index.ts                  # TypeScript类型定义
│   ├── utils/
│   │   └── dataLoader.ts             # 数据加载工具
│   ├── App.tsx                       # 应用入口
│   ├── main.tsx                      # React入口
│   └── index.css                     # 全局样式
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## 安装依赖

```bash
cd frontend
npm install
# 或
pnpm install
# 或
yarn install
```

## 开发运行

```bash
npm run dev
# 或
pnpm dev
# 或
yarn dev
```

访问 http://localhost:5173

## 构建

```bash
npm run build
```

## 数据结构

### DashboardSummary

顶层汇总数据，包含平台、品牌数、型号数、评论数等统计信息。

### BrandRow

品牌行数据，包含品牌信息、热门型号、来源平台、情感统计等。

### UnifiedComment

统一评论数据格式，支持多平台（Bilibili、Reddit、GSM Arena）的数据聚合。

## 功能特性

1. **三个Tab切换**：智能手机、汽车、其他智能家电
2. **KPI卡片**：舆情平台数、品牌数量、覆盖型号数、用户评论数
3. **品牌表格**：支持按评论数、好评率排序
4. **评论筛选**：品牌、型号、平台、情感、时间多维度筛选
5. **评论表格**：分页展示，支持详细查看
6. **AI分析面板**：问题输入和结果展示（当前为Mock）

## 后续接入真实API

将 `src/utils/dataLoader.ts` 中的数据加载函数替换为真实的API调用即可。
