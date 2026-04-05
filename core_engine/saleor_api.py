# 修改：使用绝对路径导入
from core_engine.base_api import BaseAPI
from core_engine.utils import load_config, get_logger

logger = get_logger("SaleorAPI")

class SaleorAPI(BaseAPI):
    def __init__(self):
        self.config = load_config()
        super().__init__(base_url=self.config.get('base_url', "http://localhost:8000/graphql/"))
        self.token = None

    def get_auth_token(self):
        mutation = """
        mutation TokenCreate($email: String!, $password: String!) {
          tokenCreate(email: $email, password: $password) {
            token
            errors { field message }
          }
        }
        """
        variables = {
            "email": self.config['admin_user']['email'],
            "password": self.config['admin_user']['password']
        }
        res = self.post_graphql(mutation, variables)
        self.token = res.get('data', {}).get('tokenCreate', {}).get('token')
        return self.token

    def update_product_name(self, product_id, new_name):
        mutation = """
        mutation UpdateProduct($id: ID!, $input: ProductInput!) {
          productUpdate(id: $id, input: $input) {
            product { name }
            errors { field message }
          }
        }
        """
        variables = {"id": product_id, "input": {"name": new_name}}
        # 增加 Token 过期自动重试逻辑
        res = self.post_graphql(mutation, variables, token=self.token)
        if "errors" in res and any("Signature has expired" in e.get("message", "") for e in res["errors"]):
            logger.warning("Token 过期，正在自动重连...")
            self.get_auth_token()
            res = self.post_graphql(mutation, variables, token=self.token)
        return res

    def get_product_id_by_name(self, product_name):
        query = """
        query GetProduct($search: String) {
          products(first: 5, filter: {search: $search}, channel: "default-channel") {
            edges {
              node { id name }
            }
          }
        }
        """
        res = self.post_graphql(query, {"search": product_name})
        edges = res.get('data', {}).get('products', {}).get('edges', [])
        for edge in edges:
            if edge['node']['name'] == product_name:
                return edge['node']['id']
        return edges[0]['node']['id'] if edges else None

    def get_product_name_by_id(self, product_id):
        """
        根据 ID 获取商品名称 (已修复多渠道错误)
        """
        query = """
        query GetProduct($id: ID!, $channel: String) {
          product(id: $id, channel: $channel) { 
            name 
          }
        }
        """
        # 从配置中读取 channel，默认为 "default-channel"
        channel_slug = self.config.get('channel', "default-channel")
        
        res = self.post_graphql(query, {"id": product_id, "channel": channel_slug})
        
        # 安全获取数据
        data = res.get('data')
        if data and data.get('product'):
            return data['product'].get('name')
        
        logger.error(f"无法获取商品名称，API返回: {res}")
        return None