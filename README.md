# SaleorQA_System 自动化测试系统

本项目是一个针对 Saleor 电商平台的自动化测试与管理系统，集成了后台管理、API 调试、邮件监控及前端购物流程测试。

## 1. 系统访问地址

在后台成功运行 Saleor 服务后，您可以通过以下链接访问各个模块：

| 模块名称 | 访问地址 | 界面预览 |
| :--- | :--- | :--- |
| **管理员后台** | [http://localhost:9000/dashboard/](http://localhost:9000/dashboard/) | ![图片1](images\1.png) |
| **GraphQL 交互界面** | [http://localhost:8000/graphql/](http://localhost:8000/graphql/) | ![图片2](images\2.png) |
| **邮件测试工具** | [http://localhost:8025/](http://localhost:8025/) | ![图片3](images\3.png) |
| **客户购物前端** | [http://localhost:3000/default-channel](http://localhost:3000/default-channel) | ![图片4](images\4.png) |

---

## 2. 自动化测试脚本运行

请确保您的开发环境为 **Python 3.12**。所有的测试脚本均需在 `SaleorQA_System` 根目录下通过命令行运行。

### 运行指令：

* **运行失败演示用例：**
    ```bash
    py -3.12 -m pytest -s function_tests/test_fail_demo.py
    ```
* **运行 Storefront 前端功能测试：**
    ```bash
    py -3.12 -m pytest -s function_tests/test_storefront.py
    ```
* **运行订单接口测试：**
    ```bash
    py -3.12 -m pytest -s api_tests/test_orders.py
    ```
* **运行全流程接口测试：**
    ```bash
    py -3.12 -m pytest -s api_tests/test_full_flow.py
    ```
* **运行业务流接口测试：**
    ```bash
    py -3.12 -m pytest -s api_tests/test_business_flow.py
    ```

---

## 3. SaleorQA 系统启动

本项目包含一个可视化的 QA 管理系统，启动方式如下：

1.  **启动后端服务：**
    在终端执行以下命令：
    ```bash
    python app/backend.py
    ```
2.  **启动前端界面：**
    后端启动后，直接在文件管理器中双击或在浏览器中打开以下文件：
    `app/frontend/index.html`

---

## 4. SaleorQA 系统操作手册

请参考以下图解说明进行系统操作：

| 步骤 | 操作指引图示 |
| :---: | :--- |
| **01** | ![图片5](images\5.png) |
| **02** | ![图片6](images\6.png) |
| **03** | ![图片7](images\7.png) |
| **04** | ![图片8](images\8.png) |
| **05** | ![图片9](images\9.png) |
| **06** | ![图片10](images\10.png) |
| **07** | ![图片11](images\11.png) |
| **08** | ![图片12](images\12.png) |
| **09** | ![图片13](images\13.png) |
| **10** | ![图片14](images\14.png) |
| **11** | ![图片15](images\15.png) |
| **12** | ![图片16](images\16.png) |
| **13** | ![图片17](images\17.png) |
| **14** | ![图片18](images\18.png) |
| **15** | ![图片19](images\19.png) |
| **16** | ![图片20](images\20.png) |
| **17** | ![图片21](images\21.png) |
| **18** | ![图片22](images\22.png) |
| **19** | ![图片23](images\23.png) |
| **20** | ![图片24](images\24.png) |
| **21** | ![图片25](images\25.png) |
| **22** | ![图片26](images\26.png) |
| **23** | ![图片27](images\27.png) |

---