# TaskCompass Server

AI 驅動的需求對齊工具後端服務

[前端仓库](https://github.com/lonicrea/taskcompass-frontend)

## 📖 專案簡介

TaskCompass 是一個智慧需求對齊工具，透過多輪互動式對話協助使用者把模糊想法逐步整理成結構化需求。後端採用 Python Flask，預設串接 OpenAI API 來提供問答與分析能力，並保留 OpenAI 相容端點的擴充彈性。

## ✨ 核心功能

- 🤖 **智慧問題生成**：根據使用者想法自動生成 5-10 個針對性問題
- 📝 **多輪需求對齊**：支援多輪互動，持續細化需求
- 📊 **報告自動生成**：根據問答內容生成結構化需求分析報告
- 📄 **文件匯出**：支援匯出 Markdown 格式專案文件
- 💾 **工作階段管理**：以 SQLite 持久化儲存專案資料
- 🔒 **Token 限額**：可配置每日 token 使用限額，控制成本
- 🔐 **API 金鑰安全**：金鑰可存放於伺服器端，不暴露給前端

## 🛠️ 技術棧

- **框架**：Flask 3.0.3
- **資料庫**：SQLite
- **AI 串接**：OpenAI API
- **PDF 生成**：ReportLab
- **CORS**：Flask-CORS

## 📦 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/lonicrea/taskcompass-backend.git
cd TaskCompass-Backend
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv .
# Windows
Scripts\activate
# Linux/Mac
source bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置環境變數

編輯 `.env` 檔案：

```env
# OpenAI API 配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# 應用配置
SECRET_KEY=your_secret_key_here
PORT=5000

# Token 限額配置（每日總 token 數限制，設為 0 代表不限制）
DAILY_TOKEN_LIMIT=0
```

如果你要改用其他 OpenAI 相容服務，也可以額外填入：

```env
QWEN_API_KEY=
QWEN_BASE_URL=
QWEN_MODEL=
```

### 5. 執行伺服器

```bash
python run.py
```

伺服器會在 `http://localhost:5000` 啟動。

## 📡 API 介面

### 健康檢查
```http
GET /api/health
```

### 生成問題
```http
POST /api/generate-questions
Content-Type: application/json

{
  "idea": "我想開發一個線上學習平台"
}
```

### 取得工作階段資料
```http
GET /api/session/<session_id>
```

### 提交答案
```http
POST /api/submit-answers
Content-Type: application/json

{
  "session_id": "uuid",
  "answers": [
    {"answer": "答案內容 1"},
    {"answer": "答案內容 2"}
  ]
}
```

### 繼續細化需求
```http
POST /api/continue-with-feedback
Content-Type: application/json

{
  "session_id": "uuid",
  "feedback": "我想增加使用者權限管理功能"
}
```

### 生成 PDF 文件
```http
POST /api/generate-pdf
Content-Type: application/json

{
  "session_id": "uuid"
}
```

### 下載文件
```http
GET /api/download-pdf/<session_id>
```

### 刪除工作階段
```http
DELETE /api/session/<session_id>
```

## ⚙️ 配置說明

### 環境變數

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 金鑰 | - |
| `OPENAI_BASE_URL` | OpenAI API 基礎 URL | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | 預設模型名稱 | `gpt-4o-mini` |
| `QWEN_API_KEY` | 舊版相容金鑰（可選） | - |
| `QWEN_BASE_URL` | 舊版相容基礎 URL（可選） | - |
| `QWEN_MODEL` | 舊版相容模型名稱（可選） | - |
| `SECRET_KEY` | Flask 金鑰 | `dev-secret-key` |
| `PORT` | 服務埠 | `5000` |
| `DAILY_TOKEN_LIMIT` | 每日 token 限額（0 代表不限制） | `0` |

### Token 限額

設定 `DAILY_TOKEN_LIMIT` 可控制每日 token 使用量：
- `0`：不限制
- `100000`：每日最多使用 100,000 個 token

達到限額後，AI 相關功能將暫停使用，但查看歷史紀錄等功能不受影響。

## 📁 项目结构

```
TaskCompass-server/
├── app/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── session.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── main.py
│   └── utils/
│       ├── __init__.py
│       ├── openai_api.py
│       ├── pdf_generator.py
│       ├── markdown_generator.py
│       └── token_limit.py
├── output/
├── taskcompass.db
├── .env
├── requirements.txt
└── run.py  # 启动脚本
```


## 常見問題

### 1. 無法連線到 OpenAI API
檢查 `.env` 檔案中的 `OPENAI_API_KEY`、`OPENAI_BASE_URL` 與 `OPENAI_MODEL` 是否正確配置。

### 2. Token 限額生效
查看 `.env` 中的 `DAILY_TOKEN_LIMIT` 配置，設為 `0` 可停用限額。


## 📄 开源协议： GPL v3

## 👨‍💻 作者
Royan([Royan·小站](https://www.ycxhl.top))
