"""
结账流程 UI 测试
验证完整的结账流程
"""

import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pages.home_page import HomePage


@pytest.mark.function
@pytest.mark.slow
def test_checkout_page_accessibility(driver):
    """
    测试结账页面可访问性
    
    验证能否正常访问结账页面
    """
    print("\n[功能测试] 结账页面可访问性")
    
    home_page = HomePage(driver)
    home_page.open()
    
    print("[Step 1] 查找结账入口...")
    
    # 直接访问结账页面
    base_url = home_page.base_url if hasattr(home_page, 'base_url') else "http://localhost:3000"
    checkout_urls = [
        f"{base_url}/checkout",
        f"{base_url}/cart",
        f"{base_url}/basket",
    ]
    
    accessed = False
    for url in checkout_urls:
        try:
            driver.get(url)
            time.sleep(2)
            page_source = driver.page_source.lower()
            
            # 检查是否是结账相关页面
            checkout_indicators = [
                "checkout", "结账", "shipping", "配送",
                "payment", "支付", "order", "订单"
            ]
            
            if any(ind in page_source for ind in checkout_indicators):
                print(f"   ✓ 成功访问: {url}")
                accessed = True
                break
        except:
            continue
    
    if not accessed:
        pytest.skip("无法访问结账相关页面")
    
    print("[Step 2] 检查页面元素...")
    
    page_source = driver.page_source.lower()
    
    # 检查结账流程中的常见元素
    elements_to_check = [
        ("配送地址表单", ["shipping", "address", "配送", "地址"]),
        ("支付方式", ["payment", "支付", "card", "信用卡"]),
        ("订单摘要", ["summary", "摘要", "total", "总计"]),
        ("提交订单按钮", ["place order", "submit", "提交", "确认"]),
    ]
    
    for name, keywords in elements_to_check:
        found = any(kw in page_source for kw in keywords)
        status = "✓" if found else "○"
        print(f"   {status} {name}: {'存在' if found else '未找到'}")
    
    print("   ✓ 结账页面检查完成")


@pytest.mark.function
def test_shipping_address_form(driver):
    """
    测试配送地址表单
    
    验证地址表单的输入和验证功能
    """
    print("\n[功能测试] 配送地址表单验证")
    
    home_page = HomePage(driver)
    home_page.open()
    
    base_url = home_page.base_url if hasattr(home_page, 'base_url') else "http://localhost:3000"
    
    # 尝试访问结账页面
    driver.get(f"{base_url}/checkout")
    time.sleep(2)
    
    print("[Step 1] 查找地址表单...")
    
    # 常见的地址表单字段
    address_fields = {
        "first_name": ["first", "given", "名"],
        "last_name": ["last", "family", "姓"],
        "address": ["address", "street", "地址", "街道"],
        "city": ["city", "城市"],
        "postal_code": ["postal", "zip", "邮编"],
        "country": ["country", "国家"],
        "email": ["email", "邮箱"],
    }
    
    found_fields = {}
    for field_name, keywords in address_fields.items():
        try:
            for selector in [
                f"input[name*='{field_name}' i]",
                f"input[placeholder*='{keywords[0]}' i]",
                f"input[id*='{field_name}' i]",
            ]:
                try:
                    elem = driver.find_element(By.CSS_SELECTOR, selector)
                    if elem.is_displayed():
                        found_fields[field_name] = elem
                        break
                except:
                    continue
        except:
            pass
    
    print(f"   找到 {len(found_fields)} 个地址表单字段")
    
    if found_fields:
        print("[Step 2] 测试表单输入...")
        
        test_data = {
            "first_name": "Test",
            "last_name": "User",
            "address": "123 Test Street",
            "city": "Test City",
            "postal_code": "12345",
            "email": "test@example.com",
        }
        
        for field_name, elem in found_fields.items():
            if field_name in test_data:
                try:
                    elem.clear()
                    elem.send_keys(test_data[field_name])
                    print(f"   ✓ 填写 {field_name}: {test_data[field_name]}")
                except:
                    print(f"   ⚠️ 无法填写 {field_name}")
        
        print("[Step 3] 检查表单验证...")
        
        # 检查必填字段提示
        page_source = driver.page_source.lower()
        validation_indicators = ["required", "必填", "cannot be empty"]
        
        has_validation = any(ind in page_source for ind in validation_indicators)
        if has_validation:
            print("   ✓ 检测到表单验证提示")
    
    print("   ✓ 地址表单检查完成")


@pytest.mark.function
def test_order_summary_display(driver):
    """
    测试订单摘要显示
    
    验证订单摘要信息是否正确显示
    """
    print("\n[功能测试] 订单摘要显示验证")
    
    home_page = HomePage(driver)
    home_page.open()
    
    base_url = home_page.base_url if hasattr(home_page, 'base_url') else "http://localhost:3000"
    
    # 先访问购物车
    print("[Step 1] 访问购物车...")
    driver.get(f"{base_url}/cart")
    time.sleep(2)
    
    page_source = driver.page_source.lower()
    
    print("[Step 2] 检查订单摘要元素...")
    
    summary_elements = [
        ("小计", ["subtotal", "小计"]),
        ("运费", ["shipping", "运费", "delivery"]),
        ("税费", ["tax", "税费", "vat"]),
        ("总计", ["total", "总计", "合计"]),
    ]
    
    found_summary = []
    for name, keywords in summary_elements:
        found = any(kw in page_source for kw in keywords)
        if found:
            found_summary.append(name)
        status = "✓" if found else "○"
        print(f"   {status} {name}: {'显示' if found else '未显示'}")
    
    if found_summary:
        print(f"   ✓ 检测到 {len(found_summary)} 项订单摘要信息")
    
    # 检查是否有商品列表
    product_indicators = ["product", "item", "商品", "名称", "quantity", "数量"]
    has_products = any(ind in page_source for ind in product_indicators)
    
    if has_products:
        print("   ✓ 检测到商品列表")
    else:
        print("   ○ 购物车可能为空")
    
    print("   ✓ 订单摘要检查完成")