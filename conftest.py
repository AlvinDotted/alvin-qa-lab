# -*- coding:utf-8 -*-
"""
File: conftest.py
Author: Alvin
Date: 2026-08-06
Description: 注册 Pytest 命令行参数，比如 pytest --env=uat, 把 config_mgr 的路径注入到 Allure/HTML 插件中，
让报告自动落到对应环境目录
"""
import os
from configtest import config_mgr
import time


# 1. 添加命令行参数（覆盖 .env 的环境变量）
def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action='store',
        default=None,
        help="指定运行环境: test / uat / prod(优先级高于 .env)"
    )

# 2. 配置报告路径，对接 Allure 和 HTML 插件
def pytest_configure(config):
    env_opt = config.getoption('--env')
    if env_opt:
        os.environ['ENV'] = env_opt

    # 动态设置 Allure 报告目录    
    if hasattr(config.option, 'alluredir'):
        config.option.alluredir = config_mgr.get_allure_dir()

    if hasattr(config, '_metadata'):
        config._metadata["测试环境"] = config_mgr.env.upper()
        config._metadata["执行时间"] = time.strftime("%Y-%m-%d %H:%M:%S")

    # 动态设置 HTML 报告目录
    if hasattr(config.option, 'htmlpath'):
            # 仅当用户未显式指定 --html 时
        if config.option.htmlpath is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.html"
            html_path = os.path.join(config_mgr.get_html_dir(), filename)
            config.option.htmlpath = html_path
        else:
            # 用户已指定，不覆盖，但可以提示已使用自定义路径
            print(f"使用用户指定的 HTML 报告目录: {config.option.htmlpath}")
