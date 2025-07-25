#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
import requests
from typing import Dict, Any, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('RequestHandler')

class RequestHandler:
    """请求处理类，处理HTTP请求的发送和响应处理"""
    
    def __init__(self, url: str, method: str = 'GET', timeout: float = 10.0):
        """
        初始化请求处理器
        
        Args:
            url: 请求的URL
            method: HTTP方法 (GET/POST/PUT/DELETE等)
            timeout: 请求超时时间(秒)
        """
        self.url = url
        self.method = method.upper()
        self.timeout = timeout
        self.headers = None
        self.params = None
        self.data = None
    
    def set_headers(self, headers: Dict[str, str]):
        """设置请求头"""
        self.headers = headers
    
    def set_params(self, params: Dict[str, Any]):
        """设置URL参数"""
        self.params = params
    
    def set_data(self, data: Any):
        """设置请求数据"""
        self.data = data
    
    def send_request(self) -> Dict[str, Any]:
        """
        发送HTTP请求并处理响应
        
        Returns:
            包含响应信息的字典
        """
        start_time = time.time()
        logger.debug(f"开始发送 {self.method} 请求: {self.url}")
        
        try:
            # 准备请求参数
            request_kwargs = {
                'url': self.url,
                'timeout': self.timeout
            }
            
            if self.headers:
                request_kwargs['headers'] = self.headers
                logger.debug(f"请求头: {self.headers}")
                
            if self.params:
                request_kwargs['params'] = self.params
                logger.debug(f"URL参数: {self.params}")
            
            # 根据HTTP方法添加数据
            if self.method in ['POST', 'PUT', 'PATCH']:
                if self.data:
                    # 尝试解析JSON
                    try:
                        if isinstance(self.data, str):
                            json_data = json.loads(self.data)
                            request_kwargs['json'] = json_data
                            logger.debug(f"JSON数据: {json_data}")
                        else:
                            request_kwargs['data'] = self.data
                            logger.debug(f"表单数据: {self.data}")
                    except json.JSONDecodeError:
                        request_kwargs['data'] = self.data
                        logger.debug(f"请求数据: {self.data}")
            
            # 发送请求
            response = requests.request(self.method.lower(), **request_kwargs)
            
            # 计算响应时间
            end_time = time.time()
            response_time = round(end_time - start_time, 3)
            
            # 处理响应
            logger.debug(f"收到响应: 状态码={response.status_code}, 响应时间={response_time}秒")
            
            result = {
                'url': self.url,
                'method': self.method,
                'status_code': response.status_code,
                'response_time': response_time,
                'response_size': len(response.content),
                'success': 200 <= response.status_code < 400,
                'headers': dict(response.headers)
            }
            
            # 尝试解析响应内容
            try:
                result['response'] = response.json()
                logger.debug("响应是JSON格式")
            except:
                # 如果不是JSON，返回文本内容 (限制长度)
                result['response'] = response.text[:1000]
                logger.debug(f"响应是文本格式, 长度={len(response.text)}")
            
            return result
            
        except requests.exceptions.Timeout:
            end_time = time.time()
            logger.error(f"请求超时: {self.url}")
            return {
                'url': self.url,
                'method': self.method,
                'response_time': round(end_time - start_time, 3),
                'error': '请求超时',
                'success': False
            }
        
        except requests.exceptions.RequestException as e:
            end_time = time.time()
            logger.error(f"请求异常: {str(e)}")
            return {
                'url': self.url,
                'method': self.method,
                'response_time': round(end_time - start_time, 3),
                'error': f'请求异常: {str(e)}',
                'success': False
            }
        
        except Exception as e:
            end_time = time.time()
            logger.error(f"未知错误: {str(e)}")
            return {
                'url': self.url,
                'method': self.method,
                'response_time': round(end_time - start_time, 3),
                'error': f'未知错误: {str(e)}',
                'success': False
            } 