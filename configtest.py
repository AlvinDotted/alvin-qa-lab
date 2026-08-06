# -*- coding:utf-8 -*-
"""
File: configtest.py
Author: Alvin
Date: 2026-08-05
Description: 配置基本信息、环境隔离、角色隔离、报告和日志目录实时拼接
"""

import os
from dotenv import load_dotenv
import yaml


# 1. 加载 .env，启动时把.env里面的值注入到环境变量
load_dotenv() 
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__)) # 项目根目录的绝对路径

class ConfigManager:
    """全局配置管理单例（通过类方法实现）"""
    _instance = None
    _config = None
    _secrets = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_configs()
        return cls._instance

    @property
    def env(self):
        return os.getenv("ENV", "test")  # 默认 test, 动态属性

    # 2. 加载 YAML 配置文件（只执行一次）
    def _load_configs(self):
        with open('config/config.yaml', 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)
        try:
            with open('secret.yaml', 'r', encoding='utf-8') as f:
                self._secrets = yaml.safe_load(f) or {}
        except FileNotFoundError:
            self._secrets = {}
        self._init_report_dirs()

    # 3. 根据当前环境，提前创建好报告存放的目录结构
    def _init_report_dirs(self):
        self._report_root = os.path.join(PROJECT_ROOT, 'reports', self.env)
        self._allure_dir = os.path.join(self._report_root, 'allure-results')
        self._html_dir = os.path.join(self._report_root, 'html')
        os.makedirs(self._allure_dir, exist_ok=True)
        os.makedirs(self._html_dir, exist_ok=True)

    # 4. 获取当前环境配置，并注入真实凭证
    @property
    def base_url(self):
        # 获取当前环境的基础URL
        env_conf = self._config['environments'].get(self.env)
        if not env_conf:
            raise ValueError(f'The {self.env} environment is not defined!')
        return env_conf['base_url']

    def get_credentials(self, role: str):
        # 获取角色用户名和密码
        if role not in self._config['credentials']:
            raise ValueError(f'The {role} role is not defined!')
        keys = self._config['credentials'][role]
        env_profix = self.env.upper()
        user_key = f'{env_profix}_{keys['username_key']}'
        pass_key = f'{env_profix}_{keys['password_key']}'
        user = os.getenv(user_key)
        if user is None:
            user = self._secrets.get(user_key)
        pwd = os.getenv(pass_key)
        if pwd is None:
            pwd = self._secrets.get(pass_key)
        return {'username': user, 'password': pwd}

    # 5. 当前环境的报告总目录和日志目录（如 ./reports/test）
    @property
    def report_dir(self):
        """报告总目录（实时拼接）"""
        return os.path.join(PROJECT_ROOT, 'reports', self.env)

    def get_allure_dir(self):
        """Allure 结果目录（实时拼接，并自动创建）"""
        path = os.path.join(self.report_dir, 'allure-results')
        os.makedirs(path, exist_ok=True)
        return path

    def get_html_dir(self):
        """HTML 报告目录（实时拼接，并自动创建）"""
        path = os.path.join(self.report_dir, 'html')
        os.makedirs(path, exist_ok=True)
        return path

    def log_dir(self):
        log_path = os.path.join(PROJECT_ROOT, 'logs', self.env)
        os.makedirs(log_path, exist_ok=True)
        return log_path
    

config_mgr = ConfigManager()
    
 


