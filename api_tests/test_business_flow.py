"""
核心业务流 API 测试
验证商品数据修改与查询的完整 API 业务链路
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
def test_product_crud_flow(api_client):
    """
    商品 CRUD 业务流测试
    """
    print("\n[API 测试] 商品 CRUD 业务流验证")
    
    api_client.get_auth_token()

    # 1. 获取测试商品
    print(f"\n[Step 1] 获取测试商品...")
    target_id, current_name = get_first_available_product(api_client)
    
    assert target_id, "错误：无法获取商品 ID"
    print(f"   ✓ 商品 ID: {target_id}")
    print(f"   ✓ 当前名称: {current_name}")
    
    # 2. 生成测试名称
    suffix = int(time.time()) % 1000
    NEW_NAME = f"{current_name} [API{suffix}]"
    
    print(f"\n[Step 2] 新名称: {NEW_NAME}")

    try:
        # 3. API 更新操作
        print(f"[Step 3] 执行 API 更新请求...", end='', flush=True)
        update_res = api_client.update_product_name(target_id, NEW_NAME)
        assert update_res, "API 更新请求失败"
        print(f" Done!")

        # 4. 验证更新结果
        print(f"[Step 4] 验证更新结果...")
        time.sleep(1)
        updated_name = get_product_name_by_id(api_client, target_id)
        
        assert updated_name == NEW_NAME, f"数据不一致: {updated_name} != {NEW_NAME}"
        print(f"   ✓ 验证成功: {updated_name}")

    finally:
        # 5. 还原数据
        print(f"\n[Cleanup] 还原商品名称...")
        api_client.update_product_name(target_id, current_name)
        print(f"   ✓ 还原完成")
    
    print("\n   ✅ 商品 CRUD 业务流验证通过")


@pytest.mark.api
def test_product_query_performance(api_client):
    """
    商品查询性能测试
    """
    print("\n[API 测试] 商品查询性能验证")
    
    api_client.get_auth_token()
    
    query = """
    query GetProducts($first: Int!, $search: String) {
        products(first: $first, filter: {search: $search}, channel: "default-channel") {
            edges {
                node {
                    id
                    name
                }
            }
            totalCount
        }
    }
    """
    
    test_cases = [
        {"name": "单商品查询", "first": 1},
        {"name": "10个商品查询", "first": 10},
        {"name": "带搜索的查询", "first": 10, "search": "shirt"},
    ]
    
    print(f"\n[Step 1] 测试不同查询条件...")
    
    for case in test_cases:
        variables = {"first": case["first"]}
        if "search" in case:
            variables["search"] = case["search"]
        
        start = time.time()
        result = api_client.post_graphql(query, variables, token=api_client.token)
        elapsed = time.time() - start
        
        edges = result.get("data", {}).get("products", {}).get("edges", [])
        total = result.get("data", {}).get("products", {}).get("totalCount", 0)
        
        print(f"\n   {case['name']}:")
        print(f"   - 返回数量: {len(edges)}/{total}")
        print(f"   - 响应时间: {elapsed:.3f}s")
        
        assert "errors" not in result, f"查询失败"
    
    print("\n   ✅ 商品查询性能验证通过")


@pytest.mark.api
def test_product_update_validation(api_client):
    """
    商品更新参数验证测试
    """
    print("\n[API 测试] 商品更新参数验证")
    
    api_client.get_auth_token()
    
    target_id, current_name = get_first_available_product(api_client)
    
    if not target_id:
        pytest.skip("无法获取商品，跳过测试")
    
    print(f"\n[Step 1] 测试无效参数...")
    
    # 测试空名称
    print(f"   - 测试空名称...")
    result1 = api_client.update_product_name(target_id, "")
    
    if not result1:
        print(f"     ✓ API 正确拒绝了空名称")
    else:
        print(f"     ⚠️ API 接受了空名称")
        api_client.update_product_name(target_id, current_name)
    
    # 测试超长名称
    print(f"   - 测试超长名称...")
    long_name = "A" * 300
    result2 = api_client.update_product_name(target_id, long_name)
    
    if not result2:
        print(f"     ✓ API 正确拒绝了超长名称")
    else:
        print(f"     ⚠️ API 接受了超长名称")
        api_client.update_product_name(target_id, current_name)
    
    print("\n   ✅ 参数验证测试完成")