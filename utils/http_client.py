"""
HTTP 客户端封装
提供带重试、超时、代理支持的 HTTP 请求功能
"""
import time
import logging
from typing import Optional, Dict, Any
import httpx
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import settings

logger = logging.getLogger(__name__)


class HttpClient:
    """HTTP 客户端，支持重试和代理"""

    def __init__(
        self,
        timeout: int = None,
        retries: int = None,
        backoff_factor: float = 0.5,
    ):
        self.timeout = timeout or settings.HTTP_TIMEOUT
        self.retries = retries or settings.HTTP_RETRIES
        self.backoff_factor = backoff_factor
        self.proxies = settings.get_proxy_config()

    def get(
        self,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        **kwargs
    ) -> Optional[requests.Response]:
        """
        发送 GET 请求，带指数退避重试

        Args:
            url: 请求 URL
            params: 查询参数
            headers: 请求头
            **kwargs: 其他 requests 参数

        Returns:
            Response 对象，失败返回 None
        """
        for attempt in range(self.retries + 1):
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                    proxies=self.proxies,
                    **kwargs
                )

                # 服务器错误，需要重试
                if response.status_code in {429, 500, 502, 503, 504}:
                    if attempt < self.retries:
                        sleep_time = self.backoff_factor * (2 ** attempt)
                        logger.warning(
                            f"请求 {url} 返回 {response.status_code}，"
                            f"{sleep_time}s 后重试 ({attempt + 1}/{self.retries})"
                        )
                        time.sleep(sleep_time)
                        continue

                return response

            except requests.exceptions.Timeout:
                if attempt < self.retries:
                    sleep_time = self.backoff_factor * (2 ** attempt)
                    logger.warning(f"请求 {url} 超时，{sleep_time}s 后重试")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"请求 {url} 超时，已达最大重试次数")

            except requests.exceptions.RequestException as e:
                if attempt < self.retries:
                    sleep_time = self.backoff_factor * (2 ** attempt)
                    logger.warning(f"请求 {url} 失败: {e}，{sleep_time}s 后重试")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"请求 {url} 失败: {e}")

        return None

    def post(
        self,
        url: str,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        **kwargs
    ) -> Optional[requests.Response]:
        """
        发送 POST 请求，带指数退避重试
        """
        for attempt in range(self.retries + 1):
            try:
                response = requests.post(
                    url,
                    data=data,
                    json=json,
                    headers=headers,
                    timeout=self.timeout,
                    proxies=self.proxies,
                    **kwargs
                )

                if response.status_code in {429, 500, 502, 503, 504}:
                    if attempt < self.retries:
                        sleep_time = self.backoff_factor * (2 ** attempt)
                        logger.warning(
                            f"请求 {url} 返回 {response.status_code}，"
                            f"{sleep_time}s 后重试"
                        )
                        time.sleep(sleep_time)
                        continue

                return response

            except requests.exceptions.RequestException as e:
                if attempt < self.retries:
                    sleep_time = self.backoff_factor * (2 ** attempt)
                    logger.warning(f"请求 {url} 失败: {e}，{sleep_time}s 后重试")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"请求 {url} 失败: {e}")

        return None


class HttpxClient:
    """使用 httpx 的异步友好客户端"""

    def __init__(
        self,
        timeout: int = None,
        retries: int = None,
        backoff_factor: float = 0.5,
        verify_ssl: bool = False,
    ):
        self.timeout = timeout or settings.HTTP_TIMEOUT
        self.retries = retries or settings.HTTP_RETRIES
        self.backoff_factor = backoff_factor
        self.verify_ssl = verify_ssl
        # httpx 使用 proxy 参数，支持字典格式 {'http://': '...', 'https://': '...'}
        proxy_config = settings.get_proxy_config()
        # 取 https:// 代理（httpx 格式），如果没有则取 http://
        self.proxy = proxy_config.get("https://") or proxy_config.get("http://") if proxy_config else None

    def get(
        self,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> Optional[httpx.Response]:
        """发送 GET 请求"""
        for attempt in range(self.retries + 1):
            try:
                with httpx.Client(
                    verify=self.verify_ssl,
                    timeout=self.timeout,
                    proxy=self.proxy,
                    follow_redirects=True,  # 跟随 301/302 重定向
                ) as client:
                    response = client.get(url, params=params, headers=headers)

                    if response.status_code in {429, 500, 502, 503, 504}:
                        if attempt < self.retries:
                            sleep_time = self.backoff_factor * (2 ** attempt)
                            logger.warning(
                                f"请求 {url} 返回 {response.status_code}，重试中..."
                            )
                            time.sleep(sleep_time)
                            continue

                    return response

            except httpx.TransportError as e:
                if attempt < self.retries:
                    sleep_time = self.backoff_factor * (2 ** attempt)
                    logger.warning(f"请求 {url} 失败: {e}，{sleep_time}s 后重试")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"请求 {url} 失败: {e}")

        return None


# 全局客户端实例
http_client = HttpClient()
httpx_client = HttpxClient()
