# backend.py
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
import asyncio
import subprocess, os, time, sys, psutil, json
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

app = FastAPI(title="SaleorQA Enterprise System")

# 路径自动定位
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_DIR = os.path.join(BASE_DIR, "reports")
SCREENSHOT_DIR = os.path.join(REPORT_DIR, "screenshots")
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

# 确保目录存在
for d in [REPORT_DIR, SCREENSHOT_DIR]:
    if not os.path.exists(d): 
        os.makedirs(d)
        print(f"✓ 创建目录: {d}")

app.mount("/reports", StaticFiles(directory=REPORT_DIR), name="reports")
app.mount("/screenshots", StaticFiles(directory=SCREENSHOT_DIR), name="screenshots")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- 脚本映射表 ---
SCRIPTS = {
    # 功能测试
    "storefront": "function_tests/test_storefront.py",
    "mail_test": "function_tests/test_fail_demo.py",
    
    # API测试
    "orders": "api_tests/test_orders.py",
    "business": "api_tests/test_business_flow.py",
    "full": "api_tests/test_full_flow.py",

    # UI测试
    "ui_product_browsing": "ui_tests/test_product_browsing.py",
    "ui_search": "ui_tests/test_search_functionality.py",
    "ui_navigation": "ui_tests/test_navigation_flow.py",
}

def send_qq_email(script_id, error_output, report_url):
    """
    从外部模板文件加载邮件内容并发送，增加了增强的错误捕获和调试日志
    """
    try:
        mail_host = "smtp.qq.com"
        mail_user = "198689336@qq.com"
        mail_pass = "codfwhbthflybgcd"
        sender_addr = '198689336@qq.com'
        receiver_addr = '198689336@qq.com'

        # 调试日志：打印接收到的参数
        print(f">>> [邮件调试] 接收到的 script_id = {script_id}")
        print(f">>> [邮件调试] 接收到的 report_url = {report_url}")

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

        # 调试日志：确认模板中的URL
        print(f">>> [邮件调试] 模板填充后的报告链接: {report_url}")

        # 4. 构建并发送邮件
        message = MIMEText(html_content, 'html', 'utf-8')
        message['From'] = formataddr(["SaleorQA监控中心", sender_addr])
        message['To'] = formataddr(["项目管理员", receiver_addr])
        message['Subject'] = Header(f"🔴 任务失败：{script_id}", 'utf-8')

        smtpObj = smtplib.SMTP_SSL(mail_host, 465) 
        smtpObj.login(mail_user, mail_pass)
        smtpObj.sendmail(sender_addr, [receiver_addr], message.as_string())
        smtpObj.quit()
        print(f">>> [邮件服务] 告警已成功发送，邮件中的报告链接: {report_url}")
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
    """执行测试并根据结果触发告警 - 实时流式输出版本"""
    if script_id not in SCRIPTS:
        raise HTTPException(status_code=404, detail=f"脚本 {script_id} 不存在")
    
    print(f"\n{'='*60}")
    print(f"[测试执行] 开始运行测试: {script_id}")
    print(f"[测试执行] 脚本路径: {SCRIPTS[script_id]}")
    print(f"{'='*60}")
    
    timestamp = int(time.time())
    temp_report = os.path.join(REPORT_DIR, f"temp_{timestamp}.html")
    
    # 设置环境变量 - 关键优化
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    env["WDM_LOG_LEVEL"] = "0"
    env["WDM_PROGRESS_BAR"] = "0"
    # 禁用 pytest 的颜色输出（避免 ANSI 转义码干扰）
    env["PYTEST_ADDOPTS"] = "--color=no"
    
    # 构建 pytest 命令
    cmd = [
        sys.executable, "-m", "pytest",
        "-s", "-v",
        "--tb=short",
        "--color=no",  # 禁用颜色
        SCRIPTS[script_id],
        f"--html={temp_report}",
        "--self-contained-html",
        "--maxfail=1"
    ]
    
    print(f"[测试执行] 命令: {' '.join(cmd)}")
    print(f"[测试执行] 工作目录: {BASE_DIR}")
    print(f"[测试执行] 开始执行...")
    
    try:
        # 使用 Popen 实现实时输出
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            env=env,
            cwd=BASE_DIR,
            bufsize=1,  # 行缓冲
            universal_newlines=True
        )
        
        output_lines = []
        start_time = time.time()
        
        # 实时读取输出
        print(f"[测试执行] 实时输出:")
        print("-" * 60)
        
        for line in process.stdout:
            line = line.rstrip()
            if line:
                output_lines.append(line)
                print(f"  {line}")  # 后端控制台实时打印
        
        # 等待进程结束，设置超时
        try:
            returncode = process.wait(timeout=180)  # 3分钟超时
        except subprocess.TimeoutExpired:
            process.kill()
            print(f"[测试执行] ❌ 测试执行超时（180秒）")
            return {
                "status": "failed",
                "output": "测试执行超时（180秒），请检查网络连接或页面加载速度",
                "report_url": ""
            }
        
        elapsed_time = time.time() - start_time
        output_text = "\n".join(output_lines)
        
        print("-" * 60)
        print(f"[测试执行] 执行完成，耗时: {elapsed_time:.2f} 秒")
        print(f"[测试执行] 返回码: {returncode}")
        
    except Exception as e:
        print(f"[测试执行] ❌ 执行异常: {e}")
        return {
            "status": "failed",
            "output": f"执行异常: {str(e)}",
            "report_url": ""
        }
    
    # 确定测试状态
    status = "Success" if returncode == 0 else "Failed"
    final_name = f"Report_{status}_{script_id}_{timestamp}.html"
    final_path = os.path.join(REPORT_DIR, final_name)
    report_url = f"http://127.0.0.1:8000/reports/{final_name}"
    
    # 处理报告文件
    if os.path.exists(temp_report):
        try:
            os.rename(temp_report, final_path)
            print(f"[测试执行] ✓ 报告已保存: {final_name}")
        except Exception as e:
            print(f"[测试执行] ⚠️ 重命名报告失败: {e}")
    else:
        print(f"[测试执行] ⚠️ 警告: 临时报告文件不存在 {temp_report}")
        error_report_path = os.path.join(REPORT_DIR, f"Error_{script_id}_{timestamp}.html")
        with open(error_report_path, 'w', encoding='utf-8') as f:
            f.write(f"<html><body><h1>测试执行失败</h1><p>脚本: {script_id}</p><pre>{output_text}</pre></body></html>")
        final_name = f"Error_{script_id}_{timestamp}.html"
        report_url = f"http://127.0.0.1:8000/reports/{final_name}"
    
    # 失败时发送邮件
    if status == "Failed":
        print(f">>> [系统通知] 脚本 {script_id} 运行失败，准备发送告警邮件...")
        send_qq_email(script_id, output_text, report_url)
    else:
        print(f">>> [系统通知] 脚本 {script_id} 运行成功")
    
    return {
        "status": status.lower(),
        "output": output_text,
        "report_url": report_url
    }

