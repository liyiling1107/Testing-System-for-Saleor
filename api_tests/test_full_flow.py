"""
全量回归 API 测试
验证完整的 API 端到端业务流程
"""

import pytest
import time
import logging


def get_first_available_product(api_client):
    """
    通过 API 获取第一个可用商品
    """
    query = """
    query GetFirstProduct {
        products(first: 1, channel: "default-channel") {
            edges {
                node {
                    id
                    name
                }
            }
        }
    }
    """
    
    result = api_client.post_graphql(query, token=api_client.token)
    edges = result.get("data", {}).get("products", {}).get("edges", [])
    
    if edges:
        node = edges[0]["node"]
        return node["id"], node["name"]
    
    return None, None


def get_product_name_by_id(api_client, product_id):
    """
    通过 API 获取商品名称（带 channel 参数）
    """
    query = """
    query GetProduct($id: ID!) {
        product(id: $id, channel: "default-channel") {
            name
        }
    }
    """
    
    result = api_client.post_graphql(query, {"id": product_id}, token=api_client.token)
    product = result.get("data", {}).get("product")
    
    if product:
        return product["name"]
    return None


@pytest.mark.api
def test_full_product_lifecycle(api_client):
    """
    完整商品生命周期测试
    """
    print("\n[API 测试] 完整商品生命周期验证")
    
    api_client.get_auth_token()
    logging.getLogger("core_engine").setLevel(logging.WARNING)

    # 1. 获取商品
    print(f"\n[Step 1] 获取测试商品...")
    target_id, current_name = get_first_available_product(api_client)
    
    assert target_id, "无法获取商品"
    print(f"   ✓ 商品 ID: {target_id}")
    print(f"   ✓ 商品名称: {current_name}")
    
    # 2. 更新商品
    suffix = int(time.time()) % 1000
    NEW_NAME = f"{current_name} [Full{suffix}]"
    
    print(f"\n[Step 2] 更新商品名称...")
    assert api_client.update_product_name(target_id, NEW_NAME), "更新失败"
    print(f"   ✓ 更新成功: {NEW_NAME}")
    
    # 3. 验证更新
    print(f"\n[Step 3] 验证更新结果...")
    time.sleep(1)
    updated_name = get_product_name_by_id(api_client, target_id)
    assert updated_name == NEW_NAME, f"验证失败: {updated_name} != {NEW_NAME}"
    print(f"   ✓ 验证成功")
    
    # 4. 还原
    print(f"\n[Step 4] 还原商品名称...")
    api_client.update_product_name(target_id, current_name)
    print(f"   ✓ 还原完成")
    
    print("\n   ✅ 完整商品生命周期验证通过")


@pytest.mark.api
def test_categories_query(api_client):
    """
    分类查询测试
    """
    print("\n[API 测试] 分类查询验证")
    
    query = """
    query {
        categories(first: 10) {
            edges {
                node {
                    id
                    name
                    slug
                }
            }
        }
    }
    """
    
    print(f"\n[Step 1] 查询分类列表...")
    result = api_client.post_graphql(query)
    
    edges = result.get("data", {}).get("categories", {}).get("edges", [])
    
    assert edges, "无法获取分类列表"
    print(f"   ✓ 获取到 {len(edges)} 个分类")
    
    print(f"\n   分类列表:")
    for i, edge in enumerate(edges[:5], 1):
        node = edge["node"]
        print(f"   {i}. {node.get('name', 'N/A')}")
    
    print("\n   ✅ 分类查询验证通过")


@pytest.mark.api
@pytest.mark.slow
def test_api_endurance(api_client):
    """
    API 持续稳定性测试
    """
    print("\n[API 测试] API 持续稳定性验证")
    
    query = """
    query {
        shop {
            name
        }
    }
    """
    
    iterations = 30
    times = []
    failures = 0
    
    print(f"\n[Step 1] 连续发送 {iterations} 次请求...")
    
    for i in range(iterations):
        start = time.time()
        result = api_client.post_graphql(query)
        elapsed = time.time() - start
        
        times.append(elapsed)
        
        if result.get("data", {}).get("shop"):
            if (i + 1) % 10 == 0:
                print(f"   已完成 {i+1}/{iterations} 次...")
        else:
            failures += 1
    
    avg_time = sum(times) / len(times)
    
    print(f"\n   测试结果:")
    print(f"   - 总请求数: {iterations}")
    print(f"   - 失败次数: {failures}")
    print(f"   - 平均响应: {avg_time:.3f}s")
    print(f"   - 最快响应: {min(times):.3f}s")
    print(f"   - 最慢响应: {max(times):.3f}s")
    
    assert failures == 0, f"有 {failures} 次请求失败"
    print("\n   ✅ API 持续稳定性验证通过")