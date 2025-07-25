#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import argparse
import sys
import time
import os
import json
import random
from typing import List, Dict, Any, Optional
from colorama import init, Fore, Style
from tqdm.asyncio import tqdm

from async_request_handler import AsyncRequestHandler
from utils import load_payload_file, save_results, parse_key_value_string, is_valid_url, check_payload_placeholder

# 初始化colorama
init(autoreset=True)

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="高性能异步爆破工具 - 对特定URL进行参数爆破测试",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # 基本参数
    parser.add_argument("-u", "--url", required=True, help="目标URL地址")
    parser.add_argument("-m", "--method", default="GET", choices=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"], 
                        help="HTTP请求方法")
    parser.add_argument("-p", "--params", help="请求参数，格式为key=value,key2=value2")
    parser.add_argument("-d", "--data", help="请求数据，JSON格式字符串或表单数据")
    parser.add_argument("-H", "--headers", help="请求头，格式为key=value,key2=value2")
    
    # 性能参数
    parser.add_argument("-c", "--concurrency", type=int, default=100, help="并发连接数")
    parser.add_argument("-n", "--num-requests", type=int, default=1000, help="请求次数")
    parser.add_argument("-T", "--timeout", type=float, default=10.0, help="请求超时时间(秒)")
    parser.add_argument("--delay", type=float, default=0.0, help="请求间延迟时间(秒)")
    parser.add_argument("--rate-limit", type=int, help="每秒请求速率限制")
    
    # 载荷参数
    parser.add_argument("-f", "--payload-file", help="载荷文件，每行一个值")
    parser.add_argument("--placeholder", default="PAYLOAD_PLACEHOLDER", help="载荷占位符文本")
    
    # IP伪装参数
    parser.add_argument("--proxy", help="代理服务器，格式为http(s)://host:port或socks5://host:port")
    parser.add_argument("--proxy-file", help="代理服务器列表文件，每行一个代理")
    parser.add_argument("--proxy-type", default="http", choices=["http", "https", "socks4", "socks5"], 
                        help="代理服务器类型")
    parser.add_argument("--rotate-user-agents", action="store_true", help="随机轮换User-Agent")
    parser.add_argument("--user-agents-file", help="User-Agent列表文件，每行一个UA")
    parser.add_argument("--spoof-ip", help="伪造源IP地址，将添加到X-Forwarded-For头")
    
    # 输出参数
    parser.add_argument("-o", "--output", help="结果保存文件")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细输出")
    
    return parser.parse_args()

def display_banner():
    """显示工具横幅"""
    banner = f"""
{Fore.CYAN}╔═══════════════════════════════════════════════════╗
{Fore.CYAN}║ {Fore.RED}高性能异步爆破工具 {Fore.GREEN}v2.0{Fore.CYAN}                        ║
{Fore.CYAN}║ {Fore.YELLOW}基于异步协程实现的高并发请求工具{Fore.CYAN}                 ║
{Fore.CYAN}╚═══════════════════════════════════════════════════╝{Style.RESET_ALL}
    """
    print(banner)

async def load_proxies(args) -> List[str]:
    """加载代理服务器列表"""
    proxies = []
    
    # 从命令行参数加载单个代理
    if args.proxy:
        proxy = args.proxy
        if not proxy.startswith(('http://', 'https://', 'socks4://', 'socks5://')):
            proxy = f"{args.proxy_type}://{proxy}"
        proxies.append(proxy)
    
    # 从文件加载代理列表
    if args.proxy_file:
        file_proxies = await AsyncRequestHandler.load_proxy_file(args.proxy_file)
        proxies.extend(file_proxies)
        print(f"{Fore.GREEN}[信息] 已从文件加载 {len(file_proxies)} 个代理服务器{Style.RESET_ALL}")
    
    return proxies