@app.get("/api/sys_info")
def get_sys_info():
    """实时系统资源监控数据"""
    try:
        return {
            "cpu": psutil.cpu_percent(interval=1),
            "memory": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage('/').percent if sys.platform != 'win32' else psutil.disk_usage('C:\\').percent
        }
    except Exception as e:
        print(f"获取系统信息失败: {e}")
        return {"cpu": 0, "memory": 0}

@app.get("/api/reports")
def list_reports():
    """获取历史报告列表"""
    try:
        files = [f for f in os.listdir(REPORT_DIR) if f.endswith('.html')]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(REPORT_DIR, x)), reverse=True)
        
        reports = []
        for f in files[:50]:  # 只返回最新的50个报告
            file_path = os.path.join(REPORT_DIR, f)
            reports.append({
                "name": f,
                "url": f"http://127.0.0.1:8000/reports/{f}",
                "time": time.ctime(os.path.getmtime(file_path)),
                "size": f"{os.path.getsize(file_path) / 1024:.2f} KB"
            })
        return reports
    except Exception as e:
        print(f"获取报告列表失败: {e}")
        return []

@app.get("/api/config")
def get_config():
    """获取配置"""
    if not os.path.exists(CONFIG_PATH):
        default_config = {"baseUrl": "http://demo.saleor.io", "email": "198689336@qq.com"}
        with open(CONFIG_PATH, 'w') as f:
            json.dump(default_config, f)
        return default_config
    
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

@app.post("/api/config")
def save_config(config: dict = Body(...)):
    """保存配置"""
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"[配置] 配置已保存: {config}")
        return {"status": "success", "message": "配置保存成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存配置失败: {str(e)}")

@app.get("/api/screenshots")
def list_screenshots():
    """获取异常快照"""
    try:
        files = [f for f in os.listdir(SCREENSHOT_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(SCREENSHOT_DIR, x)), reverse=True)
        
        screenshots = []
        for f in files[:50]:  # 只返回最新的50个截图
            file_path = os.path.join(SCREENSHOT_DIR, f)
            screenshots.append({
                "name": f,
                "url": f"http://127.0.0.1:8000/screenshots/{f}",
                "time": time.ctime(os.path.getmtime(file_path)),
                "size": f"{os.path.getsize(file_path) / 1024:.2f} KB"
            })
        return screenshots
    except Exception as e:
        print(f"获取截图列表失败: {e}")
        return []

