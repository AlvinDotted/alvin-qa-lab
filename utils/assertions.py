# -*- coding:utf-8 -*-
"""
File: assertions.py
Author: Alvin
Date: 2026-07-31
Description: 统一封装，支持登录专用和通用接口断言
Function:
  1. 登录断言：处理 login_api.py 返回的 dict 格式
  2. 通用断言：处理 requests.Response 原始响应
  3. 辅助断言：字段存在性、非空、值校验等
"""

import json
import allure

# 断言接口成功，返回 result 内容
def assert_api_success(resp):
    if resp.status_code != 200:
        allure.attach(resp.txt, "Response Content", allure.attachment_type.TEXT)
        raise AssertionError(f"HTTP Status Code Error:{resp.status_code}")
    data = resp.json()
    if data.get("success") is False:
        allure.attach(json.dumps(data, indent=2), "Response detail", allure.attachment_type.JSON)
        raise AssertionError(f"Business Error: {data.get('message')}")
    return data.get("result")

# 断言接口失败
def assert_api_failure(resp, expected_message = None):
    data = resp.json()
    if data.get("success") is True:
        raise AssertionError("Expected failure, but got success.")
    if expected_message:
        assert expected_message in data.get("message", ""), f"Expected error message to contain '{expected_message}', but got '{data.get('message')}'. "
    return data

# 断言登录成功，返回 token
def assert_login_success(data: dict):
    if not data.get("success"):
        message = data.get("message", "Unknown error")
        raise AssertionError(f"Login failed: {message}")
    token = data.get("token")
    if not token:
        raise AssertionError("No token in login response.")
    return token

# 断言登录失败
def assert_login_failure(data: dict, expected_message = None):
    if data.get("success"):
        raise AssertionError("Expected login failure, but got success.")
    if expected_message:
        actual_msg = data.get("message", "")
        if expected_message not in actual_msg:
            raise AssertionError(f"Expected error message to contain '{expected_message}'，but got '{actual_msg}'")
    return data