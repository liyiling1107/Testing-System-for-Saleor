"""
API 响应时间性能测试
验证各 GraphQL 接口的响应速度是否在合理范围内
"""

import pytest
import time
import statistics
from core_engine.saleor_api import SaleorAPI


# 性能阈值配置（单位：秒）
THRESHOLDS = {
    "shop_info": 1.0,        # 店铺信息查询
    "products_list": 2.0,    # 商品列表查询
    "single_product": 1.0,   # 单个商品查询
    "categories": 1.5,       # 分类查询
}


def measure_api_call(api_client, query, variables=None, token=None):
    """测量单次 API 调用的响应时间"""
    start = time.time()
    result = api_client.post_graphql(query, variables, token)
    elapsed = time.time() - start
    return elapsed, result


@pytest.mark.performance
def test_shop_info_response_time(api_client):
    """
    测试店铺信息查询的响应时间
    
    验证 GraphQL 查询 shop 基础信息的速度
    """
    print("\n[性能测试] 店铺信息查询响应时间")
    
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
    
    times = []
    iterations = 5
    
    for i in range(iterations):
        elapsed, result = measure_api_call(api_client, query)
        times.append(elapsed)
        
        if result.get("data", {}).get("shop"):
            print(f"   第 {i+1} 次: {elapsed:.3f}s - ✓ 成功")
        else:
            print(f"   第 {i+1} 次: {elapsed:.3f}s - ✗ 失败")
    
    avg_time = statistics.mean(times)
    min_time = min(times)
    max_time = max(times)
    std_dev = statistics.stdev(times) if len(times) > 1 else 0
    
    print(f"\n   统计结果 (共 {iterations} 次):")
    print(f"   - 平均响应: {avg_time:.3f}s")
    print(f"   - 最快响应: {min_time:.3f}s")
    print(f"   - 最慢响应: {max_time:.3f}s")
    print(f"   - 标准差: {std_dev:.3f}s")
    print(f"   - 阈值: {THRESHOLDS['shop_info']}s")
    
    assert avg_time < THRESHOLDS["shop_info"], \
        f"平均响应时间 {avg_time:.3f}s 超过阈值 {THRESHOLDS['shop_info']}s"


@pytest.mark.performance
def test_products_list_response_time(api_client):
    """
    测试商品列表查询的响应时间
    
    分别测试获取 10、20、50 个商品的响应速度
    """
    print("\n[性能测试] 商品列表查询响应时间")
    
    test_cases = [
        (10, THRESHOLDS["products_list"]),
        (20, THRESHOLDS["products_list"] * 1.2),
        (50, THRESHOLDS["products_list"] * 1.5),
    ]
    
    query = """
    query GetProducts($first: Int!) {
        products(first: $first, channel: "default-channel") {
            edges {
                node {
                    id
                    name
                }
            }
        }
    }
    """
    
    for first, threshold in test_cases:
        print(f"\n   测试获取 {first} 个商品:")
        
        times = []
        iterations = 3
        
        for i in range(iterations):
            elapsed, result = measure_api_call(api_client, query, {"first": first})
            times.append(elapsed)
            
            product_count = len(result.get("data", {}).get("products", {}).get("edges", []))
            print(f"      第 {i+1} 次: {elapsed:.3f}s - 获取 {product_count} 个商品")
        
        avg_time = statistics.mean(times)
        print(f"      平均响应: {avg_time:.3f}s (阈值: {threshold}s)")
        
        if avg_time > threshold:
            print(f"      ⚠️ 警告: 超过阈值")
        else:
            print(f"      ✓ 通过")


@pytest.mark.performance
def test_single_product_response_time(api_client):
    """
    测试单个商品查询的响应时间
    """
    print("\n[性能测试] 单个商品查询响应时间")
    
    # 先获取一个商品 ID
    api_client.get_auth_token()
    products = api_client.get_products(first=1)
    
    if not products:
        pytest.skip("没有可用的商品，跳过测试")
    
    product_id = products[0]["id"]
    product_name = products[0]["name"]
    print(f"   测试商品: {product_name}")
    
    query = """
    query GetProduct($id: ID!) {
        product(id: $id) {
            id
            name
            description
            pricing {
                priceRange {
                    start {
                        gross {
                            amount
                            currency
                        }
                    }
                }
            }
        }
    }
    """
    
    times = []
    iterations = 10
    
    for i in range(iterations):
        elapsed, result = measure_api_call(api_client, query, {"id": product_id})
        times.append(elapsed)
    
    avg_time = statistics.mean(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"\n   统计结果 (共 {iterations} 次):")
    print(f"   - 平均响应: {avg_time:.3f}s")
    print(f"   - 最快响应: {min_time:.3f}s")
    print(f"   - 最慢响应: {max_time:.3f}s")
    print(f"   - 阈值: {THRESHOLDS['single_product']}s")
    
    assert avg_time < THRESHOLDS["single_product"], \
        f"平均响应时间 {avg_time:.3f}s 超过阈值 {THRESHOLDS['single_product']}s"


@pytest.mark.performance
@pytest.mark.slow
def test_api_endurance(api_client):
    """
    测试 API 的持续稳定性
    
    连续发送 50 次请求，观察响应时间是否稳定
    """
    print("\n[性能测试] API 持续稳定性测试 (50 次连续请求)")
    
    query = """
    query {
        shop {
            name
        }
    }
    """
    
    times = []
    failures = 0
    
    for i in range(50):
        elapsed, result = measure_api_call(api_client, query)
        times.append(elapsed)
        
        if result.get("data", {}).get("shop"):
            if (i + 1) % 10 == 0:
                print(f"   已完成 {i+1} 次请求...")
        else:
            failures += 1
            print(f"   ✗ 第 {i+1} 次请求失败")
    
    avg_time = statistics.mean(times)
    min_time = min(times)
    max_time = max(times)
    
    # 计算后 25 次 vs 前 25 次的平均时间（检测性能衰减）
    first_half_avg = statistics.mean(times[:25])
    second_half_avg = statistics.mean(times[25:])
    degradation = ((second_half_avg - first_half_avg) / first_half_avg) * 100
    
    print(f"\n   测试结果:")
    print(f"   - 总请求数: 50")
    print(f"   - 失败次数: {failures}")
    print(f"   - 平均响应: {avg_time:.3f}s")
    print(f"   - 最快响应: {min_time:.3f}s")
    print(f"   - 最慢响应: {max_time:.3f}s")
    print(f"   - 前半段平均: {first_half_avg:.3f}s")
    print(f"   - 后半段平均: {second_half_avg:.3f}s")
    print(f"   - 性能衰减: {degradation:+.1f}%")
    
    assert failures == 0, f"有 {failures} 次请求失败"
    
    if degradation > 20:
        print(f"   ⚠️ 警告: 性能衰减超过 20%")
    else:
        print(f"   ✓ 性能稳定")