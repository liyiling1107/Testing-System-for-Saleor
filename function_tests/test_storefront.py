from pages.home_page import HomePage 

def test_home_page_load(driver):
    home_page = HomePage(driver)
    home_page.open()
    
    # 获取首页展示的第一个商品名
    product_name = home_page.get_first_product_name()
    
    print(f"\n首页第一个商品是: {product_name}")
    assert product_name != ""