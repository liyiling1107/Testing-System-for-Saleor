import pytest
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
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
    client.get_auth_token() 
    return client

@pytest.fixture(scope="function")
def driver():
    """浏览器驱动初始化"""
    options = webdriver.ChromeOptions()
    # 规避自动化检测
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 如果需要无头模式（不弹出浏览器窗口）可以取消下面一行的注释
    # options.add_argument('--headless') 
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.maximize_window()
    
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

    if report.when == "call" or report.when == "setup":
        xfail = hasattr(report, "wasxfail")
        if (report.skipped and xfail) or (report.failed and not xfail):
            # 尝试从 fixture 中获取 driver
            driver = item.funcargs.get("driver")
            if driver:
                # 生成唯一文件名
                timestamp = datetime.now().strftime("%H%M%S")
                file_name = f"{item.name}_{timestamp}.png"
                img_path = os.path.join(SCREENSHOT_DIR, file_name)
                
                # 保存截图
                driver.get_screenshot_as_file(img_path)
                
                if os.path.exists(img_path):
                    # 使用相对路径嵌入 HTML（确保报告拷贝到别处也能看图）
                    rel_path = os.path.join("screenshots", file_name)
                    html = '<div><img src="%s" alt="screenshot" style="width:300px;height:200px;" ' \
                           'onclick="window.open(this.src)" align="right"/></div>' % rel_path
                    extra.append(pytest_html.extras.html(html))
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
        "Python": "3.12"
    }

def pytest_html_results_table_header(cells):
    """修改报告表格头，移除不必要的列"""
    cells.insert(2, "<th>Description</th>")
    cells.pop()

def pytest_html_results_table_row(report, cells):
    """修改报告表格行内容"""
    description = getattr(report, "description", "")
    cells.insert(2, f"<td>{description}</td>")
    cells.pop()

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """从 docstring 获取测试描述显示在报告中"""
    item._obj.__doc__ = item._obj.__doc__ or "未提供描述"
    item.results_description = item._obj.__doc__.strip()