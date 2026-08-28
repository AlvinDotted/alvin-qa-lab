# -*- coding:utf-8 -*-
"""
File: run.py
Author: Alvin
Date: 2026-08-13
Description: 测试启动脚本 —— 自动生成按环境隔离的报告路径，并调用 pytest
"""

import os
import sys
import shutil
import argparse
import subprocess
import time
from configtest import config_mgr
from utils.paths import PROJECT_ROOT, LOGO_PATH, FAVICON_PATH
from utils.allure_helper import replace_favicon, replace_allure_logo, create_allure_config


def parse_args():
    parser = argparse.ArgumentParser(description="Execute automated API tests")
    parser.add_argument(
        "--env",
        default="test",
        choices=["test", "uat"],
        help="Specify the runtime environment (test/uat). Default is test."
    )
    parser.add_argument(
        "--path",
        default="tests",
        help="Specify the test path (directory or file). Default: tests"
    )
    parser.add_argument(
        "--no-html",
        action="store_true",
        help="Disable HTML report (enabled by default)"
    )
    parser.add_argument(
        "--no-allure",
        action="store_true",
        help="Disable Allure report (enabled by default)"
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
    cmd = ["pytest", args.path, "-v", "-s"]
    if not args.no_html:
        cmd.append(f"--html={html_file}")
    if not args.no_allure:
        cmd.append(f"--alluredir={allure_dir}")
    cmd.append(f"--base-url={config_mgr.base_url}")
    cmd.append(f"--env={env}")
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
    print(f"Execute the command: {' '.join(cmd)}")
    print()
    try:
        env_dict = os.environ.copy()
        env_dict["ENV"] = env
        result = subprocess.run(cmd, env=env_dict)
        # 生成 Allure 报告（测试执行完成后）
        if not args.no_allure:
            print("\n" + "=" * 60)
            print("📊 Generating Allure report...")
            print("=" * 60)
            allure_cmd = shutil.which("allure") or shutil.which("allure.cmd")
            if not allure_cmd:
                print("⚠️ WARNING: 'allure' command not found. Please ensure Allure 3 is installed and added to the PATH")
            else:
                allure_report_dir = report_root / "allure-report"
                # 动态生成配置文件（按环境区分历史数据）
                config_file = create_allure_config(env)
                # 删除旧的报告目录
                if allure_report_dir.exists():
                    print(f"🗑️ Remove old report directories: {allure_report_dir}")
                    shutil.rmtree(allure_report_dir)
                result_allure = subprocess.run([
                    allure_cmd,
                    "generate",
                    "--config", str(config_file),
                    "-o", str(allure_report_dir),
                    str(allure_dir)
                ])
                if result_allure.returncode == 0:
                    print(f"✅ Allure standard report generated: {allure_report_dir / 'index.html'}")
                    # 常规报告：favicon 无配置项，生成后替换
                    if FAVICON_PATH.exists():
                        n = replace_favicon(allure_report_dir / "index.html", FAVICON_PATH)
                        print(f"✅ Favicon replaced in standard report, in total {n} ")

                    single_dir = report_root / "allure-report-single"
                    single_dir.mkdir(parents=True, exist_ok=True)
                    single_cmd = [
                        allure_cmd,
                        "awesome",
                        str(allure_dir),
                        "--single-file",
                        "--config", str(config_file),
                        "--report-language", "en",  
                        "-o", str(single_dir),
                    ]
                    result_single = subprocess.run(single_cmd)
                    if result_single.returncode == 0:
                        single_file = single_dir / "index.html"
                        print(f"✅ Single-file report generated: {single_file}")
                        print(f"   Can be opened by double-clicking: file:///{single_file}")
                        if LOGO_PATH.exists():
                            ok = replace_allure_logo(single_file, LOGO_PATH)
                            print(f"✅ Logo replaced in single-file report: ({"Success" if ok else "Target not found"})\n")
                        # 单文件报告：favicon 无配置项，生成后替换
                        if FAVICON_PATH.exists():
                            n = replace_favicon(single_file, FAVICON_PATH)
                            print(f"✅ Favicon replaced in standard report, in total {n} ")
                        # 发送测试报告邮件（附件为allure生成的单文件HTML报告）
                        # send_report_email(
                        #     sender_email=sender_email,
                        #     sender_password=sender_password,
                        #     smtp_server=smtp_server,
                        #     smtp_port=smtp_port,
                        #     receiver_email=receiver_email,
                        #     subject="接口自动化测试报告",
                        #     body="测试已执行完毕，详细报告请见附件。",
                        #     file_path=str(single_file)
                        # )
                    else:
                        print(f"❌ Single-file report generation failed. Error code: {result_single.returncode}")
                else:
                    print(f"❌ Allure report generation failed. Error code: {result_allure.returncode}")     
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n⚠️ Test execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Run failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()