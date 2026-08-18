# -*- coding:utf-8 -*-
"""
File: run.py
Author: Alvin
Date: 2026-08-13
Description: 测试启动脚本 —— 自动生成按环境隔离的报告路径，并调用 pytest
"""

import os
import sys
import time
import argparse
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.absolute()


def parse_args():
    parser = argparse.ArgumentParser(description="运行接口自动化测试")
    parser.add_argument(
        "--env",
        default="test",
        choices=["test", "uat"],
        help="指定运行环境 (test/uat)，默认 test"
    )
    parser.add_argument(
        "--path",
        default="tests",
        help="指定测试路径，可以是目录或文件，默认 tests"
    )
    parser.add_argument(
        "--no-html",
        action="store_true",
        help="禁用 HTML 报告（默认生成）"
    )
    parser.add_argument(
        "--no-allure",
        action="store_true",
        help="禁用 Allure 报告（默认生成）"
    )
    # 解析已知参数，剩余参数透传给 pytest
    known_args, unknown_args = parser.parse_known_args()
    return known_args, unknown_args


def main():
    args, unknown_args = parse_args()

    env = args.env
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    report_root = PROJECT_ROOT / "reports" / env
    html_dir = report_root / "html"
    allure_dir = report_root / "allure-results"

    html_dir.mkdir(parents=True, exist_ok=True)
    allure_dir.mkdir(parents=True, exist_ok=True)

    html_file = html_dir / f"report_{timestamp}.html"

    # 构建 pytest 命令
    cmd = ["pytest", args.path, "-v", "-s"]

    if not args.no_html:
        cmd.append(f"--html={html_file}")
    if not args.no_allure:
        cmd.append(f"--alluredir={allure_dir}")

    from configtest import config_mgr
    cmd.append(f"--base-url={config_mgr.base_url}")
    cmd.append(f"--env={env}")

    # 透传所有未知参数给 pytest（如 -m smoke, -k "xxx", -x 等）
    if unknown_args:
        cmd.extend(unknown_args)

    print("=" * 60)
    print(f"🚀 Runtime environment: {env.upper()}")
    print(f"📁 Test path: {args.path}")
    print(f"📄 HTML report: {html_file}")
    print(f"📊 Allure data: {allure_dir}")
    if unknown_args:
        print(f"🔧 Extra args: {' '.join(unknown_args)}")
    print("=" * 60)
    print(f"执行命令: {' '.join(cmd)}")
    print()

    try:
        env_dict = os.environ.copy()
        env_dict["ENV"] = env
        result = subprocess.run(cmd, env=env_dict)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 运行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()