async def load_user_agents(args) -> List[str]:
    """加载自定义User-Agent列表"""
    user_agents = []
    
    if args.user_agents_file and os.path.exists(args.user_agents_file):
        try:
            with open(args.user_agents_file, 'r') as f:
                user_agents = [line.strip() for line in f if line.strip()]
            print(f"{Fore.GREEN}[信息] 已从文件加载 {len(user_agents)} 个User-Agent{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[错误] 加载User-Agent文件失败: {str(e)}{Style.RESET_ALL}")
    
    return user_agents

async def prepare_request_data(args, placeholder: str, payload: Optional[str]) -> Dict[str, Any]:
    """准备请求数据，替换占位符"""
    if not payload:
        return {
            "url": args.url,
            "headers": parse_key_value_string(args.headers) if args.headers else {},
            "params": parse_key_value_string(args.params) if args.params else {},
            "data": args.data
        }
    
    # 替换URL中的占位符
    url = args.url.replace(placeholder, payload) if placeholder in args.url else args.url
    
    # 替换请求头中的占位符
    headers = {}
    if args.headers:
        for key, value in parse_key_value_string(args.headers).items():
            headers[key] = value.replace(placeholder, payload) if placeholder in value else value
    
    # 替换参数中的占位符
    params = {}
    if args.params:
        for key, value in parse_key_value_string(args.params).items():
            params[key] = value.replace(placeholder, payload) if placeholder in value else value
    
    # 替换数据中的占位符
    data = None
    if args.data:
        data = args.data.replace(placeholder, payload) if placeholder in args.data else args.data
    
    return {
        "url": url,
        "headers": headers,
        "params": params,
        "data": data
    }

async def process_batch(
    handler: AsyncRequestHandler,
    payloads: List[str],
    batch_size: int,
    placeholder: str,
    progress_bar: tqdm
) -> List[Dict[str, Any]]:
    """处理一批请求"""
    results = []
    
    # 处理每个载荷
    batch_tasks = []
    for payload in payloads:
        task = handler.send_request(payload=payload)
        batch_tasks.append(task)
    
    # 等待所有任务完成
    for future in asyncio.as_completed(batch_tasks):
        try:
            result = await future
            results.append(result)
            progress_bar.update(1)
        except Exception as e:
            results.append({
                "success": False,
                "error": f"请求执行异常: {str(e)}"
            })
            progress_bar.update(1)
    
    return results

