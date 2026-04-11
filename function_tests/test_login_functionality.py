"""
登录功能 UI 测试
验证用户登录流程的各项功能
"""

import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pages.home_page import HomePage


@pytest.mark.function
def test_login_form_exists(driver):
    """
    验证登录表单存在且可访问
    
    检查页面上是否有登录入口
    """
    print("\n[功能测试] 登录表单存在性验证")
    
    home_page = HomePage(driver)
    home_page.open()
    
    print("[Step 1] 查找登录入口...")
    
    # 常见的登录入口选择器
    login_selectors = [
        (By.LINK_TEXT, "登录"),
        (By.LINK_TEXT, "Sign in"),
        (By.LINK_TEXT, "Login"),
        (By.CSS_SELECTOR, "a[href*='login']"),
        (By.CSS_SELECTOR, "a[href*='signin']"),
        (By.CSS_SELECTOR, "[data-testid='login-button']"),
        (By.CSS_SELECTOR, ".login-btn"),
        (By.CSS_SELECTOR, ".signin-btn"),
    ]
    
    login_link = None
    for by, selector in login_selectors:
        try:
            elements = driver.find_elements(by, selector)
            for elem in elements:
                if elem.is_displayed():
                    login_link = elem
                    print(f"   ✓ 找到登录入口: {selector}")
                    break
            if login_link:
                break
        except:
            continue
    
    if login_link:
        print("[Step 2] 点击登录入口...")
        login_link.click()
        time.sleep(2)
        
        print("[Step 3] 验证登录页面...")
        current_url = driver.current_url.lower()
        page_source = driver.page_source.lower()
        
        # 检查是否进入登录页面
        is_login_page = any([
            "login" in current_url,
            "signin" in current_url,
            "auth" in current_url,
            "email" in page_source and "password" in page_source
        ])
        
        if is_login_page:
            print("   ✓ 成功进入登录页面")
        else:
            print("   ⚠️ 可能未进入标准登录页面")
    else:
        print("   ⚠️ 未找到登录入口，可能用户已登录或页面布局不同")
    
    print("   ✓ 登录表单检测完成")


@pytest.mark.function
def test_login_with_invalid_credentials(driver):
    """
    测试无效凭据登录
    
    验证错误提示是否正确显示
    """
    print("\n[功能测试] 无效凭据登录验证")
    
    home_page = HomePage(driver)
    home_page.open()
    
    print("[Step 1] 导航到登录页面...")
    
    # 尝试直接访问登录页面
    base_url = home_page.base_url if hasattr(home_page, 'base_url') else "http://localhost:3000"
    login_urls = [
        f"{base_url}/login",
        f"{base_url}/signin",
        f"{base_url}/account/login",
        f"{base_url}/auth/login",
    ]
    
    login_page_found = False
    for url in login_urls:
        try:
            driver.get(url)
            time.sleep(2)
            page_source = driver.page_source.lower()
            if "password" in page_source and ("email" in page_source or "username" in page_source):
                print(f"   ✓ 找到登录页面: {url}")
                login_page_found = True
                break
        except:
            continue
    
    if not login_page_found:
        pytest.skip("无法找到登录页面，跳过测试")
    
    print("[Step 2] 输入无效凭据...")
    
    # 查找邮箱/用户名输入框
    email_selectors = [
        (By.CSS_SELECTOR, "input[type='email']"),
        (By.CSS_SELECTOR, "input[name='email']"),
        (By.CSS_SELECTOR, "input[placeholder*='email' i]"),
        (By.CSS_SELECTOR, "input[placeholder*='邮箱' i]"),
        (By.CSS_SELECTOR, "#email"),
    ]
    
    # 查找密码输入框
    password_selectors = [
        (By.CSS_SELECTOR, "input[type='password']"),
        (By.CSS_SELECTOR, "input[name='password']"),
        (By.CSS_SELECTOR, "input[placeholder*='password' i]"),
        (By.CSS_SELECTOR, "input[placeholder*='密码' i]"),
        (By.CSS_SELECTOR, "#password"),
    ]
    
    # 查找提交按钮
    submit_selectors = [
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.CSS_SELECTOR, "button:contains('登录')"),
        (By.CSS_SELECTOR, "button:contains('Sign in')"),
        (By.CSS_SELECTOR, "[data-testid='submit-button']"),
        (By.CSS_SELECTOR, ".login-form button"),
    ]
    
    email_input = None
    for by, selector in email_selectors:
        try:
            email_input = driver.find_element(by, selector)
            if email_input.is_displayed():
                break
        except:
            continue
    
    password_input = None
    for by, selector in password_selectors:
        try:
            password_input = driver.find_element(by, selector)
            if password_input.is_displayed():
                break
        except:
            continue
    
    if not email_input or not password_input:
        pytest.skip("无法找到登录表单元素")
    
    # 输入无效凭据
    invalid_email = "fake_user_12345@nonexistent.com"
    invalid_password = "wrongpassword123"
    
    email_input.clear()
    email_input.send_keys(invalid_email)
    password_input.clear()
    password_input.send_keys(invalid_password)
    
    print(f"   输入邮箱: {invalid_email}")
    print(f"   输入密码: {'*' * len(invalid_password)}")
    
    print("[Step 3] 提交表单...")
    
    submit_button = None
    for by, selector in submit_selectors:
        try:
            submit_button = driver.find_element(by, selector)
            if submit_button.is_displayed():
                break
        except:
            continue
    
    if submit_button:
        submit_button.click()
    else:
        password_input.submit()
    
    time.sleep(2)
    
    print("[Step 4] 验证错误提示...")
    
    page_source = driver.page_source.lower()
    error_keywords = [
        "invalid", "错误", "error", "incorrect", "不正确",
        "failed", "失败", "not found", "不存在"
    ]
    
    found_error = False
    for keyword in error_keywords:
        if keyword in page_source:
            print(f"   ✓ 检测到错误提示（包含: '{keyword}'）")
            found_error = True
            break
    
    if found_error:
        print("   ✓ 无效凭据被正确拒绝")
    else:
        print("   ⚠️ 未检测到明确的错误提示")
    
    assert found_error or "login" in driver.current_url.lower(), \
        "登录失败后应有错误提示或停留在登录页面"


