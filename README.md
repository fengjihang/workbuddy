# ZCM 招投标助手

基于 AI 大模型的招投标全流程辅助平台，提供招标文件解析、投标书生成、合规性审查、知识库管理等核心功能。

## 功能模块

| 模块 | 说明 |
|------|------|
| 招标分析 | 上传招标文件，AI 自动解析关键条款、评分标准、废标风险 |
| 投标书生成 | 根据招标文件智能生成投标响应文件，支持在线编辑 |
| 合规性审查 | 对比招标文件与投标书，逐项检查符合性，识别废标风险 |
| 知识库管理 | 管理历史标书、企业资质等文档，支持 RAG 语义检索 |

## 技术栈

- **后端**：Python 3.10+ / FastAPI / SQLAlchemy / ChromaDB / SQLite
- **前端**：Vue 3 / TypeScript / Vite / Element Plus / Pinia
- **AI**：兼容 OpenAI 接口的大模型（默认 DeepSeek）

## 环境要求

- Python >= 3.10
- Node.js >= 18
- pip / npm

---

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/fengjihang/workbuddy.git
cd workbuddy
```

### 2. 后端配置

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 复制并填写环境变量
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API 配置：

```env
# LLM 配置（默认使用 DeepSeek，也可替换为其他兼容 OpenAI 接口的服务）
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=sk-你的API密钥
LLM_MODEL=deepseek-chat
EMBEDDING_MODEL=text-embedding-3-small

# 服务配置（一般不需要修改）
HOST=0.0.0.0
PORT=8000
DATABASE_URL=sqlite:///./zcm.db
```

> 💡 **获取 API Key**：访问 [DeepSeek 开放平台](https://platform.deepseek.com/) 注册并创建 API Key。也可使用其他兼容 OpenAI 接口的服务（如 OpenAI、通义千问等），修改 `LLM_BASE_URL` 和 `LLM_MODEL` 即可。

### 3. 启动后端

```bash
# 在 backend 目录下执行
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

启动成功后访问 http://localhost:8000/api/health 返回 `{"status":"ok"}` 即表示正常。

### 4. 前端配置与启动

```bash
# 新开一个终端，进入 frontend 目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

启动成功后访问 **http://localhost:5173** 即可使用。

---

## 目录结构

```
zcm-project/
├── backend/
│   ├── app/
│   │   ├── main.py          # 应用入口
│   │   ├── config.py        # 配置管理
│   │   ├── database.py      # 数据库连接
│   │   ├── models/          # 数据库模型
│   │   ├── schemas/         # Pydantic 数据校验
│   │   ├── routes/          # API 路由（招标/投标/合规/知识库）
│   │   ├── services/        # 业务逻辑层
│   │   ├── rag/             # RAG 检索增强生成
│   │   └── llm/             # LLM 接口封装
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── views/           # 页面组件
│   │   ├── stores/          # Pinia 状态管理
│   │   ├── api/             # 后端接口封装
│   │   ├── router/          # 路由配置
│   │   └── components/      # 公共组件
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## 注意事项

- 数据库文件 `zcm.db` 在首次启动时自动创建，无需手动初始化
- 上传的文件存储在 `backend/uploads/`，向量数据存储在 `backend/chroma_data/`，这些目录已在 `.gitignore` 中排除，不会上传到 Git
- 生产部署时建议将 `RELOAD` 关闭（去掉 `--reload` 参数）并配置 Nginx 反向代理

## 常见问题

**Q：启动后端报 `ModuleNotFoundError`？**
A：确认已在 `backend` 目录下执行 `pip install -r requirements.txt`，建议使用虚拟环境。

**Q：前端请求 API 报错 `Network Error`？**
A：确认后端已正常启动在 8000 端口，前端开发服务器通过 Vite 代理转发 `/api` 请求到后端。

**Q：LLM 调用报错？**
A：访问 http://localhost:8000/api/llm-test 测试 LLM 连通性，检查 `.env` 中的 `LLM_API_KEY` 是否正确填写。
