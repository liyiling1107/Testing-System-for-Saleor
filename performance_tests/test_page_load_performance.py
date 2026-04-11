"""
页面加载性能测试
使用 Selenium 测量前端页面加载时间
"""

import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from pages.home_page import HomePage
from core_engine.utils import load_test_data


@pytest.mark.performance
def test_homepage_load_time(driver):
    """
    测试首页加载时间
    
    测量 DOM 加载完成和页面完全渲染的时间
    """
    print("\n[性能测试] 首页加载时间")
    
    home_page = HomePage(driver)
    
    iterations = 3
    navigation_times = []
    dom_times = []
    full_load_times = []
    
    for i in range(iterations):
        print(f"\n   第 {i+1} 次测量:")
        
        # 使用 Navigation Timing API 获取精确时间
        start = time.time()
        home_page.open()
        
        # 等待页面稳定
        time.sleep(1)
        
        # 获取 Navigation Timing 数据
        nav_timing = driver.execute_script("""
            var timing = performance.timing;
            var navigationStart = timing.navigationStart;
            return {
                domContentLoaded: timing.domContentLoadedEventEnd - navigationStart,
                loadComplete: timing.loadEventEnd - navigationStart,
                responseTime: timing.responseEnd - timing.requestStart,
                domInteractive: timing.domInteractive - navigationStart
            };
        """)
        
        navigation_times.append(nav_timing["domContentLoaded"])
        dom_times.append(nav_timing["domInteractive"])
        full_load_times.append(nav_timing["loadComplete"])
        
        print(f"      DOM 可交互: {nav_timing['domInteractive']}ms")
        print(f"      DOMContentLoaded: {nav_timing['domContentLoaded']}ms")
        print(f"      完全加载: {nav_timing['loadComplete']}ms")
        print(f"      响应时间: {nav_timing['responseTime']}ms")
        
        # 清除缓存后重新测量
        driver.delete_all_cookies()
        driver.execute_script("window.localStorage.clear();")
    
    avg_nav = sum(navigation_times) / len(navigation_times) / 1000
    avg_dom = sum(dom_times) / len(dom_times) / 1000
    avg_full = sum(full_load_times) / len(full_load_times) / 1000
    
    print(f"\n   平均结果 (共 {iterations} 次):")
    print(f"   - DOM 可交互: {avg_dom:.2f}s")
    print(f"   - DOMContentLoaded: {avg_nav:.2f}s")
    print(f"   - 完全加载: {avg_full:.2f}s")
    
    # 性能阈值
    DOM_THRESHOLD = 5.0  # 5秒
    FULL_THRESHOLD = 8.0  # 8秒
    
    if avg_dom > DOM_THRESHOLD:
        print(f"   ⚠️ DOM 加载时间 {avg_dom:.2f}s 超过阈值 {DOM_THRESHOLD}s")
    else:
        print(f"   ✓ DOM 加载时间在阈值内")
    
    if avg_full > FULL_THRESHOLD:
        print(f"   ⚠️ 完全加载时间 {avg_full:.2f}s 超过阈值 {FULL_THRESHOLD}s")
    else:
        print(f"   ✓ 完全加载时间在阈值内")


@pytest.mark.performance
def test_first_contentful_paint(driver):
    """
    测试首次内容绘制 (FCP) 时间
    """
    print("\n[性能测试] 首次内容绘制 (FCP)")
    
    # 直接使用配置的 URL
    data = load_test_data()
    base_url = data['environment']['base_url']
    
    driver.get(base_url)
    time.sleep(2)  # 等待页面开始渲染
    
    # 使用 Paint Timing API
    paint_timing = driver.execute_script("""
        var paint = performance.getEntriesByType('paint');
        var fcp = paint.find(entry => entry.name === 'first-contentful-paint');
        var fp = paint.find(entry => entry.name === 'first-paint');
        return {
            firstPaint: fp ? fp.startTime : 0,
            firstContentfulPaint: fcp ? fcp.startTime : 0
        };
    """)
    
    fp = paint_timing["firstPaint"] / 1000
    fcp = paint_timing["firstContentfulPaint"] / 1000
    
    print(f"   - First Paint: {fp:.2f}s")
    print(f"   - First Contentful Paint: {fcp:.2f}s")
    
    FCP_THRESHOLD = 3.0
    
    if fcp > 0:
        if fcp < FCP_THRESHOLD:
            print(f"   ✓ FCP {fcp:.2f}s 在阈值 {FCP_THRESHOLD}s 内")
        else:
            print(f"   ⚠️ FCP {fcp:.2f}s 超过阈值 {FCP_THRESHOLD}s")
    else:
        print(f"   ⚠️ 无法获取 FCP 数据（浏览器可能不支持 Paint Timing API）")


