import pytest
import time
import logging
from pages.home_page import HomePage
from core_engine.utils import load_test_data

def test_api_modify_and_ui_verify(api_client, driver):
    """
    全链路同步测试：
    验证从 API 修改商品名到 UI 自动刷新显示的完整业务流。
    使用 get_product_names() 处理多商品扫描。
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

        while time.time() - t_start < MAX_WAIT:
            elapsed = int(time.time() - t_start)
            try:
                driver.refresh()
                # 清除前端 Session 和 LocalStorage 防止干扰
                driver.execute_script("window.localStorage.clear(); window.sessionStorage.clear();")
                time.sleep(2) 

                # 【关键修复】：改用复数方法获取列表
                current_names = home_page.get_product_names()
                
                # 确定显示状态
                if not current_names:
                    display_info = "LOADING..."
                else:
                    display_info = str(current_names[:2]) # 只显示前两个名字预览

                # 检查目标名称是否在当前页面列表中
                is_match = TARGET_NAME in current_names
                status_icon = "等待中" if not is_match else "Done!"
                
                print(f"\r   等待中 已运行: {elapsed:3d}s | 状态: {status_icon} | UI预览: {display_info}" + " " * 40, end='', flush=True)

                if is_match:
                    print(f"\n   恭喜 [Success] UI 已在 {elapsed}s 同步完成！")
                    success = True
                    break
            except Exception:
                pass
            time.sleep(CHECK_INTERVAL)

        # 4. 最终断言
        if not success:
            print(f"\n[Final Check] 正在执行最后一次深度扫描...")
            driver.refresh()
            time.sleep(5)
            final_names = home_page.get_product_names()
            assert TARGET_NAME in final_names, f"超时：UI 在 {MAX_WAIT}s 内未更新为 {TARGET_NAME}"

    finally:
        # 5. 还原数据库 (无论成功失败都执行，且重新获取 Token 防止过期)
        print(f"\n[Cleanup] 还原数据库状态...")
        api_client.get_auth_token() 
        api_client.update_product_name(target_id, START_NAME)
        print(f"   还原完成: {START_NAME}")