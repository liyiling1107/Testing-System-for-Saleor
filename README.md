```markdown
# SaleorQA_System 自动化测试系统

## 项目简介

本项目是一个针对 **Saleor 电商平台** 的完整 QA 自动化测试管理系统，集成了 API 测试、UI 测试、性能测试、安全测试，并提供可视化的管理后台用于触发测试、查看报告和接收告警。

**技术栈：** Python 3.12 + FastAPI + Pytest + Selenium + GraphQL

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      浏览器前端 (index.html)                  │
│                    http://127.0.0.1:8000                    │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST API / SSE 流式
┌─────────────────────────▼───────────────────────────────────┐
│                 FastAPI 后端 (backend.py)                    │
│        测试调度 · 实时日志 · 报告管理 · 邮件告警               │
└─────────────────────────┬───────────────────────────────────┘
                          │ subprocess.Popen()
┌─────────────────────────▼───────────────────────────────────┐
│                    Pytest 测试执行层                          │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │ API测试  │  UI测试  │ 功能测试  │ 性能测试  │ 安全测试  │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    Saleor 电商平台                            │
│   GraphQL API :8000 │ Storefront :3000 │ Dashboard :9000   │
└─────────────────────────────────────────────────────────────┘
```

**三层设计：**
1. **前端控制台** - 可视化触发测试、查看报告、系统监控
2. **后端服务** - 测试调度、流式日志推送、报告管理、失败邮件告警
3. **测试执行层** - Pytest 组织各类测试用例，生成 HTML 报告

---

## 目录结构（核心文件）

```
Testing-System-for-Saleor-main/
├── app/
│   ├── backend.py              # FastAPI 后端服务入口
│   └── frontend/index.html     # 可视化操作界面
├── core_engine/
│   └── saleor_api.py           # GraphQL API 客户端封装
├── pages/
│   ├── base_page.py            # Page Object 基类
│   └── home_page.py            # 首页对象
├── api_tests/                  # API 接口测试
├── ui_tests/                   # UI 界面测试
├── function_tests/             # 功能回归测试
├── performance_tests/          # 性能与并发测试
├── security_tests/             # 安全渗透测试
├── conftest.py                 # Pytest 配置（fixture、截图、报告）
├── config.json                 # 环境配置（URL、账号）
├── check_products.py           # 商品查询与配置生成工具
├── fix_env.py                  # 测试数据修复脚本
├── requirements.txt            # Python 依赖
└── reports/                    # 测试报告输出目录（自动创建）
```

---

## 运行步骤

### 1. 环境准备

```bash
# 确保 Python 3.12 已安装
python --version

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置文件

编辑 `config.json`，填入你的 Saleor 环境信息：

```json
{
  "baseUrl": "http://localhost:8000",
  "frontend_url": "http://localhost:3000",
  "dashboard_url": "http://localhost:9000",
  "admin_user": {
    "email": "admin@example.com",
    "password": "admin123"
  }
}
```

### 3. 修改 ChromeDriver 路径

编辑 `conftest.py` 第 51 行左右，将路径改为你的实际路径：

```python
driver = webdriver.Chrome(
    service=Service(r"你的chromedriver.exe路径"),
    options=options
)
```

### 4. 启动 Saleor 服务

确保 Saleor 的三个服务已运行：
- GraphQL API: `http://localhost:8000`
- Storefront: `http://localhost:3000`
- Dashboard: `http://localhost:9000`

### 5. 验证环境

```bash
# 检查商品数据是否可用
python check_products.py
# 选择 1 查看所有商品，确认有可用商品
```

### 6. 启动 QA 管理系统

```bash
# 启动后端服务
python app/backend.py

# 浏览器打开前端界面
# 直接双击 app/frontend/index.html
```

【图1】QA管理系统主界面

### 7. 运行测试

**方式一：通过前端界面**
- 点击对应测试卡片上的「运行」按钮
- 实时查看终端输出
- 测试完成后点击「报告」查看结果

【图2】测试执行实时日志界面

**方式二：命令行直接运行**
```bash
# API 测试
py -3.12 -m pytest -s api_tests/test_orders.py

# UI 测试
py -3.12 -m pytest -s ui_tests/test_search_functionality.py

# 功能测试
py -3.12 -m pytest -s function_tests/test_login_functionality.py

# 性能测试
py -3.12 -m pytest -s performance_tests/test_api_response_time.py

# 安全测试
py -3.12 -m pytest -s security_tests/test_authentication_security.py
```

---

## 测试套件速查

| 类别 | 脚本 ID | 测试内容 |
|:---|:---|:---|
| API | `orders` | 订单查询、分页、权限 |
| API | `business` | 商品 CRUD、查询性能 |
| API | `full` | 完整生命周期、稳定性 |
| UI | `ui_search` | 搜索框、关键词搜索 |
| UI | `ui_navigation` | 页面导航、后退 |
| UI | `ui_product_browsing` | 商品浏览、一致性 |
| 功能 | `func_login` | 登录表单、无效凭据 |
| 功能 | `func_cart` | 购物车增删改 |
| 功能 | `func_checkout` | 结账流程 |
| 性能 | `perf_api_response` | API 响应时间 |
| 性能 | `perf_concurrent` | 并发请求 |
| 性能 | `perf_page_load` | 页面加载性能 |
| 安全 | `sec_auth` | 认证安全、SQL注入 |
| 安全 | `sec_api` | API安全、CORS、XSS |

---

## 常用辅助命令

```bash
# 检查商品数据并生成配置
python check_products.py
# 选项 4：自动生成 test_data.yaml

# 修复被测试改乱的商品名
python fix_env.py

# 生成带时间戳的 HTML 报告
py -3.12 -m pytest --html=reports/report.html --self-contained-html
```

【图3】测试报告示例

---

## 故障排查

| 问题 | 解决方案 |
|:---|:---|
| Token 获取失败 | 检查 `config.json` 中的 `admin_user` 账号密码 |
| ChromeDriver 报错 | 修改 `conftest.py` 中的驱动路径 |
| 测试跳过（无商品） | 运行 `python check_products.py` 确认数据库有商品 |
| 前端无法连接后端 | 确保 `backend.py` 运行在 `127.0.0.1:8000` |
| 邮件发送失败 | 更新 `backend.py` 中的 QQ 邮箱授权码 |

---

## 扩展开发

**添加新测试用例：**
1. 在对应目录创建测试文件
2. 在 `backend.py` 的 `SCRIPTS` 字典中添加映射
3. 在前端 `index.html` 中添加对应的按钮卡片

**添加新 API 方法：**
在 `core_engine/saleor_api.py` 中参照现有方法添加 GraphQL 查询封装。

---

## 依赖清单（核心）

```
pytest==9.0.2
fastapi==0.135.3
selenium==4.41.0
requests==2.33.1
pytest-html==4.2.0
PyYAML==6.0.3
uvicorn==0.43.0
```