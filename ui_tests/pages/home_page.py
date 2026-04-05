from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# 使用绝对导入，确保 package 识别正常
from ui_tests.pages.base_page import BasePage

class HomePage(BasePage):
    """
    Saleor 商城首页页面对象
    适配 Next.js Storefront 的 data-testid 结构
    """
    
    # 定位器：根据 product-element.tsx 源码确定
    PRODUCT_CARDS = (By.CSS_SELECTOR, '[data-testid="ProductElement"]')
    PRODUCT_NAME_TAG = (By.TAG_NAME, "h3")

    def __init__(self, driver):
        super().__init__(driver)
        # 根据实际环境修改 URL
        self.url = "http://localhost:3000/"

    def open(self):
        """打开首页"""
        self.driver.get(self.url)

    def get_product_names(self):
        """获取首页所有展示的商品名称列表"""
        try:
            # 1. 等待至少一个商品卡片加载完成
            WebDriverWait(self.driver, 10).until(
                lambda d: len(d.find_elements(*self.PRODUCT_CARDS)) > 0
            )
            
            # 2. 抓取所有卡片
            cards = self.driver.find_elements(*self.PRODUCT_CARDS)
            names = []
            for card in cards:
                try:
                    # 在每个卡片内部查找 h3 标签
                    name_text = card.find_element(*self.PRODUCT_NAME_TAG).text.strip()
                    if name_text:
                        names.append(name_text)
                except Exception:
                    continue
            return names
        except Exception as e:
            print(f"\n[UI Error] 获取商品列表失败: {e}")
            return []

    def get_first_product_name(self):
        """获取列表中的第一个商品名称（适配 test_full_flow.py）"""
        names = self.get_product_names()
        return names[0] if names else None
    
    # 在 home_page.py 中补充：
    def get_first_product_name(self):
        names = self.get_product_names()
        return names[0] if names else ""