"""
Saleor GraphQL API 客户端
提供与Saleor电商平台交互的核心功能
"""

import requests
import json
from typing import Optional, Dict, Any, List
import logging
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SaleorAPI:
    """Saleor API 客户端类"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        初始化API客户端
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        base_url = self.config.get("baseUrl", "https://demo.saleor.io")
        # 移除末尾的斜杠并构建GraphQL端点
        base_url = base_url.rstrip('/')
        self.base_url = f"{base_url}/graphql/"
        self.token = None
        self.frontend_url = self.config.get("frontend_url", "http://localhost:3000")
        self.dashboard_url = self.config.get("dashboard_url", "http://localhost:9000")
        
        logger.info(f"API 客户端初始化，端点: {self.base_url}")
        logger.info(f"前端地址: {self.frontend_url}")
        logger.info(f"后台地址: {self.dashboard_url}")
    
    def _load_config(self, config_path: str) -> Dict:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                return {}
        logger.warning(f"配置文件不存在: {config_path}")
        return {}
    
    def post_graphql(self, query: str, variables: Dict = None, token: str = None) -> Dict:
        """
        发送GraphQL请求
        
        Args:
            query: GraphQL查询字符串
            variables: 查询变量
            token: 认证令牌
            
        Returns:
            API响应字典
        """
        headers = {
            "Content-Type": "application/json",
        }
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        try:
            logger.debug(f"发送GraphQL请求: {query[:100]}...")
            response = requests.post(
                self.base_url, 
                json=payload, 
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"HTTP 错误! 状态码: {response.status_code}, 内容: {response.text[:200]}")
                return {"data": None, "errors": [{"message": f"HTTP {response.status_code}: {response.text[:100]}"}]}
                
        except requests.exceptions.ConnectionError:
            error_msg = f"连接失败！请确认本地Saleor服务是否运行在: {self.base_url}"
            logger.error(error_msg)
            return {"data": None, "errors": [{"message": error_msg}]}
        except requests.exceptions.Timeout:
            error_msg = "请求超时，请检查网络连接"
            logger.error(error_msg)
            return {"data": None, "errors": [{"message": error_msg}]}
        except Exception as e:
            logger.error(f"请求异常: {e}")
            return {"data": None, "errors": [{"message": str(e)}]}
    
    def get_auth_token(self) -> Optional[str]:
        """
        获取认证Token
        
        Returns:
            认证令牌或None
        """
        admin_user = self.config.get("admin_user", {})
        email = admin_user.get("email", "admin@example.com")
        password = admin_user.get("password", "admin")
        
        logger.info(f"尝试获取 Token，用户: {email}")
        
        query = """
        mutation TokenCreate($email: String!, $password: String!) {
            tokenCreate(email: $email, password: $password) {
                token
                refreshToken
                errors {
                    field
                    message
                    code
                }
            }
        }
        """
        
        variables = {"email": email, "password": password}
        result = self.post_graphql(query, variables)
        
        if result.get("data") and result["data"].get("tokenCreate"):
            token_data = result["data"]["tokenCreate"]
            if token_data.get("token"):
                self.token = token_data["token"]
                logger.info(f"✓ Token 获取成功: {self.token[:20]}...")
                return self.token
            else:
                errors = token_data.get("errors", [])
                logger.error(f"Token 获取失败: {errors}")
                
                # 如果是认证失败，提示用户检查配置
                if errors and errors[0].get("code") == "INVALID_CREDENTIALS":
                    logger.error("用户名或密码错误，请检查 config.json 中的 admin_user 配置")
        elif result.get("errors"):
            logger.error(f"GraphQL 错误: {result['errors']}")
        
        logger.warning("将使用未认证模式继续测试")
        return None
    
    def get_product_id_by_name(self, name):
        """根据商品名称获取商品 ID"""
        try:
            # 方案1：直接通过名称搜索
            query = """
            query GetProductByName($name: String!) {
                products(first: 1, filter: {search: $name}) {
                    edges {
                        node {
                            id
                            name
                        }
                    }
                }
            }
            """
        
            variables = {"name": name}
            result = self.post_graphql(query, variables, token=self.token)
        
            if "data" in result and result["data"]["products"]["edges"]:
                product = result["data"]["products"]["edges"][0]["node"]
                if product["name"] == name:
                    return product["id"]
        
            # 方案2：如果精确匹配失败，获取所有商品并匹配（不区分大小写）
            query_all = """
            {
                products(first: 100, channel: "default-channel") {
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
        
            result_all = self.post_graphql(query_all, token=self.token)
        
            if "data" in result_all and result_all["data"]["products"]["edges"]:
                for edge in result_all["data"]["products"]["edges"]:
                    node = edge["node"]
                    # 精确匹配
                    if node["name"] == name:
                        return node["id"]
                    # 不区分大小写匹配
                    if node["name"].lower() == name.lower():
                        return node["id"]
        
            self.logger.warning(f"错误：找不到商品 '{name}'")
            return None
        
        except Exception as e:
            self.logger.error(f"获取商品 ID 失败: {e}")
            return None
    
    def get_product_name_by_id(self, product_id: str) -> Optional[str]:
        """
        根据商品ID获取商品名
        
        Args:
            product_id: 商品ID
            
        Returns:
            商品名称或None
        """
        query = """
        query GetProduct($id: ID!) {
            product(id: $id) {
                name
                id
            }
        }
        """
        
        result = self.post_graphql(query, {"id": product_id})
        
        if result.get("data") and result["data"].get("product"):
            product = result["data"]["product"]
            logger.info(f"找到商品: {product['name']}")
            return product["name"]
        
        logger.warning(f"未找到商品ID: {product_id}")
        return None
    
    def update_product_name(self, product_id: str, new_name: str) -> bool:
        """
        更新商品名称
        
        Args:
            product_id: 商品ID
            new_name: 新商品名称
            
        Returns:
            是否更新成功
        """
        if not self.token:
            logger.info("需要认证才能更新商品，尝试获取 Token...")
            self.get_auth_token()
            if not self.token:
                logger.error("认证失败，无法更新商品")
                return False
        
        query = """
        mutation ProductUpdate($id: ID!, $input: ProductInput!) {
            productUpdate(id: $id, input: $input) {
                product {
                    id
                    name
                    slug
                }
                errors {
                    field
                    message
                    code
                }
            }
        }
        """
        
        variables = {
            "id": product_id,
            "input": {"name": new_name}
        }
        
        result = self.post_graphql(query, variables, token=self.token)
        
        if result.get("data") and result["data"].get("productUpdate"):
            errors = result["data"]["productUpdate"].get("errors", [])
            if not errors:
                logger.info(f"✓ 商品名称更新成功: {new_name}")
                return True
            else:
                logger.error(f"更新失败: {errors}")
                return False
        elif result.get("errors"):
            logger.error(f"GraphQL 错误: {result['errors']}")
            return False
        
        return False
    
    def get_orders(self, first: int = 10) -> List[Dict]:
        """
        获取订单列表
        
        Args:
            first: 获取订单数量
            
        Returns:
            订单列表
        """
        if not self.token:
            logger.info("需要认证才能获取订单，尝试获取 Token...")
            self.get_auth_token()
            if not self.token:
                logger.warning("未认证，无法获取订单列表")
                return []
        
        query = """
        query GetOrders($first: Int!) {
            orders(first: $first) {
                edges {
                    node {
                        id
                        number
                        userEmail
                        created
                        status
                        total {
                            gross {
                                amount
                                currency
                            }
                        }
                        lines {
                            productName
                            quantity
                        }
                    }
                }
                totalCount
            }
        }
        """
        
        result = self.post_graphql(query, {"first": first}, token=self.token)
        
        if result.get("data") and result["data"].get("orders"):
            orders = []
            for edge in result["data"]["orders"]["edges"]:
                orders.append(edge["node"])
            logger.info(f"获取到 {len(orders)} 个订单")
            return orders
        elif result.get("errors"):
            logger.error(f"获取订单失败: {result['errors']}")
        
        return []
    
    def get_products(self, first: int = 20, search: str = None) -> List[Dict]:
        """
        获取商品列表
        
        Args:
            first: 获取商品数量
            search: 搜索关键词
            
        Returns:
            商品列表
        """
        query = """
        query GetProducts($first: Int!, $search: String) {
            products(first: $first, filter: {search: $search}) {
                edges {
                    node {
                        id
                        name
                        slug
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
                        thumbnail {
                            url
                        }
                    }
                }
                totalCount
            }
        }
        """
        
        variables = {"first": first}
        if search:
            variables["search"] = search
        
        result = self.post_graphql(query, variables)
        
        if result.get("data") and result["data"].get("products"):
            products = []
            for edge in result["data"]["products"]["edges"]:
                products.append(edge["node"])
            logger.info(f"获取到 {len(products)} 个商品")
            return products
        
        return []
    
    def get_categories(self, first: int = 20) -> List[Dict]:
        """
        获取分类列表
        
        Args:
            first: 获取分类数量
            
        Returns:
            分类列表
        """
        query = """
        query GetCategories($first: Int!) {
            categories(first: $first) {
                edges {
                    node {
                        id
                        name
                        slug
                        description
                    }
                }
            }
        }
        """
        
        result = self.post_graphql(query, {"first": first})
        
        if result.get("data") and result["data"].get("categories"):
            categories = []
            for edge in result["data"]["categories"]["edges"]:
                categories.append(edge["node"])
            logger.info(f"获取到 {len(categories)} 个分类")
            return categories
        
        return []
    
    def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            服务是否正常
        """
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
        
        result = self.post_graphql(query)
        
        if result.get("data") and result["data"].get("shop"):
            shop = result["data"]["shop"]
            logger.info(f"✓ Saleor 服务正常: {shop.get('name')}")
            return True
        
        if result.get("errors"):
            logger.error(f"健康检查失败: {result['errors']}")
        
        return False