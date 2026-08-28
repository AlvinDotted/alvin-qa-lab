# -*- coding:utf-8 -*-
"""
File: notifier.py
Author: Alvin
Date: 2026-08-22
Description: 封装邮件发送、企业微信、钉钉通知功能
"""

import os
import smtplib
import time
from email import encoders
from email.header import make_header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()
sender_email = os.getenv("SENDER_EMAIL")
sender_password = os.getenv("SENDER_PASSWORD")
smtp_server = os.getenv("SMTP_SERVER")
smtp_port = int(os.getenv("SMTP_PORT", 587))
receiver_email = os.getenv("RECEIVER_EMAIL")

def send_report_email(
    sender_email: str,
    sender_password: str,
    smtp_server: str,
    smtp_port: int,
    receiver_email: str,
    subject: str,
    body: str,
    file_path: str,
):
    print("📧 Preparing to send email...")
    # 1. 构造附件名称
    timestamp = time.strftime("%Y%m%d_%H%M")
    attachment_filename = f"接口测试报告_{timestamp}.html"

    # 2. 创建邮件
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    # 3. 邮件正文
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # 4. 读取 index.html 内容，作为附件发送
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        print(f"❌ Report file not found: {file_path}")
        return
    with open(file_path_obj, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            "attachment",
            filename=make_header([(attachment_filename, "utf-8")]).encode()
        )
        msg.attach(part)

    # 5. 发送
    print("📧 Connecting to SMTP server...")
    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=60) as server:
            server.starttls()
            print("📧 Connection successful. Logging in...")
            server.login(sender_email, sender_password)
            print("📧 Login successful. Sending...")
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print(f"✅ Email sent: {attachment_filename}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
