# 福州充电桩智能选址系统

> 基于 Django + LangChain Agent + RAG + 知识图谱 + 高德地图的新能源充电桩智能选址 Web 应用

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.2-green)](https://djangoproject.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.2-orange)](https://langchain.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 系统功能概览

| 功能模块 | 说明 |
|---|---|
| **福州市区地图选点** | 高德地图 v2.0，支持点击选点，自动避开水域/林地/保护区等禁止区域 |
| **主干道流量热力图** | 24条福州主干道实时流量可视化，彩色路段叠加 + 热力图层 |
| **LangChain Agent 分析** | 基于 DeepSeek LLM，集成 RAG 检索 + 知识图谱查询 + POI/流量工具 |
| **知识图谱可视化** | 23节点知识图谱，展示 POI 类型、道路等级、充电需求关联关系 |
| **长期记忆系统** | 跨会话对话记忆，保存历史选址记录和分析结论 |
| **智能选址报告** | 包含 POI 分析、流量分析、AI 结论、备选位置推荐，支持 PDF 下载 |

---

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    前端 (HTML/CSS/JS)                    │
│  高德地图 v2.0 │ ECharts 知识图谱 │ 热力图 │ 报告展示   │
└────────────────────────┬────────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────────┐
│                  Django 4.2 后端                         │
│  maps │ analysis │ memory │ reports │ knowledge_base     │
└──────┬──────────┬────────┬──────────────────────────────┘
       │          │        │
  PostgreSQL  ChromaDB  LangChain Agent
  (地理实体)  (知识向量)  (DeepSeek LLM)
                          │
                    RAG + 知识图谱
                    + POI工具
                    + 流量工具
```

### 核心技术栈

- **后端框架**: Django 4.2 + Django REST Framework
- **数据库**: PostgreSQL（地理实体、POI、交通流量）
- **向量数据库**: ChromaDB（充电桩选址知识向量）
- **AI 引擎**: LangChain 0.2 + DeepSeek API（兼容 OpenAI 接口）
- **地图服务**: 高德地图 JavaScript API v2.0
- **知识图谱**: NetworkX + ECharts 可视化
- **报告生成**: ReportLab（PDF）

---

## 快速启动

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/l18920790129-art/fuzhou-ev-charging-system.git
cd fuzhou-ev-charging-system

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入以下配置：
```

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
AMAP_KEY=your_amap_key
AMAP_SECURITY_KEY=your_amap_security_key
DATABASE_URL=postgresql://user:password@localhost:5432/fuzhou_ev
```

### 3. 初始化数据库

```bash
python manage.py migrate
python data/init_fuzhou_data.py       # 初始化 POI 和交通流量数据
python knowledge_base/build_knowledge_base.py  # 构建 ChromaDB 知识向量库
```

### 4. 启动服务

```bash
python manage.py runserver 0.0.0.0:8000
```

访问 http://localhost:8000 即可使用系统。

---

## 项目结构

```
fuzhou_ev_charging/
├── maps/                    # 地图模块：POI、交通流量、禁止区域
│   ├── models.py            # 地理实体数据模型
│   ├── views.py             # 地图 API 视图
│   └── urls.py
├── analysis/                # AI 分析模块
│   ├── agent.py             # LangChain Agent 核心引擎
│   ├── models.py            # 分析任务数据模型
│   └── views.py             # 分析 API（异步任务轮询）
├── memory/                  # 长期记忆模块
│   ├── models.py            # 对话记忆、选址历史
│   └── views.py
├── reports/                 # 报告生成模块
│   ├── models.py            # 报告数据模型
│   └── views.py             # PDF 报告生成
├── knowledge_base/          # 知识库
│   └── build_knowledge_base.py  # ChromaDB 构建脚本
├── data/                    # 数据初始化脚本
│   ├── init_fuzhou_data.py  # 福州 POI + 交通数据
│   └── enhance_data.py      # 数据增强
├── templates/
│   └── index.html           # 主页面模板
├── static/
│   ├── css/main.css         # 主样式
│   └── js/app.js            # 前端应用逻辑
└── fuzhou_ev_charging/
    ├── settings.py          # Django 配置
    └── urls.py              # 主路由
```

---

## API 接口文档

### 地图相关

| 接口 | 方法 | 说明 |
|---|---|---|
| `/api/maps/pois/` | GET | 获取所有 POI 数据 |
| `/api/maps/traffic/` | GET | 获取主干道交通流量 |
| `/api/maps/heatmap/` | GET | 获取热力图数据点 |
| `/api/maps/exclusion-zones/` | GET | 获取禁止选址区域 |
| `/api/maps/quick-score/` | POST | 快速评分（坐标 → 评分） |
| `/api/maps/candidates/` | GET | 获取候选选址列表 |

### AI 分析相关

| 接口 | 方法 | 说明 |
|---|---|---|
| `/api/analysis/chat/` | POST | 发送消息给 LangChain Agent |
| `/api/analysis/task/<id>/` | GET | 轮询分析任务状态 |
| `/api/analysis/knowledge-graph/` | GET | 获取知识图谱数据 |

### 记忆系统

| 接口 | 方法 | 说明 |
|---|---|---|
| `/api/memory/history/` | GET | 获取对话历史 |
| `/api/memory/clear/` | POST | 清除当前会话记忆 |

### 报告相关

| 接口 | 方法 | 说明 |
|---|---|---|
| `/api/reports/generate/` | POST | 生成选址报告 |
| `/api/reports/list/` | GET | 获取报告列表 |
| `/api/reports/<id>/` | GET | 获取报告详情 |
| `/api/reports/<id>/pdf/` | GET | 下载 PDF 报告 |

---

## 数据说明

### POI 数据（60个）

覆盖福州市区主要 POI，包括：
- 地铁站（1号线、2号线、4号线共15个站点）
- 购物中心（万象城、东百中心、泰禾广场等）
- 医院（省立医院、协和医院、第一医院等）
- 写字楼、景区、加油站、停车场

### 交通流量数据（24条主干道）

| 道路名称 | 等级 | 日均流量 |
|---|---|---|
| 福厦高速（福州段） | 高速 | 95,000辆/日 |
| 绕城高速（北段） | 高速 | 88,000辆/日 |
| 福马路 | 主干道 | 65,000辆/日 |
| 八一七路（北段） | 主干道 | 55,000辆/日 |
| ... | ... | ... |

### 禁止选址区域（8个）

旗山国家森林公园、鼓山风景区、西湖公园、左海公园、晋安河水系、光明港水系、闽江水域、福州国家森林公园

---

## LangChain Agent 工具链

Agent 配备以下工具，自动选择并组合调用：

1. **`retrieve_knowledge`** — RAG 检索 ChromaDB 知识向量库
2. **`query_knowledge_graph`** — 查询知识图谱节点关系
3. **`check_exclusion_zones`** — 检查坐标是否在禁止区域
4. **`query_nearby_pois`** — 查询周边 POI 及需求评分
5. **`query_traffic_flow`** — 查询周边主干道流量数据
6. **`calculate_location_score`** — 综合评分计算

---

## 开发团队

本系统为福州市新能源充电桩选址智能决策平台原型，旨在通过 AI 技术辅助充电基础设施规划。

---

## License

MIT License