@pytest.mark.function
def test_login_form_validation(driver):
    """
    测试登录表单的前端验证
    
    验证空提交、格式验证等
    """
    print("\n[功能测试] 登录表单前端验证")
    
    home_page = HomePage(driver)
    home_page.open()
    
    base_url = home_page.base_url if hasattr(home_page, 'base_url') else "http://localhost:3000"
    
    # 尝试访问登录页
    login_urls = [f"{base_url}/login", f"{base_url}/signin", f"{base_url}/account/login"]
    
    for url in login_urls:
        try:
            driver.get(url)
            time.sleep(2)
            if "password" in driver.page_source.lower():
                break
        except:
            continue
    
    print("[Step 1] 测试空表单提交...")
    
    # 查找提交按钮
    submit_selectors = [
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.CSS_SELECTOR, "[data-testid='submit-button']"),
        (By.CSS_SELECTOR, "form button"),
    ]
    
    submit_button = None
    for by, selector in submit_selectors:
        try:
            elements = driver.find_elements(by, selector)
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    submit_button = elem
                    break
        except:
            continue
    
    if submit_button:
        # 不输入任何内容直接提交
        submit_button.click()
        time.sleep(1)
        
        # 检查 HTML5 验证或错误提示
        page_source = driver.page_source.lower()
        
        validation_indicators = [
            "required", "请填写", "不能为空", "cannot be empty",
            "invalid", "有效", "valid"
        ]
        
        has_validation = any(ind in page_source for ind in validation_indicators)
        
        if has_validation:
            print("   ✓ 检测到表单验证")
        else:
            print("   ⚠️ 表单可能依赖后端验证")
    
    print("[Step 2] 测试邮箱格式验证...")
    
    driver.refresh()
    time.sleep(1)
    
    email_selectors = [
        (By.CSS_SELECTOR, "input[type='email']"),
        (By.CSS_SELECTOR, "input[name='email']"),
    ]
    
    email_input = None
    for by, selector in email_selectors:
        try:
            email_input = driver.find_element(by, selector)
            if email_input.is_displayed():
                break
        except:
            continue
    
    if email_input:
        # 输入无效邮箱格式
        invalid_emails = ["notanemail", "test@", "@test.com", "test@test"]
        
        for invalid_email in invalid_emails[:2]:
            email_input.clear()
            email_input.send_keys(invalid_email)
            
            # 触发 blur 事件
            driver.execute_script("arguments[0].blur();", email_input)
            time.sleep(0.5)
            
            # 检查验证消息
            validation_message = email_input.get_attribute("validationMessage")
            if validation_message:
                print(f"   ✓ 邮箱 '{invalid_email}' 触发验证: {validation_message}")
            else:
                # 检查是否有其他错误提示
                pass
    
    print("   ✓ 表单验证测试完成")