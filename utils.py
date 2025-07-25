#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import datetime
import re
import urllib.parse
from colorama import Fore, Style

def load_payload_file(file_path):
    """
    加载载荷文件，每行作为一个载荷
    
    Args:
        file_path (str): 载荷文件路径
        
    Returns:
        list: 载荷列表
    """
    try:
        if not os.path.exists(file_path):
            print(f"{Fore.RED}[错误] 载荷文件不存在: {file_path}{Style.RESET_ALL}")
            return []
        
        with open(file_path, 'r', encoding='utf-8') as file:
            # 读取所有行并去除空白
            payloads = [line.strip() for line in file.readlines() if line.strip()]
        
        print(f"{Fore.GREEN}[信息] 成功加载 {len(payloads)} 个载荷{Style.RESET_ALL}")
        return payloads
    
    except Exception as e:
        print(f"{Fore.RED}[错误] 载荷文件加载失败: {str(e)}{Style.RESET_ALL}")
        return []

def save_results(results, file_path):
    """
    保存结果到文件
    
    Args:
        results (dict): 结果数据
        file_path (str): 保存路径
    """
    try:
        # 创建包含结果摘要的数据
        summary = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_requests": results["total"],
            "successful_requests": results["success"],
            "failed_requests": results["failed"],
            "success_rate": f"{(results['success'] / results['total'] * 100):.2f}%" if results["total"] > 0 else "0%",
            "responses": results["responses"]
        }
        
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        # 保存为JSON文件
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(summary, file, indent=2, ensure_ascii=False)
        
        return True
    
    except Exception as e:
        print(f"{Fore.RED}[错误] 结果保存失败: {str(e)}{Style.RESET_ALL}")
        return False

def format_time(seconds):
    """
    格式化时间为易读格式
    
    Args:
        seconds (float): 秒数
        
    Returns:
        str: 格式化后的时间字符串
    """
    if seconds < 0.001:
        return f"{seconds * 1000000:.2f}μs"
    elif seconds < 1:
        return f"{seconds * 1000:.2f}ms"
    else:
        return f"{seconds:.2f}s"

def format_size(size_bytes):
    """
    格式化字节数为易读格式
    
    Args:
        size_bytes (int): 字节数
        
    Returns:
        str: 格式化后的大小字符串
    """
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f}KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f}MB"

def parse_key_value_string(kv_string):
    """
    解析键值对字符串为字典
    
    Args:
        kv_string (str): 键值对字符串，格式为key=value,key2=value2
        
    Returns:
        dict: 解析后的字典
    """
    if not kv_string:
        return {}
    
    result = {}
    pairs = kv_string.split(',')
    
    for pair in pairs:
        if '=' in pair:
            key, value = pair.split('=', 1)
            result[key.strip()] = value.strip()
    
    return result

def is_valid_url(url):
    """
    检查URL是否有效
    
    Args:
        url (str): 要检查的URL
        
    Returns:
        bool: URL是否有效
    """
    # 基本URL格式正则表达式
    url_pattern = re.compile(
        r'^(?:http|https)://'  # http:// 或 https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # 域名
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP地址
        r'(?::\d+)?'  # 可选端口
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    # 使用正则表达式验证URL格式
    if not url_pattern.match(url):
        return False
    
    # 尝试解析URL
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def check_payload_placeholder(text, placeholder="PAYLOAD_PLACEHOLDER"):
    """
    检查文本中是否包含载荷占位符
    
    Args:
        text (str): 要检查的文本
        placeholder (str): 占位符文本，默认为"PAYLOAD_PLACEHOLDER"
        
    Returns:
        bool: 是否包含占位符
    """
    if not text:
        return False
    
    return placeholder in text 