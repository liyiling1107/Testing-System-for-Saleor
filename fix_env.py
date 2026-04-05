from core_engine.saleor_api import SaleorAPI

def force_reset_to_white_plimsolls():
    api = SaleorAPI()
    print("正在连接 API 并获取授权...")
    api.get_auth_token()
    
    # 1. 尝试通过模糊搜索找到那个被改掉的商品
    print("正在搜索名称包含 'Auto Shoes' 的残留商品...")
    bad_product_id = api.get_product_id_by_name("Auto Shoes")
    
    if not bad_product_id:
        # 如果搜不到 Auto Shoes，尝试直接用你已知的 ID (UHJvZHVjdDoxMjc=)
        bad_product_id = "UHJvZHVjdDoxMjc="
        print(f"未搜到关键词，尝试使用默认 ID: {bad_product_id}")

    # 2. 执行还原操作
    target_name = "White Plimsolls"
    print(f"正在将 ID 为 {bad_product_id} 的商品名重置为: {target_name}")
    
    res = api.update_product_name(bad_product_id, target_name)
    
    errors = res.get('data', {}).get('productUpdate', {}).get('errors', [])
    if not errors:
        print(f"✅ 成功！数据库已改回: {target_name}")
    else:
        print(f"❌ 还原失败: {errors}")

if __name__ == "__main__":
    force_reset_to_white_plimsolls()