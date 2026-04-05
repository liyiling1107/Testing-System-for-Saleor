#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查看 Saleor 中的所有商品
用于调试测试数据配置
"""

import json
import requests
import yaml
import os
from core_engine.saleor_api import SaleorAPI

# 配置文件路径
CONFIG_PATHS = [
    "data/test_data.yaml",
    "configs/test_data.yaml", 
    "test_data.yaml"
]

def get_test_data_path():
    """获取存在的测试数据配置文件路径"""
    for path in CONFIG_PATHS:
        if os.path.exists(path):
            return path
    return CONFIG_PATHS[0]  # 默认返回第一个

def get_all_products(api_client, first=50):
    """获取所有商品列表"""
    query = """
    query GetProducts($first: Int!) {
        products(first: $first, channel: "default-channel") {
            edges {
                node {
                    id
                    name
                    slug
                    channelListings {
                        channel {
                            name
                        }
                        visibleInListings
                    }
                }
            }
            totalCount
        }
    }
    """
    
    variables = {"first": first}
    
    try:
        result = api_client.post_graphql(query, variables=variables, token=api_client.token)
        
        if "data" in result and result["data"]:
            products_data = result["data"]["products"]
            total_count = products_data.get("totalCount", 0)
            edges = products_data.get("edges", [])
            
            print(f"\n{'='*60}")
            print(f"📦 商品总数: {total_count}")
            print(f"📋 当前显示: {len(edges)} 个商品")
            print(f"{'='*60}\n")
            
            products = []
            for idx, edge in enumerate(edges, 1):
                node = edge["node"]
                product_info = {
                    "index": idx,
                    "id": node["id"],
                    "name": node["name"],
                    "slug": node["slug"],
                    "visible": node["channelListings"][0]["visibleInListings"] if node["channelListings"] else False
                }
                products.append(product_info)
                
                # 打印商品信息
                print(f"{idx:3d}. {product_info['name']}")
                print(f"     ID: {product_info['id']}")
                print(f"     Slug: {product_info['slug']}")
                print(f"     可见: {'✓' if product_info['visible'] else '✗'}")
                print()
            
            return products
        else:
            print("❌ 获取商品失败")
            print(f"响应: {result}")
            return []
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return []

def search_product_by_name(api_client, search_name):
    """根据名称搜索商品"""
    query = """
    query SearchProducts($search: String!) {
        products(first: 10, filter: {search: $search}) {
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
    
    variables = {"search": search_name}
    
    try:
        result = api_client.post_graphql(query, variables=variables, token=api_client.token)
        
        if "data" in result and result["data"]:
            edges = result["data"]["products"]["edges"]
            
            if edges:
                print(f"\n🔍 找到 '{search_name}' 相关商品:")
                for edge in edges:
                    node = edge["node"]
                    print(f"  - {node['name']} (ID: {node['id']})")
                return edges
            else:
                print(f"\n❌ 未找到包含 '{search_name}' 的商品")
                return []
        else:
            print(f"❌ 搜索失败: {result}")
            return []
            
    except Exception as e:
        print(f"❌ 搜索异常: {e}")
        return []

def check_test_data_matches(api_client, test_data_file=None):
    """检查测试数据配置是否与数据库匹配"""
    if test_data_file is None:
        test_data_file = get_test_data_path()
    
    if not os.path.exists(test_data_file):
        print(f"❌ 找不到配置文件: {test_data_file}")
        return False
    
    try:
        with open(test_data_file, 'r', encoding='utf-8') as f:
            test_data = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")
        return False
    
    print(f"\n{'='*60}")
    print(f"🔍 验证测试数据配置: {test_data_file}")
    print(f"{'='*60}\n")
    
    valid_count = 0
    invalid_count = 0
    
    # 检查 product_updates
    if "product_updates" in test_data:
        print("📝 检查商品更新配置:")
        for idx, item in enumerate(test_data["product_updates"], 1):
            product_id = item.get("id")
            original_name = item.get("original_name")
            
            print(f"\n  {idx}. 商品: {original_name}")
            print(f"     ID: {product_id}")
            
            # 通过 ID 获取商品
            query = """
            query GetProduct($id: ID!) {
                product(id: $id) {
                    id
                    name
                }
            }
            """
            
            try:
                result = api_client.post_graphql(query, {"id": product_id}, token=api_client.token)
                if "data" in result and result["data"] and result["data"]["product"]:
                    product = result["data"]["product"]
                    print(f"     ✅ 数据库中存在: {product['name']}")
                    valid_count += 1
                    if product['name'] != original_name:
                        print(f"     ⚠️  名称不匹配: 配置='{original_name}', 实际='{product['name']}'")
                else:
                    print(f"     ❌ 数据库中不存在此商品")
                    invalid_count += 1
            except Exception as e:
                print(f"     ❌ 查询失败: {e}")
                invalid_count += 1
        
        print(f"\n📊 统计: ✅ {valid_count} 个有效, ❌ {invalid_count} 个无效")
    
    # 检查 products.sync_flow
    if "products" in test_data and "sync_flow" in test_data["products"]:
        sync_config = test_data["products"]["sync_flow"]
        print("\n📝 检查同步流程配置 (products.sync_flow):")
        print(f"   default_name: {sync_config.get('default_name')}")
        print(f"   target_name: {sync_config.get('target_name')}")
        print(f"   check_interval: {sync_config.get('check_interval')}")
        print(f"   max_wait: {sync_config.get('max_wait')}")
        
        # 验证商品是否存在
        default_name = sync_config.get('default_name')
        if default_name:
            print(f"\n   验证商品 '{default_name}'...")
            # 通过 API 查找商品
            target_id = None
            for product in get_all_products(api_client, first=100):
                if product["name"] == default_name:
                    target_id = product["id"]
                    break
            
            if target_id:
                print(f"   ✅ 商品存在: {default_name} (ID: {target_id})")
            else:
                print(f"   ❌ 商品不存在: {default_name}")
    
    return valid_count > 0

def update_test_data_config(api_client, test_data_file=None, max_products=5):
    """自动更新 test_data.yaml 配置文件（包含 products.sync_flow 结构）"""
    if test_data_file is None:
        test_data_file = get_test_data_path()
    
    # 获取前 max_products 个可见商品
    print(f"\n📝 正在获取商品列表...")
    products = get_all_products(api_client, first=max_products)
    
    if not products:
        print("❌ 无法获取商品列表")
        return False
    
    # 只使用可见的商品
    visible_products = [p for p in products if p["visible"]]
    
    if not visible_products:
        print("❌ 没有可见的商品")
        return False
    
    # 选择第一个商品作为 sync_flow 的测试商品
    test_product = visible_products[0]
    
    # 构建新的配置（完整格式）
    new_config = {
        "products": {
            "sync_flow": {
                "default_name": test_product["name"],
                "target_name": f"{test_product['name']} (Modified)",
                "check_interval": 2,
                "max_wait": 60
            }
        },
        "product_updates": [],
        "order_flow": {
            "variant_id": "UHJvZHVjdFZhcmlhbnQ6MzE3",
            "customer_email": "test@example.com"
        }
    }
    
    # 添加所有可见商品到 product_updates
    for product in visible_products:
        new_config["product_updates"].append({
            "id": product["id"],
            "original_name": product["name"],
            "new_name": f"{product['name']} (Modified)",
            "channel": "default-channel"
        })
    
    # 备份原文件
    if os.path.exists(test_data_file):
        backup_file = f"{test_data_file}.backup"
        try:
            with open(test_data_file, 'r', encoding='utf-8') as f:
                old_content = f.read()
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(old_content)
            print(f"✅ 已备份原配置到: {backup_file}")
        except Exception as e:
            print(f"⚠️  备份失败: {e}")
    
    # 写入新配置
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(test_data_file), exist_ok=True)
        
        with open(test_data_file, 'w', encoding='utf-8') as f:
            yaml.dump(new_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        print(f"\n✅ 已成功更新配置文件: {test_data_file}")
        print(f"📝 更新了 {len(new_config['product_updates'])} 个商品配置")
        
        # 显示新配置内容
        print(f"\n{'='*60}")
        print("📄 新配置内容预览:")
        print(f"{'='*60}")
        
        print("\n# 同步流程配置 (供测试使用)")
        print(f"products:")
        print(f"  sync_flow:")
        print(f"    default_name: \"{new_config['products']['sync_flow']['default_name']}\"")
        print(f"    target_name: \"{new_config['products']['sync_flow']['target_name']}\"")
        print(f"    check_interval: {new_config['products']['sync_flow']['check_interval']}")
        print(f"    max_wait: {new_config['products']['sync_flow']['max_wait']}")
        
        print("\n# 商品更新配置 (供 API 使用)")
        for item in new_config["product_updates"]:
            print(f"\n  - id: \"{item['id']}\"")
            print(f"    original_name: \"{item['original_name']}\"")
            print(f"    new_name: \"{item['new_name']}\"")
            print(f"    channel: \"{item['channel']}\"")
        
        return True
        
    except Exception as e:
        print(f"❌ 写入配置文件失败: {e}")
        return False

def add_custom_sync_product(api_client, test_data_file=None):
    """手动添加指定的商品到 sync_flow 配置"""
    if test_data_file is None:
        test_data_file = get_test_data_path()
    
    print("\n📝 手动选择要测试的商品:")
    products = get_all_products(api_client, first=50)
    
    if not products:
        print("❌ 无法获取商品列表")
        return False
    
    visible_products = [p for p in products if p["visible"]]
    
    print("\n可见商品列表:")
    for p in visible_products:
        print(f"  {p['index']:3d}. {p['name']}")
    
    try:
        choice = input("\n请输入要测试的商品编号: ").strip()
        selected_index = int(choice)
        selected_product = next((p for p in visible_products if p["index"] == selected_index), None)
        
        if not selected_product:
            print("❌ 无效的商品编号")
            return False
        
        target_name = input(f"请输入修改后的名称 (直接回车使用 '{selected_product['name']} (Modified)'): ").strip()
        if not target_name:
            target_name = f"{selected_product['name']} (Modified)"
        
        # 读取现有配置
        if os.path.exists(test_data_file):
            with open(test_data_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}
        
        # 确保必要的结构存在
        if "products" not in config:
            config["products"] = {}
        
        config["products"]["sync_flow"] = {
            "default_name": selected_product["name"],
            "target_name": target_name,
            "check_interval": 2,
            "max_wait": 60
        }
        
        if "product_updates" not in config:
            config["product_updates"] = []
        
        # 检查是否已存在该商品
        exists = any(item["id"] == selected_product["id"] for item in config["product_updates"])
        if not exists:
            config["product_updates"].append({
                "id": selected_product["id"],
                "original_name": selected_product["name"],
                "new_name": target_name,
                "channel": "default-channel"
            })
            print(f"✅ 已添加商品到 product_updates")
        
        if "order_flow" not in config:
            config["order_flow"] = {
                "variant_id": "UHJvZHVjdFZhcmlhbnQ6MzE3",
                "customer_email": "test@example.com"
            }
        
        # 保存配置
        with open(test_data_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        print(f"\n✅ 已更新配置文件: {test_data_file}")
        print(f"\n📄 当前 sync_flow 配置:")
        print(f"   default_name: {selected_product['name']}")
        print(f"   target_name: {target_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        return False

def main():
    """主函数"""
    print("\n" + "="*60)
    print("🔧 Saleor 商品查询与配置工具")
    print("="*60)
    
    # 初始化 API 客户端
    api_client = SaleorAPI()
    
    # 获取 Token
    print("\n🔑 正在获取认证 Token...")
    token = api_client.get_auth_token()
    if not token:
        print("❌ 获取 Token 失败，请检查配置")
        return
    
    print("✅ Token 获取成功\n")
    
    config_file = get_test_data_path()
    print(f"📁 测试数据配置文件: {config_file}")
    
    # 菜单
    while True:
        print("\n" + "-"*40)
        print("请选择操作:")
        print("1. 查看所有商品")
        print("2. 搜索商品 (按名称)")
        print("3. 验证测试数据配置")
        print("4. 自动生成完整配置 (使用前5个商品)")
        print("5. 手动选择测试商品 (设置 sync_flow)")
        print("0. 退出")
        print("-"*40)
        
        choice = input("\n请输入选项 (0-5): ").strip()
        
        if choice == "1":
            get_all_products(api_client)
            
        elif choice == "2":
            search_name = input("请输入商品名称 (支持部分匹配): ").strip()
            if search_name:
                search_product_by_name(api_client, search_name)
                
        elif choice == "3":
            check_test_data_matches(api_client)
            
        elif choice == "4":
            print("\n⚠️  这将自动生成完整配置，包含 products.sync_flow")
            confirm = input("确认继续? (y/n): ").strip().lower()
            if confirm == 'y':
                update_test_data_config(api_client)
            else:
                print("已取消")
                
        elif choice == "5":
            add_custom_sync_product(api_client)
                
        elif choice == "0":
            print("👋 再见!")
            break
        else:
            print("❌ 无效选项，请重新输入")

if __name__ == "__main__":
    main()