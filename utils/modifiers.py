# -*- coding:utf-8 -*-
"""
File: modifiers.py
Author: Alvin
Date: 2026-08-17
Description: 动态修改测试数据
"""

from enum import Enum

class UsernameModifier(Enum):
    EMPTY = "empty_username"
    NOT_EXIST = "not_exist_username"
    LEADING_SPACE = "leading_space_username"
    TRAILING_SPACE = "trailing_space_username"
    BOTH_SPACE = "both_space_username"
    TOO_LONG = "too_long_username"
    SQL_INJECTION = "sql_injection_username"
    XSS = "xss_username"

class PasswordModifier(Enum):
    EMPTY = "empty_password"
    WRONG = "wrong_password"
    LEADING_SPACE = "leading_space_password"
    TRAILING_SPACE = "trailing_space_password"
    BOTH_SPACE = "both_space_password"
    TOO_LONG = "too_long_password"
    SQL_INJECTION = "sql_injection_password"
    XSS = "xss_password"

def apply_modifier(value: str, modifier: str, field_type: str) -> str:
    """
    根据修饰符和字段类型生成实际的测试值
    Args:
        value: 原始值（从 secrets 读取）
        modifier: 修饰符名称
        field_type: 字段类型（"username" 或 "password"）
    Returns:
        处理后的值
    """
    if modifier is None:
        return value

    if field_type == "username":
        return _apply_username_modifier(value, modifier)
    elif field_type == "password":
        return _apply_password_modifier(value, modifier)
    else:
        raise ValueError(f"Unknown field type: {field_type}")

# 用户名修饰符处理
def _apply_username_modifier(value: str, modifier: str) -> str:
    # 密码修饰符 → 用户名不处理，返回原值
    if modifier.endswith("_password"):
        return value

    # 用户名修饰符处理（利用枚举校验）
    try:
        mod = UsernameModifier(modifier)
    except ValueError:
        raise ValueError(f"Unknown username modifier: {modifier}")

    if mod == UsernameModifier.EMPTY:
        return ""
    if mod == UsernameModifier.NOT_EXIST:
        return "fake_user_999"
    if mod == UsernameModifier.LEADING_SPACE:
        return f" {value}"
    if mod == UsernameModifier.TRAILING_SPACE:
        return f"{value} "
    if mod == UsernameModifier.BOTH_SPACE:
        return f" {value} "
    if mod == UsernameModifier.TOO_LONG:
        return "a" * 101
    if mod == UsernameModifier.SQL_INJECTION:
        return "' OR '1'='1"
    if mod == UsernameModifier.XSS:
        return "<script>alert(1)</script>"

    return value  # 兜底

# 密码修饰符处理
def _apply_password_modifier(value: str, modifier: str) -> str:
    # 用户名修饰符 → 密码不处理，返回原值
    if not modifier.endswith("_password"):
        return value

    # 密码修饰符处理（利用枚举校验）
    try:
        mod = PasswordModifier(modifier)
    except ValueError:
        raise ValueError(f"Unknown password modifier: {modifier}")

    if mod == PasswordModifier.EMPTY:
        return ""
    if mod == PasswordModifier.WRONG:
        return f"{value}wrong"
    if mod == PasswordModifier.LEADING_SPACE:
        return f" {value}"
    if mod == PasswordModifier.TRAILING_SPACE:
        return f"{value} "
    if mod == PasswordModifier.BOTH_SPACE:
        return f" {value} "
    if mod == PasswordModifier.TOO_LONG:
        return "a" * 101
    if mod == PasswordModifier.SQL_INJECTION:
        return "' OR '1'='1"
    if mod == PasswordModifier.XSS:
        return "<script>alert(1)</script>"

    return value  # 兜底