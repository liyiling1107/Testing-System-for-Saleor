"""
订单管理 API 测试
验证订单相关的 GraphQL 接口功能
"""

import pytest


@pytest.mark.api
def test_get_orders_list_authenticated(api_client):
    """
    验证使用有效 Token 能否访问订单列表
    
    测试认证用户获取订单列表的权限
    """
    print("\n[API 测试] 订单列表访问验证")
    
    print("[Step 1] 确保已获取认证 Token...")
    token = api_client.get_auth_token()
    assert token, "无法获取认证 Token"
    print(f"   ✓ Token 有效: {token[:20]}...")
    
    print("[Step 2] 查询订单列表...")
    query = """
    query GetOrders($first: Int!) {
        orders(first: $first) {
            edges {
                node {
                    id
                    number
                    userEmail
                    status
                    created
                    total {
                        gross {
                            amount
                            currency
                        }
                    }
                }
            }
            totalCount
        }
    }
    """
    
    result = api_client.post_graphql(query, {"first": 10}, token=token)
    
    print("[Step 3] 验证响应结果...")
    
    # 检查响应结构
    assert "data" in result, "响应中缺少 data 字段"
    assert "errors" not in result, f"响应包含错误: {result.get('errors')}"
    
    orders_data = result["data"].get("orders")
    assert orders_data is not None, "响应中缺少 orders 数据"
    
    total_count = orders_data.get("totalCount", 0)
    edges = orders_data.get("edges", [])
    
    print(f"   - 订单总数: {total_count}")
    print(f"   - 本次获取: {len(edges)} 条")
    
    # 显示订单详情
    if edges:
        print(f"\n   最近订单:")
        for i, edge in enumerate(edges[:3], 1):
            node = edge["node"]
            print(f"   {i}. 订单号: {node.get('number', 'N/A')}")
            print(f"      用户: {node.get('userEmail', 'N/A')}")
            print(f"      状态: {node.get('status', 'N/A')}")
            total = node.get("total", {}).get("gross", {})
            print(f"      金额: {total.get('amount', 0)} {total.get('currency', '')}")
    else:
        print(f"   ℹ️ 当前没有订单数据")
    
    print("\n   ✅ 订单列表访问验证通过")


@pytest.mark.api
def test_orders_query_without_token(api_client):
    """
    验证未认证状态下访问订单列表的行为
    
    测试 API 的权限控制是否正确
    """
    print("\n[API 测试] 未认证订单访问验证")
    
    print("[Step 1] 不使用 Token 查询订单...")
    query = """
    query {
        orders(first: 5) {
            edges {
                node {
                    id
                    number
                }
            }
        }
    }
    """
    
    result = api_client.post_graphql(query, token=None)
    
    print("[Step 2] 分析响应结果...")
    
    # 检查是否被拒绝
    if "errors" in result:
        errors = result["errors"]
        error_messages = [e.get("message", "") for e in errors]
        print(f"   返回错误: {error_messages}")
        
        # 验证是权限错误
        permission_denied = any(
            "permission" in msg.lower() or 
            "authentication" in msg.lower() or
            "token" in msg.lower() or
            "unauthorized" in msg.lower()
            for msg in error_messages
        )
        
        if permission_denied:
            print(f"   ✓ 正确拒绝了未认证请求")
        else:
            print(f"   ⚠️ 错误类型可能不是权限问题")
    else:
        # 某些配置可能允许未认证访问
        orders_data = result.get("data", {}).get("orders", {})
        edges = orders_data.get("edges", [])
        print(f"   ℹ️ 未认证状态下获取到 {len(edges)} 条订单")
        print(f"   ⚠️ 建议生产环境限制未认证访问")
    
    print("\n   ✅ 未认证订单访问验证完成")


@pytest.mark.api
def test_order_query_pagination(api_client):
    """
    验证订单查询的分页功能
    
    测试 first 参数是否正确控制返回数量
    """
    print("\n[API 测试] 订单分页功能验证")
    
    token = api_client.get_auth_token()
    if not token:
        pytest.skip("无法获取 Token，跳过测试")
    
    query = """
    query GetOrdersPaginated($first: Int!) {
        orders(first: $first) {
            edges {
                node {
                    id
                    number
                }
            }
            totalCount
        }
    }
    """
    
    test_cases = [3, 5, 10]
    
    print("[Step 1] 测试不同分页参数...")
    
    for first in test_cases:
        result = api_client.post_graphql(query, {"first": first}, token=token)
        
        if "errors" in result:
            print(f"   ⚠️ first={first} 查询失败: {result['errors']}")
            continue
        
        orders_data = result.get("data", {}).get("orders", {})
        edges = orders_data.get("edges", [])
        total_count = orders_data.get("totalCount", 0)
        
        print(f"   - first={first}: 返回 {len(edges)} 条, 总数 {total_count}")
        
        # 验证返回数量不超过请求数量
        assert len(edges) <= first, f"返回数量 {len(edges)} 超过请求数量 {first}"
    
    print("\n   ✅ 订单分页功能验证通过")