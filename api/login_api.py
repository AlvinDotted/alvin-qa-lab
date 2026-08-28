# -*- coding:utf-8 -*-
"""
File: login_api.py
Author: Alvin
Date: 2026-08-07
Description: 登录相关业务操作封装, 处理登录请求、Token 获取与注入、登录状态校验
"""

from configtest import config_mgr
from typing import Optional
from api.http_client import HTTPClient
from utils.logger import get_logger
import requests
import time
from utils.captcha_helper import generate_check_key
from utils.redis_helper import get_captcha_code_from_redis, snapshot_keys

logger = get_logger("LoginAPI")


def get_captcha_image(
    client: HTTPClient,
    check_key: str = None,
):
    """
    获取验证码图片，返回 (check_key, captcha_code)
    Args:
        client: HTTP 客户端
        check_key: 可选，不传则自动生成
    Returns:
        (check_key, captcha_code)
    """
    if check_key is None:
        check_key = generate_check_key()
    before_keys = snapshot_keys() 
    # 调用验证码接口
    url = f"/dapi/dcore-tenant/sys/randomImage/{check_key}?_t={check_key[:13]}"
    resp = client.get(url)
    data = resp.json()
    if data.get("code") != 0 or data.get("success") is not True:
        raise RuntimeError(
            f"获取验证码失败: code={data.get('code')} message={data.get('message')}"
        )
    # 从 Redis 读取验证码
    captcha_code = get_captcha_code_from_redis(before_keys)
    return check_key, captcha_code


def login(
    client: HTTPClient,
    username: str,
    password: str,
    captcha: str = "",
    check_key: str = None,
    need_captcha: bool = False,
):
    client.set_token("")
    if need_captcha and not captcha:
        check_key, captcha = get_captcha_image(client, check_key)
    payload = {
        "username": username,
        "password": password,
        "captcha": captcha,
        "checkKey": check_key
    }
    try:
        resp = client.post("/dapi/dcore-tenant/sys/login", json=payload)
        try:
            data = resp.json() if resp.text else {}
        except ValueError:
            data = {}
        # 关键判断：success == True
        if resp.status_code == 200 and data.get("success") is True:
            token = data.get("result") 
            if token:
                client.set_token(token)
                logger.info(f"✅ 登录成功: {username}")
                return {
                    "success": True,
                    "code": data.get("code"),
                    "message": data.get("message", "登录成功"),
                    "token": token,
                }
            # 业务成功但没返回 token，接口异常
            logger.warning(f"⚠️ 登录响应无 token: {username}")
            return {
                "success": False,
                "code": data.get("code"),
                "message": "响应中未包含 token",
                "data": data,
            }
        # HTTP 非 200 或 success == False
        logger.warning(
            f"❌ 登录失败: {username} | status={resp.status_code} | "
            f"message={data.get('message', '')}"
        )
        return {
            "success": False,
            "code": data.get("code"),
            "message": data.get("message", f"HTTP {resp.status_code}"),
            "data": data,
        }
    except requests.RequestException as e:
        logger.error(f"🚨 登录请求异常: {username} | {e}")
        return {
            "success": False,
            "code": None,
            "message": f"网络异常: {str(e)}",
        }

# 将当前 client 切换为指定角色
def login_as(client: HTTPClient, role: str):
    cred = config_mgr.get_credentials(role)
    result = login(client, cred['username'], cred['password'], need_captcha=True)
    return result['success']

def logout(
    client: HTTPClient,
    endpoint: str = "/dapi/dcore-tenant/sys/logout",
    method: str = "GET",
    use_timestamp: bool = True,
):
    # 1. 构造 URL（带时间戳防缓存）
    url = endpoint
    if use_timestamp:
        timestamp = int(time.time() * 1000)  # 13位毫秒时间戳
        url = f"{endpoint}?_t={timestamp}"
    # 2. 调用服务端登出接口（即使失败也继续执行本地清理）
    try:
        if method.upper() == "POST":
            resp = client.post(url)
        else:
            resp = client.get(url)
        if resp.status_code == 200:
            # 尝试解析响应，确认服务端是否真的成功
            try:
                data = resp.json()
                if data.get("success") or data.get("code") in [0, 200]:
                    logger.info("✅ 服务端登出成功")
                else:
                    logger.warning(f"⚠️ 服务端登出返回异常: {data.get('message')}")
            except ValueError:
                # 响应不是 JSON，但状态码 200 也算成功
                logger.info("✅ 服务端登出成功（响应非 JSON）")
        else:
            logger.warning(f"⚠️ 服务端登出返回非 200: {resp.status_code}")
    except requests.RequestException as e:
        # 网络异常或超时：记录日志，但不影响本地清除
        logger.warning(f"⚠️ 调用登出接口异常: {e}，继续清理本地 Token")
    # 3. 无论服务端是否成功，本地都清除 Token 和租户信息
    client.set_token("")          
    logger.info("✅ 本地登录状态已清除")
    return True

def is_logged_in(client: HTTPClient) -> bool:
    """检查当前 client 是否持有 Token"""
    headers = client.session.headers
    auth = headers.get("x-access-token", "")
    return len(auth) > 7