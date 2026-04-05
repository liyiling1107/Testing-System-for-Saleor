import requests
from .utils import get_logger

# 初始化日志记录器
logger = get_logger("API_Client")

class BaseAPI:
    def __init__(self, base_url="http://localhost:8000/graphql/"):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}

    def post_graphql(self, query, variables=None, token=None):
        """
        统一的 GraphQL 请求方法，集成了日志记录功能
        """
        # 1. 准备请求头
        headers = self.headers.copy()
        if token:
            headers["Authorization"] = f"JWT {token}"
            
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        # 2. 记录请求日志 (截取前100个字符防止日志过大)
        clean_query = query.replace('\n', ' ').strip()
        logger.info(f"发送 GraphQL 请求: {clean_query[:100]}...")
        
        try:
            # 3. 执行请求
            response = requests.post(self.base_url, json=payload, headers=headers)
            
            # 4. 检查 HTTP 状态码
            if response.status_code != 200:
                error_msg = f"HTTP 错误! 状态码: {response.status_code}, 内容: {response.text}"
                logger.error(error_msg)
                print(f"\n[API Error] {error_msg}")
                return {"data": None, "errors": [{"message": f"HTTP {response.status_code}"}]}
            
            response_json = response.json()
            
            # 5. 检查 GraphQL 业务逻辑错误
            if "errors" in response_json:
                logger.error(f"GraphQL 业务逻辑报错: {response_json['errors']}")
            else:
                logger.info("API 请求执行成功 ✅")
                
            return response_json

        except Exception as e:
            exception_msg = f"发送请求时发生异常: {str(e)}"
            logger.exception(exception_msg) # exception 会自动记录堆栈信息
            print(f"\n[API Exception] {exception_msg}")
            return {"data": None, "errors": [{"message": str(e)}]}