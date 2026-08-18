# -*- coding:utf-8 -*-
"""
File: test_login.py
Author: Alvin
Date: 2026-08-11
Description: 测试登录接口
"""

import pytest
import allure
from api.login_api import login
from utils.data_loader import load_yaml
from utils.assertions import assert_login_failure, assert_login_success
from configtest import config_mgr
from utils.modifiers import apply_modifier

login_data = load_yaml("login_data.yaml")

class TestLogin:

    @pytest.mark.parametrize("scenario", login_data["positive_scenarios"], ids=lambda x: x['name'])
    @allure.title('登录成功-{scenario[name]}')
    def test_login_success(self, client, scenario):
        cred = config_mgr.get_credentials(scenario["role"])
        result = login(client, cred["username"], cred["password"])
        token = assert_login_success(result)
        assert token is not None

    @pytest.mark.p1
    @pytest.mark.parametrize("scenario", login_data["negative_scenarios"], ids=lambda x: x['name'])
    @allure.title('登录失败-{scenario[name]}')
    def test_login_failure(self, fresh_client, fresh_cred, scenario):
        raw_username = fresh_cred["username"]
        raw_password = fresh_cred["password"]
        modifier = scenario.get("modifier")
        final_username = apply_modifier(raw_username, modifier, "username")
        final_password = apply_modifier(raw_password, modifier, "password")
        result = login(fresh_client, final_username, final_password)
        assert_login_failure(result)

    


