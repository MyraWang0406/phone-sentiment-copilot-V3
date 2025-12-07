# 手机品牌舆情 Copilot - 部署说明

## 📦 快速部署

### 1. 环境准备
```bash
# 安装依赖
pip install -r requirements.txt
```

### 2. 数据文件检查
确保以下 CSV 文件存在：
- `Global_Phone_Sentiment/data_bilibili_v2.csv`
- `Global_Phone_Sentiment/data_bilibili.csv`
- `Global_Phone_Sentiment/data_gsmarena_notebookcheck.csv`
- `data_reddit_2111.csv`
- `data_reddit_20251206_103022.csv`
- `data_reddit_comments_20251206_105256.csv`

### 3. 启动服务
```bash
# 方式1：直接运行
python main.py

# 方式2：使用 uvicorn（推荐生产环境）
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 4. 访问应用
- 前端界面：http://127.0.0.1:8000/
- API 文档：http://127.0.0.1:8000/docs

## ✅ 已实现功能

### 前端功能
1. ✅ 标题显示："锦书舆情 Copilot"
2. ✅ 副标题包含："- 智能手机"
3. ✅ 5个KPI卡片（平台数、品牌数、型号数、原始内容、评论数）
4. ✅ 品牌舆情概览表（支持表头排序）
5. ✅ 评论透视（支持品牌/平台/型号/年月筛选）
6. ✅ Tooltip 详细说明
7. ✅ 响应式布局

### 后端功能
1. ✅ 数据加载与清洗（Bilibili/GSMArena/Reddit）
2. ✅ 品牌和型号过滤（排除URL和Other）
3. ✅ 情感分析（基于关键词匹配）
4. ✅ 评论筛选（支持品牌/平台/型号/年月）

## 📝 注意事项

1. **GSM原始内容**：GSMArena数据均为评论类型，原始内容数为0是正常现象
2. **情感分析**：基于关键词匹配，准确度有限，后续可接入大模型优化
3. **Copilot接口**：当前为规则基础占位实现，不调用大模型

## 🔧 配置修改

编辑 `Global_Phone_Sentiment/config.py` 可修改：
- 品牌定义
- 目标抓取型号列表

## 📊 API 接口说明

- `GET /stats` - 获取统计数据
- `GET /insights` - 获取品牌洞察（已过滤Other品牌）
- `GET /opinions` - 获取评论详情（支持品牌/平台/型号/年月筛选）
- `POST /copilot` - 智能分析（占位实现）

## 🐛 故障排查

如果遇到问题：
1. 检查后端日志输出
2. 确认CSV文件路径正确
3. 清除浏览器缓存后重试
4. 查看浏览器控制台错误信息

