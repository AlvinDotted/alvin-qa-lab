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
import re


# 1. 加载 .env，启动时把.env里面的值注入到环境变量
load_dotenv() 
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__)) # 项目根目录的绝对路径

class ConfigManager:

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
       # 1. 加载 config.yaml
        with open("config/config.yaml", "r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)
        # 2. 递归替换占位符 {XXX} 为环境变量值
        self._config = self._replace_placeholders(raw_config)
        # 3. 加载 secrets.yaml
        try:
            with open("secrets.yaml", "r", encoding="utf-8") as f:
                self._secrets = yaml.safe_load(f) or {}
        except FileNotFoundError:
            self._secrets = {}

    def _replace_placeholders(self, obj):
        """递归替换字符串中 {XXX} 为 os.getenv('XXX')"""
        if isinstance(obj, dict):
            return {k: self._replace_placeholders(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._replace_placeholders(item) for item in obj]
        if isinstance(obj, str):
            pattern = r"\{([A-Z_]+)\}"
            def replacer(match):
                key = match.group(1)
                return os.getenv(key, match.group(0))  # 如果环境变量不存在，保留原占位符
            return re.sub(pattern, replacer, obj)
        return obj

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

    @property
    def timeout(self):   
        return self._config["environments"][self.env].get("timeout", 30)

    def get_credentials(self, role: str):
        # 1. 先尝试不带前缀的（test，uat账号相同，给CI用）
        user_key = f"{role.upper()}_USERNAME"
        password_key = f"{role.upper()}_PASSWORD"
        user = os.getenv(user_key)
        password = os.getenv(password_key)
        # 2. 如果没取到，尝试带环境前缀的（兼容旧配置）
        if user is None:
            env_prefix = self.env.upper()
            user_key_with_env = f"{env_prefix}_{role.upper()}_USERNAME"
            password_key_with_env = f"{env_prefix}_{role.upper()}_PASSWORD"
            user = os.getenv(user_key_with_env)
            password = os.getenv(password_key_with_env)
        # 3. 如果还是没有，从 secrets.yaml 读取（本地调试用）
        if user is None:
            user = self._secrets.get(user_key) or self._secrets.get(f"{self.env.upper()}_{role.upper()}_USERNAME")
        if password is None:
            password = self._secrets.get(password_key) or self._secrets.get(f"{self.env.upper()}_{role.upper()}_PASSWORD")
        return {"username": user, "password": password}

    # 5. 当前环境的报告总目录和日志目录（如 ./reports/test）
    @property
    def report_dir(self):
        return os.path.join(PROJECT_ROOT, 'reports', self.env)

    def get_allure_dir(self):
        path = os.path.join(self.report_dir, 'allure-results')
        os.makedirs(path, exist_ok=True)
        return path

    def get_html_dir(self):
        path = os.path.join(self.report_dir, 'html')
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def log_dir(self):
        log_path = os.path.join(PROJECT_ROOT, 'logs', self.env)
        os.makedirs(log_path, exist_ok=True)
        return log_path

    @property
    def verify(self):
        return self._config["environments"][self.env].get("verify", True)

    @property
    def redis_host(self) -> str:
        """获取当前环境的 Redis 主机地址"""
        return self._config["environments"][self.env].get("redis", {}).get("host", "localhost")

    @property
    def redis_port(self) -> int:
        """获取当前环境的 Redis 端口"""
        return self._config["environments"][self.env].get("redis", {}).get("port", 6379)

    @property
    def redis_password(self) -> str:
        """获取当前环境的 Redis 密码"""
        return self._config["environments"][self.env].get("redis", {}).get("password", "")

    @property
    def redis_db(self) -> int:
        """获取当前环境的 Redis 数据库编号"""
        return self._config["environments"][self.env].get("redis", {}).get("db", 0)
    

config_mgr = ConfigManager()