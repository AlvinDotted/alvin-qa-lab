# -*- coding:utf-8 -*-
"""
File: data_loader.py
Author: Alvin
Date: 2026-07-31
Description: 数据加载工具 — 从 data/ 目录加载 YAML/JSON 文件
Function:
  - 自动定位项目根目录下的 data/ 文件夹
  - 支持 YAML 和 JSON 格式
  - 带缓存机制，多次请求同一文件不重复读取
  - 友好的报错提示
"""
import os
import json
from functools import lru_cache
import yaml

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_DIR = os.path.join(_PROJECT_ROOT, 'data')


@lru_cache(maxsize=None)
def load_yaml(filename: str):
    return _load_file(filename, "yaml")

@lru_cache(maxsize=None)
def load_json(filename: str):
    return _load_file(filename, "json")

# 内部方法：实际执行文件读取和解析
def _load_file(filename: str, filetype: str):
    file_path = os.path.join(_DATA_DIR, filename)
    if not file_path:
        raise FileNotFoundError(f"Data file {file_path} not found.")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            if filetype == "yaml":
                return yaml.safe_load(f) or {}
            elif filetype == "json":
                return json.load(f) or {}
            else:
                raise ValueError(f"Unsupported file type: {filetype}")
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Yaml parsing failed: {file_path}. \nError details: {e}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Json parsing failed:{file_path}. \nError details: {e.msg}", e.doc, e.pos)

# 清空所有文件缓存（用于调试或热加载）
def clear_cache():
    load_yaml.cache_clear()
    load_json.cache_clear()

# 修改了 YAML 文件后，调用此方法重新加载
def reload_file(filename: str):
    clear_cache()
    return load_yaml(filename)

# 返回 data/ 目录的绝对路径
def get_data_dir():
    return _DATA_DIR

# 列出 data/ 目录下的所有文件，并做文件扩展名过滤，如 "yaml" 或 "json"
def list_data_files(ext: str = None):
    if not os.path.exists(_DATA_DIR):
        return []
    files = os.listdir(_DATA_DIR)
    if ext:
        files = [f for f in files if f.endswith(f".{ext}")]
    return files
