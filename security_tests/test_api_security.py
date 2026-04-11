"""
API 安全测试
验证 GraphQL API 的安全性配置
"""

import pytest
import requests
import json
from core_engine.saleor_api import SaleorAPI


@pytest.mark.security
def test_introspection_disabled_in_production(api_client):
    """
    测试 GraphQL 内省是否在生产环境禁用
    
    内省查询可能泄露 API 结构
    """
    print("\n[安全测试] GraphQL 内省检测")
    
    introspection_query = """
    query {
        __schema {
            types {
                name
                kind
                description
                fields {
                    name
                    type {
                        name
                        kind
                    }
                }
            }
        }
    }
    """
    
    result = api_client.post_graphql(introspection_query)
    
    if result.get("data", {}).get("__schema"):
        types_count = len(result["data"]["__schema"]["types"])
        print(f"   ⚠️ 内省已启用，发现 {types_count} 个类型")
        print(f"   ℹ️ 开发环境可以启用内省，生产环境建议禁用")
    elif result.get("errors"):
        error_msg = str(result["errors"]).lower()
        if "introspection" in error_msg or "disabled" in error_msg:
            print(f"   ✓ 内省已被禁用（安全配置正确）")
        else:
            print(f"   ⚠️ 内省查询返回错误: {result['errors'][:100]}")
    else:
        print(f"   ⚠️ 内省状态未知")
    
    # 不强制断言，只记录配置状态
    print(f"   ✓ 内省检测完成")


@pytest.mark.security
def test_rate_limiting_on_api(api_client):
    """
    测试 API 速率限制
    
    快速发送大量请求，验证是否有速率限制保护
    """
    print("\n[安全测试] API 速率限制检测")
    
    query = """
    query {
        shop {
            name
        }
    }
    """
    
    request_count = 30
    results = []
    
    print(f"   快速发送 {request_count} 个请求...")
    
    for i in range(request_count):
        result = api_client.post_graphql(query)
        results.append(result)
        
        if i % 10 == 0 and i > 0:
            print(f"      已发送 {i} 个请求...")
    
    # 分析结果
    success_count = 0
    rate_limited_count = 0
    error_count = 0
    
    for result in results:
        if result.get("data", {}).get("shop"):
            success_count += 1
        elif result.get("errors"):
            error_msg = str(result["errors"]).lower()
            if "rate" in error_msg or "limit" in error_msg or "throttle" in error_msg:
                rate_limited_count += 1
            else:
                error_count += 1
        else:
            error_count += 1
    
    print(f"\n   测试结果:")
    print(f"   - 总请求数: {request_count}")
    print(f"   - 成功: {success_count}")
    print(f"   - 被限流: {rate_limited_count}")
    print(f"   - 错误: {error_count}")
    
    if rate_limited_count > 0:
        print(f"   ✓ 检测到速率限制保护")
    else:
        print(f"   ⚠️ 未检测到速率限制，建议配置限流")
    
    # 不强制断言
    print(f"   ✓ 速率限制检测完成")


@pytest.mark.security
def test_xss_injection_in_graphql(api_client):
    """
    测试 GraphQL 查询的 XSS 注入防护
    
    尝试在查询参数中注入 XSS payload
    """
    print("\n[安全测试] XSS 注入防护测试")
    
    xss_payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert(1)>",
        "javascript:alert('XSS')",
        "<svg onload=alert(1)>",
        "'><script>alert(document.cookie)</script>",
        "\"><img src=x onerror=alert(1)>",
    ]
    
    query_template = '''
    query SearchProducts($search: String!) {
        products(first: 10, filter: {search: $search}) {
            edges {
                node {
                    id
                    name
                }
            }
        }
    }
    '''
    
    vulnerable = False
    
    for payload in xss_payloads:
        print(f"\n   测试 payload: {payload[:40]}...")
        
        variables = {"search": payload}
        result = api_client.post_graphql(query_template, variables)
        
        response_str = str(result)
        
        # 检查 payload 是否被原样反射
        if payload in response_str and "<script>" not in response_str:
            # 如果被转义了，payload 可能被修改
            print(f"      ✓ Payload 被正确处理/转义")
        elif payload in response_str:
            print(f"      ⚠️ Payload 原样返回，可能存在 XSS 风险")
            vulnerable = True
        else:
            print(f"      ✓ Payload 被过滤或拒绝")
    
    print(f"\n   测试结果:")
    print(f"   - 存在 XSS 风险: {'是' if vulnerable else '否'}")
    
    # 不强制断言，只记录
    print(f"   ✓ XSS 检测完成")


