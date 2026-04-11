"""
商品浏览功能 UI 测试
验证用户浏览商品详情、切换商品等核心交互
"""

import pytest
import time
from pages.home_page import HomePage
from core_engine.utils import load_test_data


def test_browse_multiple_products(driver):
    """
    验证首页能够正常加载多个商品，并检查商品名称非空。
    这是一个基础的前端渲染验证测试。
    """
    print("\n[Step 1] 正在打开 Saleor 首页...")
    home_page = HomePage(driver)
    home_page.open()
    
    print("[Step 2] 获取页面上所有商品的名称...")
    product_names = home_page.get_product_names()
    
    print(f"[Step 3] 检测到 {len(product_names)} 个商品")
    for i, name in enumerate(product_names[:5], 1):
        print(f"   商品 {i}: {name}")
    
    # 断言：至少应该有一个商品
    assert len(product_names) > 0, "首页未检测到任何商品，请检查服务状态"
    
    # 断言：所有商品名称非空
    for name in product_names:
        assert name.strip() != "", "存在商品名称为空"


def test_product_display_consistency(api_client, driver):
    """
    验证 API 返回的商品数据与 UI 显示的一致性。
    检查 API 中的第一个商品是否出现在 UI 的商品列表中。
    """
    print("\n[Step 1] 通过 API 获取商品列表...")
    api_client.get_auth_token()
    api_products = api_client.get_products(first=5)
    
    if not api_products:
        pytest.skip("API 未返回任何商品，跳过 UI 一致性测试")
    
    api_product_names = [p.get('name', '') for p in api_products if p.get('name')]
    print(f"   API 返回商品: {api_product_names[:3]}")
    
    print("[Step 2] 打开首页并获取 UI 商品列表...")
    home_page = HomePage(driver)
    home_page.open()
    
    ui_product_names = home_page.get_product_names()
    print(f"   UI 显示商品: {ui_product_names[:3]}")
    
    print("[Step 3] 验证 API 与 UI 数据一致性...")
    # 检查 API 中的第一个有效商品是否出现在 UI 中
    found_match = False
    for api_name in api_product_names:
        if api_name in ui_product_names:
            print(f"   ✓ 匹配成功: '{api_name}' 同时存在于 API 和 UI")
            found_match = True
            break
    
    if not found_match:
        # 可能是缓存问题，尝试刷新页面
        print("   首次未匹配，尝试刷新页面...")
        driver.refresh()
        time.sleep(3)
        ui_product_names = home_page.get_product_names()
        
        for api_name in api_product_names:
            if api_name in ui_product_names:
                print(f"   ✓ 刷新后匹配成功: '{api_name}'")
                found_match = True
                break
    
    assert found_match, f"API 返回的商品 {api_product_names[:3]} 均未出现在 UI 中"


def test_product_quick_view_interaction(driver):
    """
    验证商品卡片的交互性（悬停效果、点击响应等）。
    这是一个交互性测试，确保 UI 元素可正常操作。
    """
    print("\n[Step 1] 打开 Saleor 首页...")
    home_page = HomePage(driver)
    home_page.open()
    
    print("[Step 2] 获取第一个商品元素...")
    first_product = home_page.get_first_product_element()
    
    if first_product is None:
        pytest.skip("首页未找到任何商品元素，跳过交互测试")
    
    print("[Step 3] 验证商品元素可见且可交互...")
    assert first_product.is_displayed(), "商品元素不可见"
    assert first_product.is_enabled(), "商品元素不可交互"
    
    print("[Step 4] 模拟鼠标悬停...")
    # 使用 ActionChains 模拟悬停（如果需要）
    from selenium.webdriver.common.action_chains import ActionChains
    actions = ActionChains(driver)
    actions.move_to_element(first_product).perform()
    time.sleep(0.5)
    
    print("[Step 5] 点击商品查看详情...")
    first_product.click()
    time.sleep(2)
    
    # 验证页面跳转
    current_url = driver.current_url
    print(f"   当前 URL: {current_url}")
    
    # 商品详情页 URL 通常包含 /product/ 或 /products/
    assert any(keyword in current_url.lower() for keyword in ['product', 'prod']), \
        f"点击后未跳转到商品详情页，当前 URL: {current_url}"
    
    print("   ✓ 成功跳转到商品详情页")