@pytest.mark.performance
@pytest.mark.slow
def test_page_load_with_cold_cache(driver):
    """
    测试冷缓存（首次访问）时的页面加载性能
    """
    print("\n[性能测试] 冷缓存页面加载")
    
    data = load_test_data()
    base_url = data['environment']['base_url']
    
    iterations = 3
    load_times = []
    
    for i in range(iterations):
        # 先访问空白页，避免清除缓存时报错
        driver.get("about:blank")
        time.sleep(0.5)
        
        # 清除所有缓存（在 about:blank 页面执行不会报错）
        driver.delete_all_cookies()
        driver.execute_script("""
            try {
                window.localStorage.clear();
                window.sessionStorage.clear();
            } catch(e) {
                console.log('Storage clear error:', e);
            }
        """)
        
        start = time.time()
        driver.get(base_url)
        
        # 等待页面完全加载
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        load_time = time.time() - start
        load_times.append(load_time)
        
        print(f"   第 {i+1} 次冷启动: {load_time:.2f}s")
    
    avg_load = sum(load_times) / len(load_times)
    
    print(f"\n   平均冷启动时间: {avg_load:.2f}s")
    
    COLD_START_THRESHOLD = 10.0
    
    if avg_load < COLD_START_THRESHOLD:
        print(f"   ✓ 冷启动时间在阈值 {COLD_START_THRESHOLD}s 内")
    else:
        print(f"   ⚠️ 冷启动时间 {avg_load:.2f}s 超过阈值")


@pytest.mark.performance
def test_resource_load_timing(driver):
    """
    分析页面资源加载时间
    
    检查图片、CSS、JS 等资源的加载耗时
    """
    print("\n[性能测试] 资源加载时间分析")
    
    home_page = HomePage(driver)
    home_page.open()
    
    # 获取所有资源加载时间
    resources = driver.execute_script("""
        var resources = performance.getEntriesByType('resource');
        var result = [];
        for (var i = 0; i < resources.length; i++) {
            var r = resources[i];
            result.push({
                name: r.name,
                type: r.initiatorType,
                duration: r.duration,
                size: r.transferSize || 0
            });
        }
        return result;
    """)
    
    # 分类统计
    by_type = {}
    slow_resources = []
    
    for r in resources:
        rtype = r["type"]
        duration = r["duration"]
        
        if rtype not in by_type:
            by_type[rtype] = {"count": 0, "total_time": 0, "max_time": 0}
        
        by_type[rtype]["count"] += 1
        by_type[rtype]["total_time"] += duration
        by_type[rtype]["max_time"] = max(by_type[rtype]["max_time"], duration)
        
        if duration > 1000:  # 超过 1 秒的资源
            slow_resources.append(r)
    
    print("\n   资源类型统计:")
    for rtype, stats in by_type.items():
        avg_time = stats["total_time"] / stats["count"] if stats["count"] > 0 else 0
        print(f"   - {rtype}: {stats['count']} 个, 平均 {avg_time:.0f}ms, 最慢 {stats['max_time']:.0f}ms")
    
    if slow_resources:
        print(f"\n   ⚠️ 加载缓慢的资源 (>{1000}ms):")
        for r in slow_resources[:5]:
            name = r["name"].split("/")[-1][:50]
            print(f"      - {name}: {r['duration']:.0f}ms")
    else:
        print(f"\n   ✓ 所有资源加载时间均在 1 秒内")