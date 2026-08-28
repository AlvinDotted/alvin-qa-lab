# -*- coding: utf-8 -*-
"""
File: allure_helper.py
Author: Alvin
Date: 2026-08-21
Description: Allure 3 报告定制logo / favicon
"""

import base64
import json
import re
from pathlib import Path
from utils.paths import LOGO_PATH, PROJECT_ROOT

# 支持的图片格式 -> MIME 类型
MIME_MAP = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".webp": "image/webp",
}

# 把图片文件转成 base64 data URI，文件不存在返回空字符串
def image_to_data_url(image_path: Path):
    if not image_path.exists():
        return ""
    ext = image_path.suffix.lower()
    mime = MIME_MAP.get(ext, "image/png")
    data = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{data}"

# 替换 index.html 中的 favicon link 标签 href，返回替换次数
def replace_favicon(html_path: Path, favicon_path: Path):
    data_uri = image_to_data_url(favicon_path)
    if not data_uri:
        return 0
    html = html_path.read_text(encoding="utf-8")

    # 匹配 <link rel="icon" href="..."> 或 <link rel="shortcut icon" href="...">
    # 兼容单双引号、属性顺序、自闭合标签
    # Allure 3 默认 favicon 是内联 SVG，href 值内部可能含单引号（如 width='32'），
    # 所以必须按 href 的外层引号类型匹配值（值内部允许出现相反的引号），
    # 不能用 [^"']* 匹配值，否则会把含单引号的内联 SVG 截断、损坏 HTML。
    pattern = re.compile(
        r'(<link[^>]*?rel=["\'](?:shortcut\s+)?icon["\'][^>]*?href=)(["\'])(.*?)(\2[^>]*>)',
        re.IGNORECASE | re.DOTALL,
    )
    new_html, count = pattern.subn(
        lambda m: m.group(1) + '"' + data_uri + '"' + m.group(4), html
    )
    if count == 0:
        # 有些版本 rel 属性在 href 后面，再匹配一次宽松模式
        pattern2 = re.compile(
            r'(<link[^>]*?href=)(["\'])(.*?)(\2[^>]*?rel=["\'](?:shortcut\s+)?icon["\'][^>]*>)',
            re.IGNORECASE | re.DOTALL,
        )
        new_html, count = pattern2.subn(
            lambda m: m.group(1) + '"' + data_uri + '"' + m.group(4), html
        )
    if count > 0:
        html_path.write_text(new_html, encoding="utf-8")
    return count


def replace_allure_logo(html_path: Path, logo_path: Path) -> bool:
    """
    在 Allure 3 单文件/多文件报告的 index.html 中，替换 window.allureReportOptions 里的 logo 字段。
    适用于 allure awesome / allure generate 等命令生成后的兜底修复。
    成功替换返回 True, 未找到目标或替换失败返回 False。
    """
    html = html_path.read_text(encoding="utf-8")
    marker = "window.allureReportOptions = "
    start_idx = html.find(marker)
    if start_idx == -1:
        return False
    json_start = start_idx + len(marker)
    # 精确匹配 JSON 对象（花括号计数，支持字符串转义）
    brace_count = 0
    json_end = None
    in_string = False
    escape = False
    for i, ch in enumerate(html[json_start:], json_start):
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"' and not escape:
            in_string = not in_string
            continue
        if not in_string:
            if ch == "{":
                brace_count += 1
            elif ch == "}":
                brace_count -= 1
                if brace_count == 0:
                    json_end = i + 1
                    break
    if json_end is None:
        return False
    opts_str = html[json_start:json_end]
    try:
        opts = json.loads(opts_str)
    except json.JSONDecodeError:
        return False
    logo_data = image_to_data_url(logo_path)
    if not logo_data:
        return False
    # 修改 logo（插入或替换）
    opts["logo"] = logo_data
    # 重新序列化，保持原样缩进（使用 compact 避免换行破坏 HTML）
    new_opts_str = json.dumps(opts, ensure_ascii=False, separators=(",", ":"))
    new_html = html[:json_start] + new_opts_str + html[json_end:]
    html_path.write_text(new_html, encoding="utf-8")
    return True

# 动态生成 Allure 配置文件（按环境区分 historyPath）
def create_allure_config(env: str):
    config = {
        "name": "SEVB API Test Report",
        "plugins": {
            "awesome": {
                "options": {
                    "reportLanguage": "en",
                    "singleFile": True,           
                    "logo": image_to_data_url(LOGO_PATH),                     
                }
            }
        },
        "historyPath": f"./reports/{env}/history.jsonl",
        "qualityGate": {
            "rules": [
                {"maxFailures": 10, "fastFail": True}
            ]
        }
    }
    config_file = PROJECT_ROOT / f"allurerc_{env}.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    return config_file