#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from colorama import init, Fore, Style
from tqdm import tqdm

from request_handler import RequestHandler
from utils import load_payload_file, save_results, parse_key_value_string, is_valid_url, check_payload_placeholder

# 初始化colorama
init(autoreset=True)

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="精准爆破工具 - 对特定URL进行参数爆破测试",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument("-u", "--url", required=True, help="目标URL地址")
    parser.add_argument("-m", "--method", default="GET", choices=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"], 
                        help="HTTP请求方法")
    parser.add_argument("-p", "--params", help="请求参数，格式为key=value,key2=value2")
    parser.add_argument("-d", "--data", help="POST请求数据，JSON格式字符串或表单数据")
    parser.add_argument("-H", "--headers", help="请求头，格式为key=value,key2=value2")
    parser.add_argument("-t", "--threads", type=int, default=10, help="并发线程数")
    parser.add_argument("-n", "--num-requests", type=int, default=100, help="请求次数")
    parser.add_argument("-f", "--payload-file", help="载荷文件，每行一个值")
    parser.add_argument("-o", "--output", help="结果保存文件")
    parser.add_argument("-T", "--timeout", type=float, default=10.0, help="请求超时时间(秒)")
    parser.add_argument("--delay", type=float, default=0.0, help="请求间延迟时间(秒)")
    parser.add_argument("--placeholder", default="PAYLOAD_PLACEHOLDER", help="载荷占位符文本")
    
    return parser.parse_args()

def display_banner():
    """显示工具横幅"""
    banner = f"""
{Fore.CYAN}╔═══════════════════════════════════════════════════╗
{Fore.CYAN}║ {Fore.RED}精准爆破工具 {Fore.GREEN}v1.0{Fore.CYAN}                              ║
{Fore.CYAN}║ {Fore.YELLOW}用于对特定URL进行参数爆破测试{Fore.CYAN}                   ║
{Fore.CYAN}╚═══════════════════════════════════════════════════╝{Style.RESET_ALL}
    """
    print(banner)

def main():
    """主函数"""
    display_banner()
    
    # 解析命令行参数
    args = parse_arguments()
    
    # 验证URL格式
    if not is_valid_url(args.url):
        print(f"{Fore.RED}[错误] 无效的URL格式: {args.url}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[提示] URL必须以http://或https://开头，例如: https://example.com{Style.RESET_ALL}")
        sys.exit(1)
    
    # 初始化请求处理器
    handler = RequestHandler(
        url=args.url,
        method=args.method,
        timeout=args.timeout
    )
    
    # 解析请求头
    if args.headers:
        headers = parse_key_value_string(args.headers)
        handler.set_headers(headers)
    
    # 解析请求参数
    if args.params:
        params = parse_key_value_string(args.params)
        handler.set_params(params)
    
    # 解析请求数据
    if args.data:
        handler.set_data(args.data)
    
    # 载荷文件
    payloads = []
    if args.payload_file:
        payloads = load_payload_file(args.payload_file)
        if not payloads:
            print(f"{Fore.RED}[错误] 载荷文件为空或无法读取{Style.RESET_ALL}")
            sys.exit(1)
        
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
    
    # 如果有载荷文件，请求次数为载荷数量，否则为用户指定次数
    num_requests = len(payloads) if payloads else args.num_requests
    
    # 记录开始时间
    start_time = time.time()
    
    # 统计结果
    results = {
        "success": 0,
        "failed": 0,
        "total": num_requests,
        "responses": []
    }
    
    print(f"{Fore.GREEN}[信息] 开始爆破测试，目标URL: {args.url}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}[信息] 请求方法: {args.method}, 请求次数: {num_requests}, 并发线程: {args.threads}{Style.RESET_ALL}")
    
    # 创建进度条
    progress_bar = tqdm(total=num_requests, desc="爆破进度", unit="请求")
    
    # 定义请求任务
    def request_task(i):
        # 如果有载荷文件，使用载荷，否则就是普通请求
        if payloads:
            payload = payloads[i]
            
            # 处理请求中的占位符
            temp_url = args.url.replace(args.placeholder, payload) if args.url and args.placeholder in args.url else args.url
            temp_handler = RequestHandler(url=temp_url, method=args.method, timeout=args.timeout)
            
            # 处理请求头中的占位符
            if args.headers:
                temp_headers = {}
                for key, value in parse_key_value_string(args.headers).items():
                    temp_headers[key] = value.replace(args.placeholder, payload) if args.placeholder in value else value
                temp_handler.set_headers(temp_headers)
            
            # 处理参数中的占位符
            if args.params:
                temp_params = {}
                for key, value in parse_key_value_string(args.params).items():
                    temp_params[key] = value.replace(args.placeholder, payload) if args.placeholder in value else value
                temp_handler.set_params(temp_params)
            
            # 处理数据中的占位符
            if args.data:
                temp_data = args.data.replace(args.placeholder, payload) if args.placeholder in args.data else args.data
                temp_handler.set_data(temp_data)
            
            # 发送请求
            response = temp_handler.send_request()
            # 添加载荷信息到响应
            response["payload"] = payload
        else:
            response = handler.send_request()
        
        # 添加延迟
        if args.delay > 0:
            time.sleep(args.delay)
        
        # 更新进度条
        progress_bar.update(1)
        
        # 更新结果统计
        if response.get("success", False):
            results["success"] += 1
        else:
            results["failed"] += 1
        
        results["responses"].append(response)
        
        return response
    
    # 使用线程池执行请求
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = [executor.submit(request_task, i) for i in range(num_requests)]
        
        # 等待所有请求完成
        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"\n{Fore.RED}[错误] 请求执行出错: {str(e)}{Style.RESET_ALL}")
                results["failed"] += 1
    
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

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[警告] 用户中断，程序已停止{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}[错误] 程序执行出错: {str(e)}{Style.RESET_ALL}")
        sys.exit(1) 