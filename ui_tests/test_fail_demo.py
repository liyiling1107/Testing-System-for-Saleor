import pytest
from playwright.sync_api import Page, expect

def test_mail_alert_on_failure(page: Page):
    """
    故意失败的测试用例：
    访问 Saleor Demo 站，断言标题是一个错误的值。
    """
    print("\n[开始测试] 正在访问 Saleor Demo 站点...")
    page.goto("https://demo.saleor.io/", timeout=60000)
    
    actual_title = page.title()
    expected_title = "这是一个错误的标题_用来触发邮件"
    
    print(f"[验证中] 实际标题是: {actual_title}")
    
    # 这里会抛出 AssertionError，导致 pytest 返回非零状态码
    assert actual_title == expected_title, f"失败触发成功！预期标题 '{expected_title}'，但实际是 '{actual_title}'"

# 运行命令： pytest test_fail_demo.py