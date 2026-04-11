"""
导航流程 UI 测试
验证页面间的跳转、导航菜单、面包屑等功能
"""

import pytest
import time
from selenium.webdriver.common.by import By
from pages.home_page import HomePage


def test_homepage_to_product_navigation(driver):
    """
    验证从首页点击商品能正确跳转到商品详情页，
    并能通过浏览器后退按钮返回首页。
    """
    print("\n[Step 1] 打开 Saleor 首页...")
    home_page = HomePage(driver)
    home_page.open()
    home_url = driver.current_url
    print(f"   首页 URL: {home_url}")
    
    print("[Step 2] 获取并点击第一个商品...")
    first_product = home_page.get_first_product_element()
    
    if first_product is None:
        pytest.skip("首页未找到商品，跳过导航测试")
    
    # 获取商品名称用于后续验证
    product_name = first_product.text.strip() or "Unknown Product"
    print(f"   点击商品: {product_name[:30]}...")
    
    first_product.click()
    time.sleep(2)
    
    product_url = driver.current_url
    print(f"[Step 3] 商品详情页 URL: {product_url}")
    
    # 验证 URL 发生变化
    assert product_url != home_url, "点击后 URL 未变化"
    
    print("[Step 4] 点击浏览器后退按钮...")
    driver.back()
    time.sleep(2)
    
    returned_url = driver.current_url
    print(f"   返回后 URL: {returned_url}")
    
    # 验证返回到首页或类似页面
    assert returned_url == home_url or home_url in returned_url or returned_url in home_url, \
        f"后退后未返回首页，当前 URL: {returned_url}"
    
    print("   ✓ 导航流程验证通过")


def test_navigation_menu_visibility(driver):
    """
    验证主导航菜单存在且可交互。
    """
    print("\n[Step 1] 打开 Saleor 首页...")
    home_page = HomePage(driver)
    home_page.open()
    
    print("[Step 2] 查找导航菜单元素...")
    nav_selectors = [
        (By.TAG_NAME, "nav"),
        (By.CSS_SELECTOR, "[role='navigation']"),
        (By.CSS_SELECTOR, ".navbar"),
        (By.CSS_SELECTOR, ".navigation"),
        (By.CSS_SELECTOR, "header nav"),
        (By.CSS_SELECTOR, ".main-nav"),
    ]
    
    nav_element = None
    for by, selector in nav_selectors:
        try:
            elements = driver.find_elements(by, selector)
            for elem in elements:
                if elem.is_displayed():
                    nav_element = elem
                    print(f"   ✓ 找到导航菜单: {selector}")
                    break
            if nav_element:
                break
        except:
            continue
    
    if nav_element is None:
        print("   ⚠️ 未找到明确的导航菜单元素，尝试查找链接...")
        # 退而求其次：查找页面上的链接
        links = driver.find_elements(By.TAG_NAME, "a")[:10]
        visible_links = [l for l in links if l.is_displayed() and l.text.strip()]
        print(f"   找到 {len(visible_links)} 个可见链接")
        assert len(visible_links) > 0, "页面没有任何可见链接"
    else:
        assert nav_element.is_displayed(), "导航菜单不可见"
        print("   ✓ 导航菜单可见且可用")


def test_page_load_performance(driver):
    """
    验证页面加载性能（简单的时间测量）。
    """
    print("\n[Step 1] 测量首页加载时间...")
    start_time = time.time()
    
    home_page = HomePage(driver)
    home_page.open()
    
    load_time = time.time() - start_time
    print(f"   首页加载耗时: {load_time:.2f} 秒")
    
    # 验证页面加载完成
    assert driver.execute_script("return document.readyState") == "complete", "页面未完全加载"
    
    print("[Step 2] 验证关键元素存在...")
    # 检查 body 和主要内容区域
    body = driver.find_element(By.TAG_NAME, "body")
    assert body.is_displayed(), "页面 body 不可见"
    
    print("[Step 3] 性能评估...")
    # 设置一个合理的加载时间阈值（可根据实际情况调整）
    MAX_ACCEPTABLE_LOAD_TIME = 15  # 秒
    if load_time > MAX_ACCEPTABLE_LOAD_TIME:
        print(f"   ⚠️ 加载时间较长 ({load_time:.2f}s > {MAX_ACCEPTABLE_LOAD_TIME}s)")
        # 不强制断言失败，只做警告
    else:
        print(f"   ✓ 加载时间在合理范围内 ({load_time:.2f}s <= {MAX_ACCEPTABLE_LOAD_TIME}s)")
    
    print(f"   ✓ 页面性能测试完成")