async def main_async():
    """异步主函数"""
    display_banner()
    
    # 解析命令行参数
    args = parse_arguments()
    
    # 验证URL格式
    if not is_valid_url(args.url):
        print(f"{Fore.RED}[错误] 无效的URL格式: {args.url}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[提示] URL必须以http://或https://开头，例如: https://example.com{Style.RESET_ALL}")
        return 1
    
    # 加载代理服务器
    proxies = await load_proxies(args)
    
    # 初始化请求处理器
    handler = AsyncRequestHandler(
        url=args.url,
        method=args.method,
        timeout=args.timeout,
        max_connections=args.concurrency,
        proxy_pool=proxies,
        proxy_type=args.proxy_type,
        rotate_user_agents=args.rotate_user_agents
    )
    
    # 设置IP伪装
    if args.spoof_ip:
        headers = handler.headers.copy()
        headers["X-Forwarded-For"] = args.spoof_ip
        handler.set_headers(headers)
    
    # 设置请求头
    if args.headers:
        headers = parse_key_value_string(args.headers)
        handler.set_headers(headers)
    
    # 设置请求参数
    if args.params:
        params = parse_key_value_string(args.params)
        handler.set_params(params)
    
    # 设置请求数据
    if args.data:
        handler.set_data(args.data)
    
    # 加载载荷文件
    payloads = []
    if args.payload_file:
        payloads = load_payload_file(args.payload_file)
        if not payloads:
            print(f"{Fore.RED}[错误] 载荷文件为空或无法读取{Style.RESET_ALL}")
            return 1
        
        # 检查是否使用了载荷占位符
        placeholder_found = False
        if args.url and args.placeholder in args.url:
            placeholder_found = True
        if args.params and args.placeholder in args.params:
            placeholder_found = True
        if args.data and args.placeholder in args.data:
            placeholder_found = True
        if args.headers and args.placeholder in args.headers:
            placeholder_found = True
        
        if not placeholder_found:
            print(f"{Fore.YELLOW}[警告] 未在请求中找到占位符 '{args.placeholder}'{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[警告] 载荷将被添加到默认位置，可能导致预期外的结果{Style.RESET_ALL}")
    
    # 确定请求总数
    num_requests = len(payloads) if payloads else args.num_requests
    
    print(f"{Fore.GREEN}[信息] 开始异步爆破测试，目标URL: {args.url}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}[信息] 请求方法: {args.method}, 请求次数: {num_requests}, 并发连接: {args.concurrency}{Style.RESET_ALL}")
    
    if proxies:
        print(f"{Fore.GREEN}[信息] 使用代理服务器: {len(proxies)} 个{Style.RESET_ALL}")
    
    if args.rotate_user_agents:
        print(f"{Fore.GREEN}[信息] 已启用User-Agent轮换{Style.RESET_ALL}")
    
    if args.spoof_ip:
        print(f"{Fore.GREEN}[信息] 已设置IP伪装: {args.spoof_ip}{Style.RESET_ALL}")
    
    # 记录开始时间
    start_time = time.time()
    
    # 创建异步进度条
    progress_bar = tqdm(
        total=num_requests,
        desc="爆破进度",
        unit="请求",
        ascii=True,  # 使用ASCII字符，兼容不同终端
        ncols=100
    )
    
    # 执行请求
    results = {
        "success": 0,
        "failed": 0,
        "total": num_requests,
        "responses": []
    }
    
    try:
        if payloads:
            # 使用批处理方式发送请求
            batch_size = min(1000, args.concurrency)  # 避免创建过多任务
            for i in range(0, len(payloads), batch_size):
                batch_payloads = payloads[i:i+batch_size]
                batch_results = await process_batch(
                    handler,
                    batch_payloads,
                    batch_size,
                    args.placeholder,
                    progress_bar
                )
                
                # 更新统计信息
                for result in batch_results:
                    if result.get("success", False):
                        results["success"] += 1
                    else:
                        results["failed"] += 1
                    results["responses"].append(result)
                
                # 批次间延迟
                if args.delay > 0:
                    await asyncio.sleep(args.delay)
        else:
            # 不使用载荷，直接发送请求
            batch_result = await handler.send_requests_batch(
                count=num_requests,
                concurrency=args.concurrency
            )
            
            # 更新统计信息
            results["success"] = batch_result["success"]
            results["failed"] = batch_result["failed"]
            results["responses"] = batch_result["responses"]
            
            # 更新进度条
            progress_bar.update(num_requests)
    
    except Exception as e:
        print(f"\n{Fore.RED}[错误] 执行过程出错: {str(e)}{Style.RESET_ALL}")
    finally:
        # 关闭进度条
        progress_bar.close()
    
    # 计算用时
    elapsed_time = time.time() - start_time
    
    # 显示结果统计
    print(f"\n{Fore.CYAN}[结果统计]{Style.RESET_ALL}")
    print(f"总请求次数: {results['total']}")
    print(f"成功请求数: {Fore.GREEN}{results['success']}{Style.RESET_ALL}")
    print(f"失败请求数: {Fore.RED}{results['failed']}{Style.RESET_ALL}")
    print(f"总用时: {elapsed_time:.2f}秒")
    print(f"平均请求速度: {results['total'] / elapsed_time:.2f}请求/秒")
    
    # 保存结果
    if args.output:
        save_results(results, args.output)
        print(f"{Fore.GREEN}[信息] 结果已保存到 {args.output}{Style.RESET_ALL}")
    
    return 0

def main():
    """主函数入口点"""
    try:
        return asyncio.run(main_async())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[警告] 用户中断，程序已停止{Style.RESET_ALL}")
        return 0
    except Exception as e:
        print(f"\n{Fore.RED}[错误] 程序执行出错: {str(e)}{Style.RESET_ALL}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 