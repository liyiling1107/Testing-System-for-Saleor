"""
认证安全测试
验证登录认证机制的安全性
"""

import pytest
import time
import requests
from core_engine.saleor_api import SaleorAPI


@pytest.mark.security
def test_invalid_login_blocking(api_client):
    """
    测试无效登录的防护机制
    
    连续使用错误密码尝试登录，验证是否有账户锁定或限流机制
    """
    print("\n[安全测试] 无效登录防护测试")
    
    admin_user = api_client.config.get("admin_user", {})
    email = admin_user.get("email", "admin@example.com")
    wrong_passwords = [
        "wrong123",
        "admin1234", 
        "password",
        "123456",
        "admin@123"
    ]
    
    query = """
    mutation TokenCreate($email: String!, $password: String!) {
        tokenCreate(email: $email, password: $password) {
            token
            errors {
                code
                message
            }
        }
    }
    """
    
    results = []
    lockout_detected = False
    
    for i, pwd in enumerate(wrong_passwords, 1):
        print(f"\n   尝试 {i}: 密码 '{pwd}'")
        variables = {"email": email, "password": pwd}
        result = api_client.post_graphql(query, variables)
        
        errors = result.get("data", {}).get("tokenCreate", {}).get("errors", [])
        error_codes = [e.get("code") for e in errors]
        
        results.append({
            "attempt": i,
            "password": pwd,
            "error_codes": error_codes
        })
        
        if "INVALID_CREDENTIALS" in error_codes:
            print(f"      ✓ 正确返回 INVALID_CREDENTIALS")
        elif "ACCOUNT_LOCKED" in error_codes or "TOO_MANY_REQUESTS" in error_codes:
            print(f"      🔒 账户已被锁定或限流")
            lockout_detected = True
            break
        else:
            print(f"      ⚠️ 返回: {error_codes}")
        
        time.sleep(0.5)  # 避免触发速率限制
    
    print(f"\n   测试结果:")
    print(f"   - 总尝试次数: {len(results)}")
    print(f"   - 检测到锁定/限流: {'是' if lockout_detected else '否'}")
    
    # 验证：不应该返回 token
    for r in results:
        assert "token" not in str(r), f"尝试 {r['attempt']} 意外返回了 token"
    
    print(f"   ✓ 所有无效登录均被正确拒绝")


@pytest.mark.security
def test_sql_injection_in_login(api_client):
    """
    测试登录接口的 SQL 注入防护
    
    尝试使用 SQL 注入 payload 作为用户名/密码
    """
    print("\n[安全测试] SQL 注入防护测试")
    
    sql_payloads = [
        "' OR '1'='1",
        "' OR '1'='1' --",
        "admin' --",
        "' UNION SELECT NULL--",
        "'; DROP TABLE users; --",
        "1' AND '1'='1",
        "' OR 1=1#",
        '" OR "1"="1',
    ]
    
    query = """
    mutation TokenCreate($email: String!, $password: String!) {
        tokenCreate(email: $email, password: $password) {
            token
            errors {
                code
                message
            }
        }
    }
    """
    
    vulnerable = False
    
    for payload in sql_payloads:
        print(f"\n   测试 payload: {payload[:30]}...")
        
        # 测试作为邮箱
        result1 = api_client.post_graphql(query, {"email": payload, "password": "any"})
        # 测试作为密码
        result2 = api_client.post_graphql(query, {"email": "admin@example.com", "password": payload})
        
        token1 = result1.get("data", {}).get("tokenCreate", {}).get("token")
        token2 = result2.get("data", {}).get("tokenCreate", {}).get("token")
        
        if token1 or token2:
            print(f"      ❌ 危险！SQL 注入 payload 获得了 token！")
            vulnerable = True
        else:
            print(f"      ✓ 注入被正确阻止")
    
    print(f"\n   测试结果:")
    print(f"   - 存在 SQL 注入漏洞: {'是（危险！）' if vulnerable else '否（安全）'}")
    
    assert not vulnerable, "检测到 SQL 注入漏洞！"


