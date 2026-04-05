import yaml
import logging
import os
from datetime import datetime

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
    
def load_test_data():
    # 获取项目根目录路径
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    yaml_path = os.path.join(base_path, "configs", "test_data.yaml")
    
    with open(yaml_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
    
def get_logger(name="SaleorTest"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # 创建 logs 目录
        if not os.path.exists("logs"):
            os.makedirs("logs")
            
        # 按照日期生成日志名
        log_path = os.path.join("logs", f"test_{datetime.now().strftime('%Y%m%d')}.log")
        
        # 文件处理器
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        # 日志格式：时间 - 级别 - 消息
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
    return logger

def load_yaml(file_name):
    """读取 data 目录下的 yaml 文件"""
    base_path = os.path.dirname(os.path.dirname(__file__))
    file_path = os.path.join(base_path, "data", file_name)
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)