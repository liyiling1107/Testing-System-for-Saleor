import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr # 导入格式化地址的工具

def test_pure_email():
    mail_host = "smtp.qq.com"
    mail_user = "198689336@qq.com"
    mail_pass = "codfwhbthflybgcd" 
    
    # 这里定义发件人和收件人
    my_sender = '198689336@qq.com'
    my_receiver = '198689336@qq.com' 

    content = "这是一条来自 VSCode 终端的修复测试邮件。收到此信说明 RFC5322 格式校验已通过！"
    message = MIMEText(content, 'plain', 'utf-8')
    
    # --- 关键修复点：使用 formataddr 确保格式严格符合标准 ---
    # 格式为: Header(备注名).encode() + <邮箱地址>
    message['From'] = formataddr(["SaleorQA_System", my_sender])
    message['To'] = formataddr(["Admin", my_receiver])
    # --------------------------------------------------
    
    message['Subject'] = Header("终端发信环境测试_修复版", 'utf-8')

    print("正在尝试连接 QQ 邮箱服务器...")
    try:
        smtpObj = smtplib.SMTP_SSL(mail_host, 465) 
        print("连接成功，正在登录...")
        smtpObj.login(mail_user, mail_pass)
        print("登录成功，正在发送...")
        # 注意：sendmail 的第一个参数也必须是 my_sender
        smtpObj.sendmail(my_sender, [my_receiver], message.as_string())
        smtpObj.quit()
        print("\n🎉 成功了！请查看你的 QQ 邮箱收件箱。")
    except Exception as e:
        print(f"\n❌ 依然失败！错误详情: {e}")

if __name__ == "__main__":
    test_pure_email()