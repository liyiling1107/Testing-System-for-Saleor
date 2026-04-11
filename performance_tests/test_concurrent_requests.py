"""
并发请求性能测试
验证 API 在高并发场景下的表现
"""

import pytest
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from core_engine.saleor_api import SaleorAPI


def single_request(api_client, query, variables=None):
    """执行单次请求并返回响应时间"""
    start = time.time()
    result = api_client.post_graphql(query, variables)
    elapsed = time.time() - start
    return elapsed, result


@pytest.mark.performance
@pytest.mark.slow
def test_concurrent_shop_query(api_client):
    """
    测试并发查询店铺信息的性能
    
    模拟 10 个并发用户同时查询
    """
    print("\n[性能测试] 并发店铺查询 (10 并发)")
    
    query = """
    query {
        shop {
            name
            domain {
                host
            }
        }
    }
    """
    
    concurrent_users = 10
    requests_per_user = 5
    total_requests = concurrent_users * requests_per_user
    
    print(f"   并发数: {concurrent_users}")
    print(f"   每用户请求数: {requests_per_user}")
    print(f"   总请求数: {total_requests}")
    
    times = []
    failures = 0
    
    def worker(worker_id):
        """工作线程函数"""
        local_times = []
        local_failures = 0
        for i in range(requests_per_user):
            elapsed, result = single_request(api_client, query)
            local_times.append(elapsed)
            if not result.get("data", {}).get("shop"):
                local_failures += 1
        return worker_id, local_times, local_failures
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = [executor.submit(worker, i) for i in range(concurrent_users)]
        
        for future in as_completed(futures):
            worker_id, local_times, local_failures = future.result()
            times.extend(local_times)
            failures += local_failures
            print(f"   线程 {worker_id} 完成, 平均响应: {statistics.mean(local_times):.3f}s")
    
    total_time = time.time() - start_time
    
    avg_time = statistics.mean(times)
    min_time = min(times)
    max_time = max(times)
    p95_time = sorted(times)[int(len(times) * 0.95)]
    p99_time = sorted(times)[int(len(times) * 0.99)]
    throughput = total_requests / total_time
    
    print(f"\n   测试结果:")
    print(f"   - 总耗时: {total_time:.2f}s")
    print(f"   - 吞吐量: {throughput:.2f} req/s")
    print(f"   - 失败次数: {failures}")
    print(f"   - 平均响应: {avg_time:.3f}s")
    print(f"   - 最快响应: {min_time:.3f}s")
    print(f"   - 最慢响应: {max_time:.3f}s")
    print(f"   - P95 响应: {p95_time:.3f}s")
    print(f"   - P99 响应: {p99_time:.3f}s")
    
    assert failures == 0, f"有 {failures} 次请求失败"
    assert throughput > 5, f"吞吐量 {throughput:.2f} req/s 过低"
    
    print(f"   ✓ 并发测试通过")


@pytest.mark.performance
@pytest.mark.slow
def test_concurrent_product_queries(api_client):
    """
    测试混合查询的并发性能
    
    模拟用户同时查询不同数据
    """
    print("\n[性能测试] 混合查询并发测试 (5 并发)")
    
    # 定义不同类型的查询
    queries = [
        {
            "name": "shop",
            "query": "query { shop { name } }",
            "variables": None
        },
        {
            "name": "products_10",
            "query": "query { products(first: 10, channel: \"default-channel\") { edges { node { id name } } } }",
            "variables": None
        },
        {
            "name": "categories",
            "query": "query { categories(first: 10) { edges { node { id name } } } }",
            "variables": None
        }
    ]
    
    concurrent_users = 5
    requests_per_user = 10
    
    all_times = []
    failures = 0
    
    def worker(worker_id):
        local_times = []
        local_failures = 0
        for i in range(requests_per_user):
            # 随机选择一种查询
            import random
            q = random.choice(queries)
            elapsed, result = single_request(api_client, q["query"], q["variables"])
            local_times.append(elapsed)
            if "errors" in result:
                local_failures += 1
        return worker_id, local_times, local_failures
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = [executor.submit(worker, i) for i in range(concurrent_users)]
        for future in as_completed(futures):
            worker_id, local_times, local_failures = future.result()
            all_times.extend(local_times)
            failures += local_failures
    
    total_time = time.time() - start_time
    total_requests = concurrent_users * requests_per_user
    
    avg_time = statistics.mean(all_times)
    p95_time = sorted(all_times)[int(len(all_times) * 0.95)]
    throughput = total_requests / total_time
    
    print(f"\n   测试结果:")
    print(f"   - 总请求数: {total_requests}")
    print(f"   - 总耗时: {total_time:.2f}s")
    print(f"   - 吞吐量: {throughput:.2f} req/s")
    print(f"   - 失败次数: {failures}")
    print(f"   - 平均响应: {avg_time:.3f}s")
    print(f"   - P95 响应: {p95_time:.3f}s")
    
    assert failures == 0, f"有 {failures} 次请求失败"
    print(f"   ✓ 混合并发测试通过")


@pytest.mark.performance
def test_rate_limiting_behavior(api_client):
    """
    测试 API 的速率限制行为
    
    快速连续发送请求，观察是否有速率限制
    """
    print("\n[性能测试] 速率限制行为测试")
    
    query = """
    query {
        shop {
            name
        }
    }
    """
    
    request_count = 30
    times = []
    statuses = []
    
    print(f"   快速连续发送 {request_count} 个请求...")
    
    for i in range(request_count):
        start = time.time()
        result = api_client.post_graphql(query)
        elapsed = time.time() - start
        
        times.append(elapsed)
        
        if result.get("data", {}).get("shop"):
            statuses.append("success")
        elif result.get("errors"):
            # 检查是否是速率限制错误
            error_msg = str(result["errors"]).lower()
            if "rate" in error_msg or "limit" in error_msg or "throttle" in error_msg:
                statuses.append("rate_limited")
            else:
                statuses.append("error")
        else:
            statuses.append("error")
    
    success_count = statuses.count("success")
    rate_limited_count = statuses.count("rate_limited")
    error_count = statuses.count("error")
    
    avg_time = statistics.mean(times) if times else 0
    
    print(f"\n   测试结果:")
    print(f"   - 总请求数: {request_count}")
    print(f"   - 成功: {success_count}")
    print(f"   - 被限流: {rate_limited_count}")
    print(f"   - 错误: {error_count}")
    print(f"   - 平均响应: {avg_time:.3f}s")
    
    if rate_limited_count > 0:
        print(f"   ℹ️ 检测到速率限制 (共 {rate_limited_count} 次)")
    
    # 不强制断言，只记录行为
    print(f"   ✓ 测试完成")