@app.post("/api/cleanup")
async def cleanup_system(action: str = Body(..., embed=True)):
    """
    清理系统数据
    action 类型:
    - 'reports': 清空所有 HTML 报告文件
    - 'screenshots': 清空所有异常快照图片
    - 'all': 清空报告文件和异常快照
    """
    try:
        if action == 'reports':
            deleted_count = 0
            for f in os.listdir(REPORT_DIR):
                if f.endswith(".html"):
                    os.remove(os.path.join(REPORT_DIR, f))
                    deleted_count += 1
            print(f"[清理] 已删除 {deleted_count} 个历史报告文件")
            return {"status": "success", "message": f"已删除 {deleted_count} 个历史报告文件"}
        
        elif action == 'screenshots':
            deleted_count = 0
            for f in os.listdir(SCREENSHOT_DIR):
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    os.remove(os.path.join(SCREENSHOT_DIR, f))
                    deleted_count += 1
            print(f"[清理] 已删除 {deleted_count} 个异常快照文件")
            return {"status": "success", "message": f"已删除 {deleted_count} 个异常快照文件"}
        
        elif action == 'all':
            report_count = 0
            screenshot_count = 0
            
            # 删除报告
            for f in os.listdir(REPORT_DIR):
                if f.endswith(".html"):
                    os.remove(os.path.join(REPORT_DIR, f))
                    report_count += 1
            
            # 删除截图
            for f in os.listdir(SCREENSHOT_DIR):
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    os.remove(os.path.join(SCREENSHOT_DIR, f))
                    screenshot_count += 1
            
            print(f"[清理] 已删除 {report_count} 个报告 + {screenshot_count} 个截图")
            return {"status": "success", "message": f"已删除 {report_count} 个报告文件 + {screenshot_count} 个异常快照"}
        else:
            raise HTTPException(status_code=400, detail=f"不支持的清理类型: {action}")
            
    except Exception as e:
        print(f"[清理] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "reports_count": len([f for f in os.listdir(REPORT_DIR) if f.endswith('.html')]),
        "screenshots_count": len([f for f in os.listdir(SCREENSHOT_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
    }

@app.get("/api/run_stream/{script_id}")
async def run_test_stream(script_id: str):
    """流式执行测试，实时推送终端输出"""
    if script_id not in SCRIPTS:
        raise HTTPException(status_code=404, detail=f"脚本 {script_id} 不存在")
    
    timestamp = int(time.time())
    temp_report = os.path.join(REPORT_DIR, f"temp_{timestamp}.html")
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTEST_ADDOPTS"] = "--color=no"
    env["WDM_LOG_LEVEL"] = "0"
    
    cmd = [
        sys.executable, "-u", "-m", "pytest",  # 添加 -u 强制无缓冲
        "-s", "-v", "--tb=short", "--color=no",
        SCRIPTS[script_id],
        f"--html={temp_report}", "--self-contained-html", "--maxfail=1"
    ]
    
    async def event_generator():
        # 先发送一条测试消息
        yield f"data: {json.dumps({'line': '>>> 测试启动中...'})}\n\n"
        
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            text=True, 
            encoding="utf-8", 
            env=env, 
            cwd=BASE_DIR, 
            bufsize=0  # 无缓冲
        )
        
        output_lines = []
        
        # 使用 iter 读取每一行
        for line in iter(process.stdout.readline, ''):
            line = line.rstrip()
            if line:
                output_lines.append(line)
                yield f"data: {json.dumps({'line': line})}\n\n"
        
        process.wait()
        
        status = "Success" if process.returncode == 0 else "Failed"
        final_name = f"Report_{status}_{script_id}_{timestamp}.html"
        report_url = f"http://127.0.0.1:8000/reports/{final_name}"
        
        if os.path.exists(temp_report):
            os.rename(temp_report, os.path.join(REPORT_DIR, final_name))
        
        if status == "Failed":
            send_qq_email(script_id, "\n".join(output_lines), report_url)
        
        yield f"data: {json.dumps({'done': True, 'status': status.lower(), 'report_url': report_url})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    print(f"\n{'='*60}")
    print(f"SaleorQA Enterprise System 启动中...")
    print(f"后端地址: http://127.0.0.1:8000")
    print(f"报告目录: {REPORT_DIR}")
    print(f"截图目录: {SCREENSHOT_DIR}")
    print(f"{'='*60}\n")
    
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8000,
        log_level="info",
        access_log=True
    )

