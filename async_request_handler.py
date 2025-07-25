#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import asyncio
import random
import time
import json
import aiohttp
from typing import List, Dict, Any, Optional
from fake_useragent import UserAgent

class AsyncRequestHandler:
    """异步请求处理类，用于高效地发送大量HTTP请求"""

    def __init__(self, 
                 url: str, 
                 method: str = 'GET', 
                 timeout: float = 10.0,
                 max_connections: int = 100,
                 proxy_pool: Optional[List[str]] = None,
                 proxy_type: str = 'http',
                 rotate_user_agents: bool = False):
        """
        初始化异步请求处理器
        
        参数:
            url (str): 请求的URL
            method (str): HTTP方法 (默认: 'GET')
            timeout (float): 请求超时时间，单位秒 (默认: 10.0)
            max_connections (int): 最大并发连接数 (默认: 100)
            proxy_pool (List[str], 可选): 代理服务器列表，格式为["http://host:port", ...]
            proxy_type (str): 代理类型，当proxy_pool中的代理没有指定协议时使用 (默认: 'http')
            rotate_user_agents (bool): 是否轮换User-Agent (默认: False)
        """
        self.url = url
        self.method = method.upper()
        self.timeout = timeout
        self.max_connections = max_connections
        self.headers = {}
        self.params = {}
        self.data = None
        self.proxy_pool = proxy_pool
        self.proxy_type = proxy_type
        
        # User-Agent设置
        self.rotate_user_agents = rotate_user_agents
        self.user_agents = None
        if self.rotate_user_agents:
            try:
                self.ua = UserAgent()
            except Exception as e:
                print(f"初始化User-Agent失败: {e}，将使用默认User-Agent")
                self.ua = None
                self.user_agents = self.get_default_user_agents()
    
    def set_user_agents(self, user_agents: List[str]):
        """设置自定义User-Agent列表"""
        if user_agents and isinstance(user_agents, list):
            self.user_agents = user_agents
            print(f"已设置 {len(user_agents)} 个自定义User-Agent")
    
    def get_default_user_agents(self) -> List[str]:
        """获取默认的User-Agent列表"""
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
        ]
    
    def get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        if self.ua:
            try:
                return self.ua.random
            except:
                pass
        
        if self.user_agents:
            return random.choice(self.user_agents)
        
        # 如果以上都失败，返回默认的Chrome UA
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    
    def set_headers(self, headers: Dict[str, str]):
        """设置请求头"""
        self.headers = headers
    
    def set_params(self, params: Dict[str, Any]):
        """设置URL参数"""
        self.params = params
    
    def set_data(self, data: Any):
        """设置请求数据"""
        self.data = data
    
    async def send_request(self, payload: str = None, custom_url: str = None) -> Dict[str, Any]:
        """
        发送单个异步请求
        
        参数:
            payload (str, 可选): 请求载荷，将替换URL、头部、参数或数据中的占位符
            custom_url (str, 可选): 自定义URL，如果指定则覆盖默认URL
            
        返回:
            Dict[str, Any]: 包含响应信息的字典
        """
        start_time = time.time()
        
        # 创建会话时设置代理
        proxy = None
        if self.proxy_pool:
            proxy = random.choice(self.proxy_pool)
        
        # 准备请求头
        request_headers = self.headers.copy() if self.headers else {}
        
        # 如果启用了User-Agent轮换，添加随机UA
        if self.rotate_user_agents:
            request_headers['User-Agent'] = self.get_random_user_agent()
        
        # 如果提供了载荷，替换请求参数中的占位符
        request_params = {}
        request_data = None
        url_to_use = custom_url if custom_url else self.url
        
        # 处理params
        if self.params:
            request_params = self.params.copy()
            if payload:
                for key, value in request_params.items():
                    if isinstance(value, str) and "PAYLOAD_PLACEHOLDER" in value:
                        request_params[key] = value.replace("PAYLOAD_PLACEHOLDER", payload)
        
        # 处理data
        if self.data:
            request_data = self.data
            if isinstance(request_data, str) and payload and "PAYLOAD_PLACEHOLDER" in request_data:
                request_data = request_data.replace("PAYLOAD_PLACEHOLDER", payload)
        
        try:
            # 创建TCP连接池限制的客户端会话
            conn = aiohttp.TCPConnector(limit=self.max_connections, ssl=False)
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
                # 根据method选择不同的请求方法
                if self.method == 'GET':
                    async with session.get(url_to_use, 
                                          headers=request_headers,
                                          params=request_params,
                                          proxy=proxy) as response:
                        status_code = response.status
                        response_text = await response.text()
                        response_size = len(response_text)
                
                elif self.method == 'POST':
                    async with session.post(url_to_use,
                                           headers=request_headers, 
                                           params=request_params,
                                           data=request_data,
                                           proxy=proxy) as response:
                        status_code = response.status
                        response_text = await response.text()
                        response_size = len(response_text)
                
                elif self.method == 'PUT':
                    async with session.put(url_to_use, 
                                          headers=request_headers,
                                          params=request_params, 
                                          data=request_data,
                                          proxy=proxy) as response:
                        status_code = response.status
                        response_text = await response.text()
                        response_size = len(response_text)
                
                elif self.method == 'DELETE':
                    async with session.delete(url_to_use, 
                                             headers=request_headers,
                                             params=request_params,
                                             proxy=proxy) as response:
                        status_code = response.status
                        response_text = await response.text()
                        response_size = len(response_text)
                
                elif self.method == 'HEAD':
                    async with session.head(url_to_use, 
                                           headers=request_headers,
                                           params=request_params,
                                           proxy=proxy) as response:
                        status_code = response.status
                        response_text = ""
                        response_size = 0
                
                elif self.method == 'OPTIONS':
                    async with session.options(url_to_use, 
                                              headers=request_headers,
                                              params=request_params,
                                              proxy=proxy) as response:
                        status_code = response.status
                        response_text = await response.text()
                        response_size = len(response_text)
                
                elif self.method == 'PATCH':
                    async with session.patch(url_to_use, 
                                            headers=request_headers,
                                            params=request_params, 
                                            data=request_data,
                                            proxy=proxy) as response:
                        status_code = response.status
                        response_text = await response.text()
                        response_size = len(response_text)
                
                else:
                    raise ValueError(f"不支持的HTTP方法: {self.method}")
                
                end_time = time.time()
                response_time = round(end_time - start_time, 3)
                
                # 构建响应结果
                return {
                    'url': url_to_use,
                    'method': self.method,
                    'status_code': status_code,
                    'response_time': response_time,
                    'response_size': response_size,
                    'payload': payload,
                    'response': response_text[:1000] if response_text else "",  # 只返回部分响应内容
                    'headers': dict(response.headers),
                    'success': 200 <= status_code < 400,  # 2xx和3xx视为成功
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
        except asyncio.TimeoutError:
            end_time = time.time()
            return {
                'url': url_to_use,
                'method': self.method,
                'payload': payload,
                'response_time': round(end_time - start_time, 3),
                'error': '请求超时',
                'success': False,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        
        except Exception as e:
            end_time = time.time()
            return {
                'url': url_to_use,
                'method': self.method,
                'payload': payload,
                'response_time': round(end_time - start_time, 3),
                'error': str(e),
                'success': False,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
    
    async def send_requests_batch(self, count: int, concurrency: int = None) -> Dict[str, Any]:
        """
        批量发送请求
        
        参数:
            count (int): 要发送的请求数量
            concurrency (int, 可选): 并发数，默认使用实例化时设置的max_connections
            
        返回:
            Dict[str, Any]: 包含所有响应的结果字典
        """
        if concurrency is None:
            concurrency = self.max_connections
        
        # 创建任务列表
        tasks = []
        semaphore = asyncio.Semaphore(concurrency)
        
        async def bounded_request():
            async with semaphore:
                return await self.send_request()
        
        # 创建所有任务
        for _ in range(count):
            tasks.append(bounded_request())
        
        # 执行所有任务
        start_time = time.time()
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # 处理结果
        success_count = 0
        failed_count = 0
        result_responses = []
        
        for resp in responses:
            if isinstance(resp, Exception):
                failed_count += 1
                result_responses.append({
                    'url': self.url,
                    'method': self.method,
                    'error': str(resp),
                    'success': False,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                })
            else:
                if resp.get('success', False):
                    success_count += 1
                else:
                    failed_count += 1
                result_responses.append(resp)
        
        # 返回总结果
        return {
            'total': count,
            'success': success_count,
            'failed': failed_count,
            'total_time': round(end_time - start_time, 3),
            'average_time': round((end_time - start_time) / count, 3) if count > 0 else 0,
            'responses': result_responses
        } 