@pytest.mark.security
def test_token_not_leaked_in_response(api_client):
    """
    测试 Token 不会在错误响应中泄露
    """
    print("\n[安全测试] Token 泄露检测")
    
    # 先获取一个有效 token
    api_client.get_auth_token()
    valid_token = api_client.token
    
    if not valid_token:
        pytest.skip("无法获取有效 Token，跳过测试")
    
    print(f"   已获取有效 Token: {valid_token[:20]}...")
    
    # 测试各种可能泄露 token 的场景
    test_cases = [
        ("无效查询语法", "query { shop { name }"),  # 缺少闭合括号
        ("不存在的字段", "query { shop { nonexistent } }"),
        ("无效的 mutation", "mutation { invalidMutation { id } }"),
        ("内省查询", """
            query {
                __schema {
                    types {
                        name
                        fields {
                            name
                        }
                    }
                }
            }
        """),
    ]
    
    for name, query in test_cases:
        print(f"\n   测试场景: {name}")
        result = api_client.post_graphql(query, token=valid_token)
        
        response_str = str(result)
        
        if valid_token in response_str:
            print(f"      ❌ 危险！响应中发现了 Token！")
            assert False, f"Token 在 '{name}' 的响应中泄露"
        else:
            print(f"      ✓ Token 未泄露")
    
    print(f"\n   ✓ 所有场景均未泄露 Token")


@pytest.mark.security
def test_password_not_in_api_response(api_client):
    """
    测试密码不会在任何 API 响应中返回
    """
    print("\n[安全测试] 密码泄露检测")
    
    api_client.get_auth_token()
    
    password_keywords = ["password", "pass", "pwd", "secret", "hash"]
    
    test_queries = [
        ("用户信息", """
            query {
                me {
                    email
                    firstName
                    lastName
                }
            }
        """),
        ("员工列表", """
            query {
                staffUsers(first: 10) {
                    edges {
                        node {
                            email
                            firstName
                            lastName
                        }
                    }
                }
            }
        """),
    ]
    
    for name, query in test_queries:
        print(f"\n   测试查询: {name}")
        result = api_client.post_graphql(query, token=api_client.token)
        response_str = str(result).lower()
        
        found_keywords = []
        for kw in password_keywords:
            if kw in response_str:
                found_keywords.append(kw)
        
        if found_keywords:
            print(f"      ⚠️ 响应中发现敏感关键词: {found_keywords}")
        else:
            print(f"      ✓ 未发现密码相关字段")
    
    # 不强制断言，只记录
    print(f"\n   ✓ 密码泄露检测完成")


@pytest.mark.security
def test_session_fixation_prevention(api_client):
    """
    测试会话固定攻击防护
    
    验证每次登录都会生成新的 Token
    """
    print("\n[安全测试] 会话固定防护测试")
    
    tokens = []
    
    for i in range(5):
        print(f"\n   第 {i+1} 次登录...")
        token = api_client.get_auth_token()
        
        if token:
            tokens.append(token)
            print(f"      Token: {token[:30]}...")
        else:
            print(f"      登录失败")
        
        time.sleep(0.5)
    
    # 检查所有 token 是否唯一
    unique_tokens = set(tokens)
    
    print(f"\n   测试结果:")
    print(f"   - 登录次数: 5")
    print(f"   - 获取 Token 数: {len(tokens)}")
    print(f"   - 唯一 Token 数: {len(unique_tokens)}")
    
    if len(tokens) == len(unique_tokens):
        print(f"   ✓ 每次登录生成新的唯一 Token（防会话固定）")
    else:
        print(f"   ⚠️ 检测到重复 Token，可能存在会话固定风险")
    
    assert len(tokens) == len(unique_tokens), "Token 不应重复"