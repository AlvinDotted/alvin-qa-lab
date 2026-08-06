# -*- coding:utf-8 -*-
"""
File: logger.py
Author: Alvin
Date: 2026-08-06
Description: 输出日志
"""

# utils/logger.py
import logging
import os
from logging.handlers import RotatingFileHandler
from configtest import config_mgr

# 1. 定义日志格式（包含时间、模块名、行号）
LOG_FORMAT = "%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 2. 定义日志级别（从环境变量取，默认 INFO）
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# 3. 缓存已经创建好的 logger，避免重复添加 Handler（防止日志重复打印）
_logger_cache = {}

def get_logger(name: str = "AutoTest"):
    # 获取一个 Logger 实例（按模块名隔离）
    if name in _logger_cache:
        return _logger_cache[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    
    # 如果该 logger 已有 handler，直接返回（避免重复加）
    if logger.handlers:
        return logger
    
    # 4. 文件 Handler（按大小切割，保留最近 5 个）
    log_dir = config_mgr.log_dir  
    log_file_path = os.path.join(log_dir, f"{name}.log")  # 按模块名分文件
    
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=10 * 1024 * 1024,  # 10MB 一个文件
        backupCount=5,              # 保留 5 个历史文件
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)  # 文件里记录全部级别（包含 DEBUG）
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(file_handler)
    
    # 缓存起来
    _logger_cache[name] = logger
    return logger

default_logger = get_logger("AutoTest")
