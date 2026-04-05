def test_get_orders_list(api_client):
    """验证使用自动获取的 Token 是否能访问受限资源（如订单列表）"""
    query = """
    query {
      orders(first: 5) {
        edges {
          node {
            id
            number
            userEmail
          }
        }
      }
    }
    """
    # 此时 api_client 已经自带了 token
    res = api_client.post_graphql(query, token=api_client.token)
    
    print(f"\n订单列表结果: {res}")
    assert "data" in res
    assert "errors" not in res