# CLAUDE.md

本文件为 Claude Code 提供本项目的上下文与协作约定。

## 项目概述

Alvin QA Lab —— LIMS 实验室信息管理系统的**接口自动化测试框架**。
基于 Python + pytest，数据驱动 + 环境隔离 + 双报告（HTML + Allure）。

- 作者：Alvin（8 年测试工程师，苏州）
- 被测系统：LIMS（测试环境 dcoretest / UAT 环境 uatlims）
- 技术栈：Python 3.12 / pytest / requests / allure-pytest / pytest-html / PyYAML / python-dotenv / openpyxl

## 目录结构

```
api/            # 业务封装：http_client(通用 HTTP)、login_api(登录)、sample_manage_api(样品)
config/         # config.yaml：环境定义 + 角色凭证 key 映射
data/           # YAML 数据驱动：login_data.yaml、sample_data.yaml
tests/          # pytest 用例：test_login.py、test_sample_manage.py
utils/          # 通用工具：assertions / data_loader / modifiers / logger / paths / allure_helper 等
conftest.py     # fixtures、命令行参数、markers、modifier 合法性校验
configtest.py   # ConfigManager 单例：环境/凭证/目录拼接
run.py          # 启动脚本：按环境生成隔离报告并调用 pytest
```

## 如何运行

```bash
# 推荐：用启动脚本（自动按环境隔离报告 + 透传 pytest 参数）
python run.py --env test --path tests/test_login.py
python run.py --env uat                     # 跑全部用例

# 或直接 pytest（--env 覆盖 .env 里的 ENV）
pytest tests/test_login.py --env=test

# 只生成某一种报告
python run.py --env test --no-allure
python run.py --env test --no-html
```

- 报告输出到 `reports/{env}/`（html、allure-results、allure-report、allure-report-single）
- Allure 报告依赖本机安装 Allure 3 CLI（`allure generate` / `allure awesome`）
- 日志按环境隔离到 `logs/{env}/`，按模块名分文件、10MB 轮转

## 配置与凭证（重要）

- `config/config.yaml`：环境定义（test/uat 的 base_url、timeout、verify）+ 各角色的凭证 key 名
- `secrets.yaml` 与 `.env`：真实账号密码，**已被 .gitignore 排除，绝不能提交**
- `secrets.example.yaml` / `.env.example`：凭证模板（占位符）
- 凭证解析优先级：环境变量 > secrets.yaml（见 `configtest.py:get_credentials`）
- 多个 `admin_1~admin_5` 账号用于轮换，避免登录失败被锁定

## 核心机制

- **环境隔离**：`--env` / `ENV` 决定 URL、凭证前缀（TEST_/UAT_）、报告与日志目录
- **数据驱动**：用例从 `data/*.yaml` 读场景；`data_loader.py` 用 lru_cache 缓存
- **修饰符**：`utils/modifiers.py` 的 `UsernameModifier`/`PasswordModifier` 枚举 + `apply_modifier()` 生成反向用例的变异值（空、超长、SQL 注入、XSS 等）
- **断言**：`utils/assertions.py` 统一封装（assert_login_success/failure、assert_api_success/failure）
- **markers**：smoke / regression / p0 / p1 / p2（pytest.ini 已注册，YAML 里 `markers` 字段动态打标）

## 关键 fixtures（conftest.py）

| fixture | 说明 |
|---|---|
| `client` | session 级共享 HTTP 客户端（默认头 + 网络重试） |
| `fresh_client` | 清空 token 的干净客户端，避免用例间 token 污染 |
| `fresh_cred` | 随机轮换 admin_N 账号 |
| `client_with_role` | 参数化登录指定角色 |
| `admin_client` | 登录 admin |
| `project_engineering_client` | 登录 项目工程师 |

## 编码约定

- 注释与 docstring 用中文；文件头统一格式：`File / Author: Alvin / Date / Description`
- 业务逻辑只放 `api/`，用例只做「取数据 → 调接口 → 断言」，不写请求细节
- 凭证一律从 `config_mgr.get_credentials(role)` 取，禁止硬编码


