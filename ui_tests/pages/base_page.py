from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class BasePage:
    """所有 Page 对象的基类"""
    def __init__(self, driver):
        self.driver = driver
        # 统一显式等待时间为 10 秒
        self.wait = WebDriverWait(driver, 10)

    def find_element(self, locator):
        """等待并查找元素（确保元素存在于 DOM 中）"""
        try:
            return self.wait.until(EC.presence_of_element_located(locator))
        except TimeoutException:
            print(f"\n❌ [Timeout] 无法定位元素: {locator}")
            return None

    def find_visible_element(self, locator):
        """等待并确保元素对用户可见"""
        try:
            return self.wait.until(EC.visibility_of_element_located(locator))
        except TimeoutException:
            print(f"\n❌ [Timeout] 元素存在但不可见: {locator}")
            return None

    def get_text(self, locator):
        """获取元素文本"""
        element = self.find_visible_element(locator)
        return element.text.strip() if element else ""