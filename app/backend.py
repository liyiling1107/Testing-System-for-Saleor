from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import subprocess, os, time, sys, psutil, json
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

app = FastAPI(title="SaleorQA Enterprise System")

# 路径自动定位
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_DIR = os.path.join(BASE_DIR, "reports")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

# 确保目录存在
for d in [REPORT_DIR, SCREENSHOT_DIR]:
    if not os.path.exists(d): os.makedirs(d)

app.mount("/reports", StaticFiles(directory=REPORT_DIR), name="reports")
app.mount("/screenshots", StaticFiles(directory=SCREENSHOT_DIR), name="screenshots")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- 脚本映射表 ---
SCRIPTS = {
    "storefront": "ui_tests/test_storefront.py",
    "orders": "api_tests/test_orders.py",
    "business": "api_tests/test_business_flow.py",
    "full": "api_tests/test_full_flow.py",
    "mail_test": "ui_tests/test_fail_demo.py" 
}

def send_qq_email(script_id, error_output, report_url):
    """
    从外部模板文件加载邮件内容并发送，增加了增强的错误捕获
    """
    try:
        mail_host = "smtp.qq.com"
        mail_user = "198689336@qq.com"
        mail_pass = "codfwhbthflybgcd"
        sender_addr = '198689336@qq.com'
        receiver_addr = '198689336@qq.com'

        # 1. 动态获取模板绝对路径，确保在不同环境下都能找到文件
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, "email_template.html")

        if not os.path.exists(template_path):
            print(f">>> [邮件警告] 找不到模板文件: {template_path}")
            return

        with open(template_path, "r", encoding="utf-8") as f:
            html_template = f.read()

        # 2. 准备替换的数据
        summary = "\n".join(error_output.splitlines()[-12:]) if error_output else "无详细错误日志"
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        platform_info = f"{sys.platform.upper()} Node"

        # 3. 填充模板
        html_content = html_template \
            .replace("{{script_id}}", str(script_id)) \
            .replace("{{time}}", current_time) \
            .replace("{{summary}}", summary) \
            .replace("{{report_url}}", str(report_url)) \
            .replace("{{platform}}", platform_info)

        # 4. 构建并发送邮件
        message = MIMEText(html_content, 'html', 'utf-8')
        message['From'] = formataddr(["SaleorQA监控中心", sender_addr])
        message['To'] = formataddr(["项目管理员", receiver_addr])
        message['Subject'] = Header(f"🔴 任务失败：{script_id}", 'utf-8')

        smtpObj = smtplib.SMTP_SSL(mail_host, 465) 
        smtpObj.login(mail_user, mail_pass)
        smtpObj.sendmail(sender_addr, [receiver_addr], message.as_string())
        smtpObj.quit()
        print(f">>> [邮件服务] 告警已成功发送")
    except Exception as e:
        print(f">>> [邮件服务错误] 发送失败: {e}")

@app.get("/api/statistics")
def get_stats():
    """统计各脚本执行成功与失败的次数"""
    files = [f for f in os.listdir(REPORT_DIR) if f.endswith('.html')]
    stats_breakdown = {}
    for key in SCRIPTS.keys():
        s = len([f for f in files if f"_{key}_" in f and "Success" in f])
        f = len([f for f in files if f"_{key}_" in f and "Failed" in f])
        stats_breakdown[key] = {"success": s, "failed": f}
    return {
        "total": len(files),
        "success": len([f for f in files if "Success" in f]),
        "failed": len([f for f in files if "Failed" in f]),
        "breakdown": stats_breakdown
    }

@app.get("/api/run/{script_id}")
async def run_test(script_id: str):
    """执行测试并根据结果触发告警"""
    if script_id not in SCRIPTS: raise HTTPException(status_code=404)
    
    timestamp = int(time.time())
    temp_report = os.path.join(REPORT_DIR, f"temp_{timestamp}.html")
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    # 运行测试
    cmd = [sys.executable, "-m", "pytest", "-s", SCRIPTS[script_id], f"--html={temp_report}", "--self-contained-html"]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env, cwd=BASE_DIR)
    
    status = "Success" if res.returncode == 0 else "Failed"
    final_name = f"Report_{status}_{script_id}_{timestamp}.html"
    report_url = f"http://127.0.0.1:8000/reports/{final_name}"
    
    if os.path.exists(temp_report):
        os.rename(temp_report, os.path.join(REPORT_DIR, final_name))
    
    # 修复点：传递正确的参数给邮件函数，确保后端不崩溃
    if status == "Failed":
        print(f">>> [系统通知] 脚本 {script_id} 运行失败，准备发送模板邮件...")
        send_qq_email(script_id, res.stdout + res.stderr, report_url)

    return {
        "status": status.lower(),
        "output": res.stdout + res.stderr,
        "report_url": report_url
    }

@app.get("/api/sys_info")
def get_sys_info():
    """实时系统资源监控数据"""
    return {"cpu": psutil.cpu_percent(), "memory": psutil.virtual_memory().percent}

@app.get("/api/reports")
def list_reports():
    """获取历史报告列表"""
    files = sorted([f for f in os.listdir(REPORT_DIR) if f.endswith('.html')], 
                  key=lambda x: os.path.getmtime(os.path.join(REPORT_DIR, x)), reverse=True)
    return [{"name": f, "url": f"http://127.0.0.1:8000/reports/{f}", "time": time.ctime(os.path.getmtime(os.path.join(REPORT_DIR, f)))} for f in files]

@app.get("/api/config")
def get_config():
    if not os.path.exists(CONFIG_PATH): return {"baseUrl": "http://demo.saleor.io", "email": "198689336@qq.com"}
    with open(CONFIG_PATH, 'r') as f: return json.load(f)

@app.post("/api/config")
def save_config(config: dict = Body(...)):
    with open(CONFIG_PATH, 'w') as f: json.dump(config, f)
    return {"status": "success"}

@app.get("/api/screenshots")
def list_screenshots():
    """获取异常快照"""
    files = [f for f in os.listdir(SCREENSHOT_DIR) if f.lower().endswith(('.png', '.jpg'))]
    return [{"name": f, "url": f"http://127.0.0.1:8000/screenshots/{f}"} for f in files]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)