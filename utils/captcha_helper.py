# -*- coding:utf-8 -*-
"""
File: captcha_helper.py
Author: Alvin
Date: 2026-08-27
Description: 验证码相关工具（生成 checkKey）
"""

import time
import random
import string


def generate_check_key() -> str:
    """
    生成 checkKey：13位毫秒时间戳 + 4位随机字符（与前端格式一致）
    示例: 1724668800000AbCd
    """
    ts = str(int(time.time() * 1000))
    rand = "".join(random.choices(string.ascii_letters + string.digits, k=4))
    return ts + rand