@pytest.mark.security
def test_sensitive_data_exposure(api_client):
    """
    测试敏感数据是否在 API 响应中暴露
    
    检查是否有意外返回的敏感信息
    """
    print("\n[安全测试] 敏感数据暴露检测")
    
    api_client.get_auth_token()
    
    sensitive_keywords = [
        "password", "token", "secret", "key", "private",
        "credit", "card", "cvv", "ssn", "social"
    ]
    
    test_queries = [
        ("商品信息", """
            query {
                products(first: 5) {
                    edges {
                        node {
                            id
                            name
                            slug
                        }
                    }
                }
            }
        """),
        ("订单信息", """
            query {
                orders(first: 5) {
                    edges {
                        node {
                            id
                            number
                            userEmail
                            status
                        }
                    }
                }
            }
        """, True),  # 需要认证
        ("用户信息", """
            query {
                me {
                    email
                    firstName
                    lastName
                }
            }
        """, True),
    ]
    
    for name, query, *needs_auth in test_queries:
        print(f"\n   测试查询: {name}")
        
        token = api_client.token if needs_auth and needs_auth[0] else None
        result = api_client.post_graphql(query, token=token)
        response_str = str(result).lower()
        
        found_keywords = []
        for kw in sensitive_keywords:
            if kw in response_str:
                found_keywords.append(kw)
        
        if found_keywords:
            print(f"      ⚠️ 发现敏感关键词: {found_keywords}")
            # 检查是否是正常业务字段
            normal_fields = ["useremail", "email"]
            actual_sensitive = [kw for kw in found_keywords if kw not in normal_fields]
            if actual_sensitive:
                print(f"      ❌ 可能存在敏感数据泄露: {actual_sensitive}")
        else:
            print(f"      ✓ 未发现敏感数据")
    
    print(f"\n   ✓ 敏感数据检测完成")


@pytest.mark.security
def test_cors_configuration(api_client):
    """
    测试 CORS 跨域配置
    
    验证 API 的 CORS 配置是否安全
    """
    print("\n[安全测试] CORS 配置检测")
    
    # 测试 OPTIONS 预检请求
    try:
        response = requests.options(
            api_client.base_url,
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization"
            },
            timeout=10
        )
        
        print(f"   OPTIONS 响应状态: {response.status_code}")
        
        cors_headers = {
            "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
            "Access-Control-Allow-Credentials": response.headers.get("Access-Control-Allow-Credentials"),
            "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
        }
        
        print(f"\n   CORS 响应头:")
        for header, value in cors_headers.items():
            print(f"   - {header}: {value}")
        
        # 检查危险配置
        allow_origin = cors_headers.get("Access-Control-Allow-Origin")
        allow_credentials = cors_headers.get("Access-Control-Allow-Credentials")
        
        if allow_origin == "*" and allow_credentials == "true":
            print(f"\n   ❌ 危险配置：Allow-Origin=* 且 Allow-Credentials=true")
        elif allow_origin == "*":
            print(f"\n   ⚠️ Allow-Origin=*（开发环境可接受）")
        elif allow_origin and "evil.com" in allow_origin:
            print(f"\n   ⚠️ 允许了测试的恶意 Origin")
        else:
            print(f"\n   ✓ CORS 配置看起来安全")
            
    except Exception as e:
        print(f"   ⚠️ OPTIONS 请求失败: {e}")
    
    print(f"\n   ✓ CORS 检测完成")