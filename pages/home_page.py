from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from pages.base_page import BasePage
import time
import os

class HomePage(BasePage):
    """
    Saleor 商城首页页面对象
    适配 Next.js Storefront 的 data-testid 结构
    """
    
    # 定位器：根据 product-element.tsx 源码确定
    PRODUCT_CARDS = (By.CSS_SELECTOR, '[data-testid="ProductElement"]')
    PRODUCT_NAME_TAG = (By.TAG_NAME, "h3")
    
    # 备用定位器（如果主定位器失败）
    FALLBACK_PRODUCT_CARDS = (By.CSS_SELECTOR, '[data-testid="ProductElement"], .product-card, [data-testid="product-card"]')
    FALLBACK_PRODUCT_NAME = (By.CSS_SELECTOR, "h3, .product-name, [data-testid='product-name']")

    def __init__(self, driver):
        super().__init__(driver)
        # 从环境变量或配置读取，默认使用本地
        self.url = os.getenv('FRONTEND_URL', 'http://localhost:3000')

    def open(self):
        """打开首页，增加超时处理和错误捕获"""
        try:
            print(f"正在访问: {self.url}")
            
            # 设置页面加载超时
            self.driver.set_page_load_timeout(30)
            self.driver.get(self.url)
            
            # 等待页面基本加载完成
            WebDriverWait(self.driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            print(f"✓ 页面加载成功")
            print(f"  当前标题: {self.driver.title}")
            print(f"  当前URL: {self.driver.current_url}")
            
        except TimeoutException:
            print(f"✗ 页面加载超时: {self.url}")
            # 尝试使用 JavaScript 停止加载
            try:
                self.driver.execute_script("window.stop();")
                print("  已尝试停止页面加载")
            except:
                pass
            raise TimeoutException(f"页面加载超时（30秒）: {self.url}")
            
        except WebDriverException as e:
            print(f"✗ WebDriver 错误: {e}")
            raise
        except Exception as e:
            print(f"✗ 未知错误: {e}")
            raise

    def get_product_names(self):
        """获取首页所有展示的商品名称列表"""
        try:
            # 等待页面主要内容加载
            WebDriverWait(self.driver, 20).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # 尝试等待商品卡片加载（使用主定位器）
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda d: len(d.find_elements(*self.PRODUCT_CARDS)) > 0
                )
                cards = self.driver.find_elements(*self.PRODUCT_CARDS)
                print(f"✓ 找到 {len(cards)} 个商品卡片（主定位器）")
                
            except TimeoutException:
                # 如果主定位器失败，尝试备用定位器
                print("主定位器未找到商品，尝试备用定位器...")
                try:
                    WebDriverWait(self.driver, 10).until(
                        lambda d: len(d.find_elements(*self.FALLBACK_PRODUCT_CARDS)) > 0
                    )
                    cards = self.driver.find_elements(*self.FALLBACK_PRODUCT_CARDS)
                    print(f"✓ 找到 {len(cards)} 个商品卡片（备用定位器）")
                except TimeoutException:
                    print("✗ 未找到任何商品卡片")
                    return []
            
            # 提取商品名称
            names = []
            for idx, card in enumerate(cards):
                try:
                    # 尝试多种方式获取商品名称
                    name_text = None
                    
                    # 方式1：在主卡片内查找 h3 标签
                    try:
                        name_text = card.find_element(*self.PRODUCT_NAME_TAG).text.strip()
                    except:
                        pass
                    
                    # 方式2：如果方式1失败，使用备用选择器
                    if not name_text:
                        try:
                            name_text = card.find_element(*self.FALLBACK_PRODUCT_NAME).text.strip()
                        except:
                            pass
                    
                    # 方式3：尝试获取 data-testid 属性
                    if not name_text:
                        try:
                            name_text = card.get_attribute("data-testid")
                        except:
                            pass
                    
                    if name_text:
                        names.append(name_text)
                        print(f"  商品 {idx+1}: {name_text[:50]}")
                    else:
                        print(f"  商品 {idx+1}: 无法获取名称")
                        
                except Exception as e:
                    print(f"  商品 {idx+1}: 解析失败 - {e}")
                    continue
            
            print(f"✓ 成功获取 {len(names)} 个商品名称")
            return names
            
        except TimeoutException as e:
            print(f"\n✗ [UI Error] 等待商品列表超时: {e}")
            return []
        except Exception as e:
            print(f"\n✗ [UI Error] 获取商品列表失败: {e}")
            return []

    def get_first_product_name(self):
        """获取列表中的第一个商品名称"""
        names = self.get_product_names()
        if names:
            print(f"\n✓ 首页第一个商品是: {names[0]}")
            return names[0]
        else:
            print(f"\n✗ 未找到任何商品")
            return ""
    
    def wait_for_page_load(self, timeout=30):
        """等待页面完全加载"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            return True
        except TimeoutException:
            print(f"页面加载超时（{timeout}秒）")
            return False
    
    def is_page_accessible(self):
        """检查页面是否可访问"""
        try:
            self.driver.set_page_load_timeout(10)
            self.driver.get(self.url)
            return True
        except:
            return False
        finally:
            # 恢复原来的超时设置
            self.driver.set_page_load_timeout(30)