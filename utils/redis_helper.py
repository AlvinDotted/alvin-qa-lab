# -*- coding:utf-8 -*-
"""
File: redis_helper.py
Author: Alvin
Date: 2026-08-27
Description: 配置redis
"""

import re
import time
import redis
from configtest import config_mgr
from utils.logger import get_logger

logger = get_logger("RedisHelper")

# 验证码 key 特征：32位hex + 4位字母数字
CAPTCHA_RE = re.compile(r"^[0-9a-f]{32}[0-9A-Za-z]{4}$")


def get_redis_client():
    """获取 Redis 连接"""
    return redis.Redis(
        host=config_mgr.redis_host,
        port=config_mgr.redis_port,
        password=config_mgr.redis_password,
        db=config_mgr.redis_db,
        decode_responses=True,
        protocol=2,
    )

def normalize_captcha_code(raw: str):
    """
    清洗 Redis 里的验证码 value。
    后端存的是 JSON 字符串如 '"sqat"'，剥掉引号后返回 4 位验证码。
    """
    if raw is None:
        return None
    code = raw.strip('"').strip("'")
    return code if len(code) == 4 else None

def scan_all_keys(client):
    """游标方式扫描全库，避免 keys(*) 阻塞"""
    keys = set()
    cursor = 0
    while True:
        cursor, batch = client.scan(cursor=cursor, count=500)
        keys.update(batch)
        if cursor == 0:
            break
    return keys

def snapshot_keys():
    """必须在调 randomImage 接口【之前】调用"""
    client = get_redis_client()
    return scan_all_keys(client)

def get_captcha_code_from_redis(before_keys, max_wait=10, retry_interval=1.0):
    """轮询对比快照，返回新增验证码。before_keys 来自 snapshot_keys()"""
    client = get_redis_client()
    for i in range(max_wait):
        if i > 0:
            time.sleep(retry_interval)
        new_keys = scan_all_keys(client) - before_keys
        for key in new_keys:
            if CAPTCHA_RE.match(key):
                code = normalize_captcha_code(client.get(key))
                if code:
                    return code
    raise TimeoutError(f"{max_wait}s 内未获取到新增验证码")

