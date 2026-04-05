import pytest
import time
import logging
import os
from pages.home_page import HomePage
from core_engine.utils import load_test_data

def test_api_modify_and_ui_verify(api_client, driver):
    """
    全链路同步测试（最终稳定版）：
    验证从 API 修改商品名到 UI 自动刷新显示的完整业务流。
    去除了所有可能导致编码问题的表情图标。
    """
    # 0. 数据初始化
    data = load_test_data()
    sync_config = data['products']['sync_flow']
    NAME_A = sync_config['default_name']
    NAME_B = sync_config['target_name']
    CHECK_INTERVAL = sync_config['check_interval']
    MAX_WAIT = sync_config['max_wait']

    api_client.get_auth_token()
    home_page = HomePage(driver)
    # 减少 Selenium 无关日志干扰
    logging.getLogger("selenium").setLevel(logging.WARNING)

    # 1. 数据库状态预检
    print(f"\n[Step 1] 正在同步数据库状态...", end='', flush=True)
    target_id = api_client.get_product_id_by_name(NAME_A) or api_client.get_product_id_by_name(NAME_B)
    assert target_id, f"错误：找不到商品 '{NAME_A}' 或 '{NAME_B}'"
    
    db_name = api_client.get_product_name_by_id(target_id)
    current_db = db_name if db_name else NAME_A
    START_NAME, TARGET_NAME = (NAME_A, NAME_B) if current_db == NAME_A else (NAME_B, NAME_A)
    print(f" OK! ({START_NAME} -> {TARGET_NAME})")

    try:
        # 2. API 修改操作
        print(f"[Step 2] 执行 API 修改请求...", end='', flush=True)
        modify_res = api_client.update_product_name(target_id, TARGET_NAME)
        assert modify_res, "API 修改请求失败"
        print(f" Done!")

        # 3. UI 自动化轮询验证
        print(f"[Step 3] 开启浏览器并监控 UI (最长 {MAX_WAIT}s)")
        home_page.open()

        t_start = time.time()
        success = False
        actual_ui_name = "INIT"

        while time.time() - t_start < MAX_WAIT:
            elapsed = int(time.time() - t_start)
            try:
                # --- 强力清除缓存组合拳 ---
                # 1. 清除所有 Cookie
                driver.delete_all_cookies()
                # 2. 清除浏览器本地存储
                driver.execute_script("window.localStorage.clear(); window.sessionStorage.clear();")
                # 3. 强制从服务器加载页面（忽略本地缓存）
                driver.execute_script("location.reload(true);")
                
                # 给 React/Next.js 框架一点点渲染时间
                time.sleep(3) 

                raw_name = home_page.get_first_product_name()
                actual_ui_name = raw_name.strip() if (raw_name and raw_name.strip()) else "LOADING..."

                # 将图标替换为纯文字以避开 GBK 编码错误
                status_text = "Waiting" if actual_ui_name != TARGET_NAME else "Done!"
                
                # 打印进度
                print(f"\r   进度: 已运行 {elapsed:3d}s | 状态: {status_text} | UI显示: [{actual_ui_name}]" + " " * 10, end='', flush=True)

                if actual_ui_name == TARGET_NAME:
                    print(f"\n   恭喜 [Success] UI 已在 {elapsed}s 同步完成！")
                    success = True
                    break
            except Exception as e:
                # 轮询中的偶发异常（如刷新瞬间找不到元素）直接跳过
                pass
            
            time.sleep(CHECK_INTERVAL)
        
        # 4. 最终断言
        if not success:
            print(f"\n[Final Check] 正在执行最后一次深度扫描...")
            driver.refresh()
            time.sleep(5)
            final_res = home_page.get_first_product_name()
            actual_ui_name = final_res.strip() if final_res else "EMPTY"
            if actual_ui_name == TARGET_NAME:
                success = True

        assert success, f"同步失败。最终 UI 内容: {actual_ui_name}"

    finally:
        # 5. 环境恢复 (可选：将商品名改回 NAME_A)
        print(f"\n[Cleanup] 还原数据库状态...")
        api_client.update_product_name(target_id, NAME_A)
        print(f"   还原完成: {NAME_A}")