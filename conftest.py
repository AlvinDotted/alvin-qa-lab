# -*- coding:utf-8 -*-
"""
File: conftest.py
Author: Alvin
Date: 2026-08-06
Description: 注册 Pytest 命令行参数，比如 pytest --env=uat, 把 config_mgr 的路径注入到 Allure/HTML 插件中，
让报告自动落到对应环境目录, 配置全局客户端。
"""
import os
import random
import pytest
from configtest import config_mgr
import time
import allure
from api.http_client import HTTPClient
from api.login_api import login_as
from utils.logger import get_logger
from utils.modifiers import UsernameModifier, PasswordModifier

# 1. 添加命令行参数（覆盖 .env 的环境变量）
def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action='store',
        default=None,
        help="Specify the runtime environment: test / uat (overrides .env)."
    )

# 在测试收集阶段：1）校验 modifier 合法性；2）动态添加 markers
def pytest_collection_modifyitems(config, items):
    valid_username = {m.value for m in UsernameModifier}
    valid_password = {m.value for m in PasswordModifier}
    for item in items:
        if "test_login_failure" not in item.name:
            continue
        scenario = getattr(item, "callspec", None)
        if scenario is None:
            continue
        modifier = scenario.params.get("scenario", {}).get("modifier")
        if not modifier:
            continue
        if modifier.endswith("_username") and modifier not in valid_username:
            raise ValueError(f"Unknown username modifier: {modifier}")
        if modifier.endswith("_password") and modifier not in valid_password:
            raise ValueError(f"Unknown password modifier: {modifier}")
    for item in items:
        if not hasattr(item, "callspec"):
            continue
        scenario = item.callspec.params.get("scenario")
        if not scenario or not isinstance(scenario, dict):
            continue
        markers = scenario.get("markers", [])
        for marker in markers:
            item.add_marker(getattr(pytest.mark, marker))

def pytest_html_report_title(report):
    report.title = f"测试报告 - {config_mgr.env.upper()}"

# 每次返回不同的测试账号（轮换使用，避免限流）
@pytest.fixture
def fresh_cred():
    num = random.randint(1, 5)  
    return config_mgr.get_credentials(f"admin_{num}")

# 全局 HTTP 客户端, 所有测试用例共享同一个实例（Session 自动保持 Cookie/Token）, 测试全部结束后自动关闭连接池。
@pytest.fixture(scope="session")
def client():
    _client = HTTPClient(base_url=config_mgr.base_url, timeout=config_mgr.timeout, verify=config_mgr.verify)
    _client.logger = get_logger('HTTP')
    _client.session.headers.update({
        "X-App-Id": "dTenant",          
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh_CN",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    })
    yield _client
    _client.close()

@pytest.fixture
def admin_client(client):
    login_as(client, "admin")
    return client

@pytest.fixture
def project_engineering_client(client):
    login_as(client, "project_engineering")
    return client

# 根据参数动态登录指定角色
@pytest.fixture
def client_with_role(client, request):
    role = request.param
    login_as(client, role)
    return client

# 每次调用返回一个干净的客户端（自动清除之前的token）
@pytest.fixture
def fresh_client(client):
    client.set_token("") 
    return client

# 测试结束后生成 environment.properties（Allure 环境信息）
def pytest_sessionfinish(session, exitstatus):
    allure_dir = config_mgr.get_allure_dir()
    os.makedirs(allure_dir, exist_ok=True)
    env_file = os.path.join(allure_dir, "environment.properties")
    with open(env_file, "w", encoding="utf-8") as f:
        f.write(f"Environment={config_mgr.env.upper()}\n")
        f.write(f"BaseURL={config_mgr.base_url}\n")
        f.write(f"PythonVersion={os.getenv('PYTHON_VERSION', '3.12')}\n")
        f.write(f"TestTime={time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    print(f"✅ environment.properties generated: {env_file}")

# 在所有测试用例中动态添加环境标签
@pytest.fixture(autouse=True)
def add_environment_label():
    allure.dynamic.label("environment", config_mgr.env)  # 动态读取当前环境