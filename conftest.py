import pytest
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from core_engine.saleor_api import SaleorAPI

# ====================================================
# 1. 路径配置
# ====================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.join(BASE_DIR, "reports")
SCREENSHOT_DIR = os.path.join(REPORT_DIR, "screenshots")

# 确保必要的目录存在
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# ====================================================
# 2. 基础 Fixtures
# ====================================================

@pytest.fixture(scope="session")
def api_client():
    """全局 API 客户端，自动登录"""
    client = SaleorAPI()
    
    # 添加错误处理和日志
    print(f"\n[API] 正在连接 Saleor API...")
    print(f"[API] 配置的 baseUrl: {client.config.get('baseUrl')}")
    print(f"[API] 实际使用的 API URL: {client.base_url}")
    
    try:
        token = client.get_auth_token()
        if token is None:
            print(f"[API] ⚠️ 警告: 获取 Token 失败，将使用未认证模式")
            # 不跳过测试，让测试自己处理认证失败的情况
        else:
            print(f"[API] ✓ Token 获取成功: {token[:20]}...")
    except Exception as e:
        print(f"[API] ❌ 认证异常: {e}")
        # 不抛出异常，让测试继续执行但可能失败
    
    return client

@pytest.fixture(scope="function")
def driver():
    """浏览器驱动初始化 - 增加超时配置"""
    options = Options()
    
    # 规避自动化检测
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 设置窗口大小
    options.add_argument('--window-size=1920,1080')
    
    # 增加超时相关配置
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--headless')  # 关键：无头模式
    
    # 如果后端调用时想无头运行（不弹出浏览器窗口），取消下面一行的注释
    # options.add_argument('--headless')
    
    # 本地调试时禁用 GPU 加速（避免某些显示问题）
    options.add_argument('--disable-gpu')
    
    driver = webdriver.Chrome(
        service=Service(r"C:\Users\19868\Desktop\毕业设计\SaleorQA_System\chromedriver.exe"),
        options=options
    )
    
    # 关键：设置各种超时时间
    driver.set_page_load_timeout(30)  # 页面加载超时30秒
    driver.set_script_timeout(30)      # 脚本执行超时30秒
    driver.implicitly_wait(10)         # 隐式等待10秒
    
    yield driver
    
    driver.quit()

# ====================================================
# 3. 报告增强：失败自动截图并嵌入 HTML
# ====================================================

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """实现失败截图并关联到 pytest-html 报告"""
    pytest_html = item.config.pluginmanager.getplugin("html")
    outcome = yield
    report = outcome.get_result()
    extra = getattr(report, "extra", [])
    
    # 截图功能只对使用了 driver 的测试有效
    if report.when == "call" and report.failed:
        # 尝试从 fixture 中获取 driver
        driver = item.funcargs.get("driver")
        
        if driver:
            # 生成唯一文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # 清理文件名中的非法字符
            safe_name = item.name.replace("[", "_").replace("]", "_").replace("/", "_")
            file_name = f"{safe_name}_{timestamp}.png"
            img_path = os.path.join(SCREENSHOT_DIR, file_name)
            
            # 保存截图
            try:
                driver.save_screenshot(img_path)
                print(f"\n📸 截图已保存: {img_path}")
                
                if os.path.exists(img_path):
                    # 使用相对路径嵌入 HTML
                    rel_path = os.path.join("screenshots", file_name)
                    html = '<div><img src="%s" alt="screenshot" style="width:300px;height:200px;" ' \
                           'onclick="window.open(this.src)" align="right"/></div>' % rel_path
                    extra.append(pytest_html.extras.html(html))
            except Exception as e:
                print(f"\n⚠️ 截图保存失败: {e}")
        else:
            # 如果测试没有 driver 但失败了，也记录下来
            print(f"\n⚠️ 测试 [{item.name}] 失败，但没有 driver fixture 可截图")
    
    report.extra = extra

# ====================================================
# 4. 报告自定义配置
# ====================================================

def pytest_configure(config):
    """配置报告名称和环境信息"""
    # 如果没有指定输出路径，默认生成在 reports 文件夹下
    if not config.getoption("htmlpath"):
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        config.option.htmlpath = os.path.join(REPORT_DIR, f"Execution_Report_{now}.html")
        config.option.self_contained_html = True

    # 自定义 Environment 表格内容
    config._metadata = {
        "项目名称": "Saleor 自动化测试系统",
        "测试目的": "毕业设计全链路同步验证",
        "后端接口": "Saleor GraphQL API",
        "前端架构": "Next.js Storefront",
        "Python": "3.12",
        "浏览器": "Chrome"
    }
    
    # 添加 pytest-timeout 配置（如果安装了）
    if hasattr(config, 'option'):
        if not hasattr(config.option, 'timeout'):
            config.option.timeout = 60  # 全局超时60秒

    # ========== 新增：注册自定义标记 ==========
    config.addinivalue_line("markers", "performance: 性能测试标记")
    config.addinivalue_line("markers", "slow: 慢速测试标记")
    config.addinivalue_line("markers", "security: 安全测试标记")
    config.addinivalue_line("markers", "function: 功能测试标记")

def pytest_html_results_table_header(cells):
    """修改报告表格头，添加描述列"""
    cells.insert(2, "<th>Description</th>")

def pytest_html_results_table_row(report, cells):
    """修改报告表格行内容，添加描述"""
    description = getattr(report, "description", "")
    cells.insert(2, f"<td>{description}</td>")

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """从 docstring 获取测试描述显示在报告中"""
    # 获取测试函数的文档字符串
    docstring = item._obj.__doc__
    if docstring:
        item._obj.__doc__ = docstring.strip()
    else:
        item._obj.__doc__ = "未提供描述"
        
    # 为测试添加自定义标记（可选）
    if hasattr(item, 'callspec'):
        params = item.callspec.params
        if params:
            param_str = ", ".join([f"{k}={v}" for k, v in params.items()])
            item._obj.__doc__ = f"{item._obj.__doc__}\n参数: {param_str}"