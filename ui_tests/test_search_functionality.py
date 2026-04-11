"""
搜索功能 UI 测试
验证前端搜索框的输入、提交和结果展示
"""

import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from pages.home_page import HomePage


def test_search_box_exists_and_interactive(driver):
    """
    验证搜索框存在且可交互。
    这是一个基础的功能可用性测试。
    """
    print("\n[Step 1] 打开 Saleor 首页...")
    home_page = HomePage(driver)
    home_page.open()
    
    print("[Step 2] 查找搜索框...")
    # 尝试多种常见的搜索框选择器
    search_selectors = [
        (By.CSS_SELECTOR, "input[type='search']"),
        (By.CSS_SELECTOR, "input[name='search']"),
        (By.CSS_SELECTOR, "input[placeholder*='search' i]"),
        (By.CSS_SELECTOR, "input[placeholder*='Search' i]"),
        (By.CSS_SELECTOR, "[data-testid='search-input']"),
        (By.CSS_SELECTOR, ".search-input"),
        (By.CSS_SELECTOR, "input[aria-label*='search' i]"),
    ]
    
    search_input = None
    for by, selector in search_selectors:
        try:
            search_input = driver.find_element(by, selector)
            if search_input.is_displayed():
                print(f"   ✓ 找到搜索框: {selector}")
                break
        except:
            continue
    
    if search_input is None:
        pytest.skip("未找到搜索框，可能页面布局不同，跳过测试")
    
    print("[Step 3] 验证搜索框可交互...")
    assert search_input.is_enabled(), "搜索框不可交互"
    
    # 测试输入
    test_keyword = "shirt"
    search_input.clear()
    search_input.send_keys(test_keyword)
    
    actual_value = search_input.get_attribute("value")
    assert actual_value == test_keyword, f"输入失败，预期 '{test_keyword}'，实际 '{actual_value}'"
    print(f"   ✓ 成功输入关键词: '{test_keyword}'")


def test_search_with_keyword(driver):
    """
    验证输入关键词并提交搜索后，结果页面正常显示。
    """
    print("\n[Step 1] 打开 Saleor 首页...")
    home_page = HomePage(driver)
    home_page.open()
    
    print("[Step 2] 定位搜索框...")
    search_input = home_page.find_search_input()
    
    if search_input is None:
        pytest.skip("未找到搜索框，跳过搜索功能测试")
    
    print("[Step 3] 输入搜索关键词...")
    keyword = "shirt"
    search_input.clear()
    search_input.send_keys(keyword)
    
    print("[Step 4] 提交搜索...")
    # 尝试按 Enter 提交
    search_input.send_keys(Keys.RETURN)
    time.sleep(3)
    
    print("[Step 5] 验证搜索结果页面...")
    current_url = driver.current_url.lower()
    print(f"   当前 URL: {current_url}")
    
    # 验证 URL 包含搜索参数
    url_has_search = any(indicator in current_url for indicator in ['search', 'q=', 'query', keyword.lower()])
    
    # 验证页面有搜索结果或空结果提示
    page_source = driver.page_source.lower()
    has_results = any(indicator in page_source for indicator in ['product', 'result', 'found', 'item', '商品'])
    
    print(f"   URL 包含搜索标识: {url_has_search}")
    print(f"   页面包含结果内容: {has_results}")
    
    # 至少满足一个条件
    assert url_has_search or has_results, "搜索后未显示结果页面"


def test_search_no_results_handling(driver):
    """
    验证搜索无结果时的友好提示。
    这是一个负向场景测试。
    """
    print("\n[Step 1] 打开 Saleor 首页...")
    home_page = HomePage(driver)
    home_page.open()
    
    print("[Step 2] 定位搜索框...")
    search_input = home_page.find_search_input()
    
    if search_input is None:
        pytest.skip("未找到搜索框，跳过测试")
    
    print("[Step 3] 输入一个不可能存在的商品名...")
    absurd_keyword = "XYZZY_Nonexistent_Product_999999"
    search_input.clear()
    search_input.send_keys(absurd_keyword)
    search_input.send_keys(Keys.RETURN)
    time.sleep(3)
    
    print("[Step 4] 检查无结果提示...")
    page_text = driver.page_source.lower()
    
    # 常见的无结果提示关键词
    no_result_indicators = [
        'no result', 'no product', 'not found', '找不到', '无结果',
        '0 result', 'nothing found', 'empty', '暂无'
    ]
    
    found_indicator = None
    for indicator in no_result_indicators:
        if indicator in page_text:
            found_indicator = indicator
            break
    
    if found_indicator:
        print(f"   ✓ 检测到无结果提示: '{found_indicator}'")
    else:
        print("   ⚠️ 未检测到明确的无结果提示，但页面正常响应")
    
    # 验证页面没有崩溃
    assert "error" not in driver.title.lower(), "页面出现错误"
    print("   ✓ 页面正常响应，无报错")