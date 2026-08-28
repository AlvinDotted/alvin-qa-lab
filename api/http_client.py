# -*- coding:utf-8 -*-
"""
File: http_client.py
Author: Alvin
Date: 2026-08-07
Description: HTTP 客户端。负责拼接 URL、发送请求、维持 Session。不处理业务逻辑, 不解析业务状态码。
"""

import requests
import logging
import urllib3
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

logger = logging.getLogger(__name__)


class HTTPClient:
    def __init__(self, base_url: str, timeout: int, verify: bool = True):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.verify = verify
        if not verify:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "AutoTest/1.0"
        })

        # 网络抖动重试 2 次，只对 5xx 和 429 生效
        retry = Retry(
            total=2,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _url(self, path: str):
        if path.startswith(("http://", "https://")):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    # 系统实际鉴权头
    def set_token(self, token: str):
        if token:
            self.session.headers["x-access-token"] = token
        else:
            self.session.headers.pop("x-access-token", None)

    # 兼容某些接口
    def set_bearer_token(self, token: str):
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
        else:
            self.session.headers.pop("Authorization", None)

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = self._url(path)
        kwargs.setdefault("timeout", self.timeout)

        logger.info(f"→ {method} {url}")
        resp = self.session.request(method, url, **kwargs)
        logger.info(f"← {resp.status_code} {resp.reason} ({resp.elapsed.total_seconds():.2f}s)")

        return resp

    # 快捷方法
    def get(self, path: str, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs):
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs):
        return self.request("DELETE", path, **kwargs)

    def patch(self, path: str, **kwargs):
        return self.request("PATCH", path, **kwargs)

    def close(self):
        self.session.close()

    

