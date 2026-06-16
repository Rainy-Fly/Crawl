# Web Crawler System

一个基于 Flask 的可视化爬虫管理系统，支持用户认证、配置化管理、定时调度、AI 智能分析和数据可视化。

## 功能特性

- **用户管理** - 注册/登录，bcrypt 密码加密，Session 会话管理
- **配置管理** - 支持在线编辑或文件上传 JSON 配置，可复用历史配置
- **爬虫调度** - 支持立即执行和 Cron 定时执行，多线程并发，自动重试
- **任务控制** - 实时状态监控（未开始/进行中/已完成/已暂停），支持暂停/恢复/停止
- **AI 分析** - 支持本地模型和 API 两种模式，自动数据清洗、情感分析、关键词提取
- **数据可视化** - 词云、饼图、柱状图、折线图等多种图表，Base64 内联展示

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Flask 3.0.0 + Flask-CORS |
| 数据库 | SQLite |
| 定时调度 | APScheduler 3.10.4 |
| 爬虫引擎 | requests + BeautifulSoup4 |
| 密码加密 | bcrypt |
| AI 分析 | 支持 OpenAI 兼容 API / 本地模型 |
| 可视化 | matplotlib + wordcloud |
| 前端 | 原生 HTML / CSS / JavaScript |

## 项目结构

```
Crawl/
├── index.html                 # 主功能页面
├── sign.html                  # 登录注册页面
├── show.html                  # 可视化展示页面
├── check.html                 # 结果查看页面
├── viz_list.html              # 可视化列表页面
├── crawl_demo_config.json     # 爬虫配置示例
├── time_demo_config.json      # 定时配置示例
├── douban_book_review_config.json
├── requirements.txt           # Python 依赖
├── backend/
│   ├── app.py                 # Flask 主应用入口
│   ├── call_ai.py             # AI 模型调用
│   ├── show.py                # 数据可视化
│   ├── models/
│   │   ├── database.py        # 数据库连接
│   │   ├── user.py            # 用户模型
│   │   ├── config_file.py     # 配置文件模型
│   │   ├── crawler_task.py    # 爬虫任务模型
│   │   ├── crawler_result.py  # 爬虫结果模型
│   │   ├── ai_config.py       # AI 配置模型
│   │   └── visualization.py   # 可视化模型
│   └── services/
│       └── crawler_service.py # 爬虫服务（单例模式）
└── static/
    ├── css/
    │   ├── style.css
    │   └── sign.css
    └── js/
        ├── auth.js            # 登录认证
        ├── main.js            # 主页面逻辑
        ├── show.js            # 可视化逻辑
        └── check.js           # 结果查看
```

## 快速开始

### 环境要求

- Python 3.8+

### 安装

```bash
# 克隆项目
git clone <repo-url>
cd Crawl

# 安装依赖
pip install -r requirements.txt
```

### 启动

```bash
cd backend
python app.py
```

浏览器访问 http://127.0.0.1:5000 ，首次使用请先注册账号。

## 配置说明

### 爬虫配置

```json
{
  "type": "crawler",
  "name": "示例爬虫",
  "urls": ["https://example.com/page1"],
  "selectors": {
    "title": "h1, h2, .title",
    "content": "p, .content"
  },
  "headers": {
    "User-Agent": "Mozilla/5.0 ..."
  },
  "delay": 2,
  "max_pages": 10,
  "timeout": 30,
  "retry_times": 3
}
```

### 定时配置

```json
{
  "type": "time",
  "name": "每日定时任务",
  "cron": "0 9 * * *",
  "description": "每天早上9点执行"
}
```

## API 接口

### 用户

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/register` | 注册 |
| POST | `/api/login` | 登录 |
| POST | `/api/logout` | 退出 |
| GET | `/api/user/info` | 获取用户信息 |

### 配置文件

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/config/upload` | 上传配置 |
| GET | `/api/config/list` | 配置列表 |
| GET | `/api/config/<id>` | 配置详情 |
| PUT | `/api/config/<id>` | 更新配置 |
| DELETE | `/api/config/<id>` | 删除配置 |

### 爬虫任务

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/task/create` | 创建任务 |
| POST | `/api/task/<id>/start` | 启动 |
| POST | `/api/task/<id>/pause` | 暂停 |
| POST | `/api/task/<id>/resume` | 恢复 |
| POST | `/api/task/<id>/stop` | 停止 |
| GET | `/api/task/list` | 任务列表 |

### 结果与可视化

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/result/<id>` | 获取结果 |
| GET | `/api/result/<id>/visualize` | 生成可视化图表 |

## 数据库设计

| 表名 | 说明 |
|------|------|
| `users` | 用户信息（id, username, password, create_time） |
| `config_files` | 配置文件（id, user_id, name, type, content, create_time） |
| `crawler_tasks` | 爬虫任务（id, user_id, config_id, time_config_id, status, start_time, end_time） |
| `crawler_results` | 爬虫结果（id, task_id, content, is_saved, create_time） |
| `ai_configs` | AI 配置（id, user_id, name, config_type, base_url, api_key, model_name） |
| `visualizations` | 可视化数据（id, result_id, chart_type, data, create_time） |
