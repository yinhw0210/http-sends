#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HTTP模拟请求与IP伪装工具 - 性能基准测试模块
比较标准模式(多线程)和异步模式(协程)在不同场景下的性能差异
"""

import os
import sys
import time
import argparse
import subprocess
import json
from colorama import init, Fore, Style
from tabulate import tabulate

# 初始化colorama
init(autoreset=True)

def print_banner():
    """打印工具横幅"""
    banner = f"""
{Fore.CYAN}╔═══════════════════════════════════════════════════╗
{Fore.CYAN}║ {Fore.RED}性能基准测试 {Fore.GREEN}v1.0{Fore.CYAN}                            ║
{Fore.CYAN}║ {Fore.YELLOW}用于比较标准模式和异步模式的性能差异{Fore.CYAN}             ║
{Fore.CYAN}╚═══════════════════════════════════════════════════╝{Style.RESET_ALL}
    """
    print(banner)

def run_benchmark(url, method="GET", requests=1000, concurrency=100, payload_file=None, data=None):
    """
    运行基准测试，比较标准模式和异步模式的性能
    
    Args:
        url: 目标URL
        method: HTTP方法
        requests: 请求次数
        concurrency: 并发数
        payload_file: 载荷文件路径
        data: 请求数据
    
    Returns:
        dict: 包含测试结果的字典
    """
    results = {
        "url": url,
        "method": method,
        "requests": requests,
        "concurrency": concurrency,
        "standard_mode": {},
        "async_mode": {}
    }
    
    # 基本命令行参数
    base_args = [
        "-u", url,
        "-m", method,
        "-n", str(requests),
        "-o", "benchmark_results.json"
    ]
    
    # 添加载荷文件参数
    if payload_file:
        base_args.extend(["-f", payload_file])
    
    # 添加数据参数
    if data:
        base_args.extend(["-d", data])
    
    # 运行标准模式测试
    print(f"{Fore.YELLOW}[基准测试] 正在运行标准模式测试...{Style.RESET_ALL}")
    standard_cmd = [sys.executable, "main.py"] + base_args + ["-t", str(min(concurrency, 50))]
    
    standard_start = time.time()
    subprocess.call(standard_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    standard_time = time.time() - standard_start
    
    # 加载结果
    if os.path.exists("benchmark_results.json"):
        with open("benchmark_results.json", "r") as f:
            standard_results = json.load(f)
            results["standard_mode"] = {
                "time": standard_time,
                "success": standard_results.get("successful_requests", 0),
                "failed": standard_results.get("failed_requests", 0),
                "requests_per_second": requests / standard_time
            }
    
    # 运行异步模式测试
    print(f"{Fore.YELLOW}[基准测试] 正在运行异步模式测试...{Style.RESET_ALL}")
    async_cmd = [sys.executable, "async_main.py"] + base_args + ["-c", str(concurrency)]
    
    async_start = time.time()
    subprocess.call(async_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    async_time = time.time() - async_start
    
    # 加载结果
    if os.path.exists("benchmark_results.json"):
        with open("benchmark_results.json", "r") as f:
            async_results = json.load(f)
            results["async_mode"] = {
                "time": async_time,
                "success": async_results.get("successful_requests", 0),
                "failed": async_results.get("failed_requests", 0),
                "requests_per_second": requests / async_time
            }
    
    # 计算性能提升
    if results["standard_mode"] and results["async_mode"]:
        standard_time = results["standard_mode"]["time"]
        async_time = results["async_mode"]["time"]
        results["speedup"] = standard_time / async_time if async_time > 0 else 0
    
    # 删除临时结果文件
    if os.path.exists("benchmark_results.json"):
        os.remove("benchmark_results.json")
    
    return results

def run_comprehensive_benchmark(url, requests=1000):
    """运行全面的基准测试，测试不同场景"""
    scenarios = [
        {
            "name": "简单GET请求",
            "method": "GET", 
            "requests": requests,
            "concurrency": 100,
            "data": None
        },
        {
            "name": "POST表单请求",
            "method": "POST", 
            "requests": requests,
            "concurrency": 100,
            "data": "username=test&password=test123"
        },
        {
            "name": "POST JSON请求",
            "method": "POST", 
            "requests": requests,
            "concurrency": 100,
            "data": '{"username":"test", "password":"test123"}'
        },
        {
            "name": "高并发GET请求",
            "method": "GET", 
            "requests": requests,
            "concurrency": 500,
            "data": None
        }
    ]
    
    all_results = []
    
    for scenario in scenarios:
        print(f"\n{Fore.CYAN}[基准测试] 运行场景: {scenario['name']}{Style.RESET_ALL}")
        result = run_benchmark(
            url=url,
            method=scenario["method"],
            requests=scenario["requests"],
            concurrency=scenario["concurrency"],
            data=scenario["data"]
        )
        result["name"] = scenario["name"]
        all_results.append(result)
    
    return all_results

def format_time(seconds):
    """格式化时间为易读格式"""
    if seconds < 0.001:
        return f"{seconds * 1000000:.2f}μs"
    elif seconds < 1:
        return f"{seconds * 1000:.2f}ms"
    else:
        return f"{seconds:.2f}s"

def display_results(results):
    """格式化显示结果"""
    if not results:
        print(f"{Fore.RED}[错误] 没有可用的测试结果{Style.RESET_ALL}")
        return
    
    # 结果表格数据
    table_data = []
    
    for result in results:
        # 准备行数据
        standard_time = result.get("standard_mode", {}).get("time", 0)
        async_time = result.get("async_mode", {}).get("time", 0)
        speedup = result.get("speedup", 0)
        
        standard_rps = result.get("standard_mode", {}).get("requests_per_second", 0)
        async_rps = result.get("async_mode", {}).get("requests_per_second", 0)
        
        row = [
            result.get("name", "未知场景"),
            result.get("method", "GET"),
            result.get("requests", 0),
            result.get("concurrency", 0),
            f"{standard_time:.2f}秒",
            f"{async_time:.2f}秒",
            f"{speedup:.1f}倍",
            f"{standard_rps:.1f}",
            f"{async_rps:.1f}"
        ]
        
        table_data.append(row)
    
    # 使用tabulate格式化表格
    headers = ["场景", "方法", "请求数", "并发数", "标准模式时间", "异步模式时间", "性能提升", "标准RPS", "异步RPS"]
    table = tabulate(table_data, headers=headers, tablefmt="grid")
    
    print("\n性能基准测试结果：")
    print(table)
    
    # 输出性能结论
    avg_speedup = sum(result.get("speedup", 0) for result in results) / len(results)
    print(f"\n{Fore.GREEN}[结论] 异步模式平均性能提升: {avg_speedup:.1f}倍{Style.RESET_ALL}")
    
    if avg_speedup >= 5:
        print(f"{Fore.GREEN}[建议] 对于高并发场景，强烈推荐使用异步模式{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}[建议] 对于小规模测试，两种模式差异不大，可根据需求选择{Style.RESET_ALL}")
    
    # 输出系统配置建议
    max_concurrency = max(result.get("concurrency", 0) for result in results)
    if max_concurrency > 1000:
        print(f"{Fore.YELLOW}[警告] 高并发测试({max_concurrency})可能需要调整系统配置以达到最佳性能{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[建议] 可能需要增加系统的文件描述符限制(ulimit -n)和调整网络参数{Style.RESET_ALL}")

def main():
    """主函数"""
    print_banner()
    
    parser = argparse.ArgumentParser(description="性能基准测试工具")
    parser.add_argument("-u", "--url", required=True, help="目标URL地址")
    parser.add_argument("-n", "--num-requests", type=int, default=1000, help="每个场景的请求数")
    parser.add_argument("-q", "--quick", action="store_true", help="快速测试模式(仅测试单个场景)")
    parser.add_argument("-o", "--output", help="将结果保存到文件")
    
    args = parser.parse_args()
    
    try:
        if args.quick:
            # 快速测试模式，只测试GET请求
            print(f"{Fore.YELLOW}[基准测试] 运行快速测试模式: GET请求{Style.RESET_ALL}")
            results = [run_benchmark(args.url, requests=args.num_requests)]
            results[0]["name"] = "快速测试 - GET请求"
        else:
            # 全面测试模式，测试多种场景
            results = run_comprehensive_benchmark(args.url, requests=args.num_requests)
        
        # 显示结果
        display_results(results)
        
        # 保存结果到文件
        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)
            print(f"\n{Fore.GREEN}[信息] 测试结果已保存到 {args.output}{Style.RESET_ALL}")
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[警告] 用户中断，基准测试已停止{Style.RESET_ALL}")
        return 1
    except Exception as e:
        print(f"\n{Fore.RED}[错误] 基准测试失败: {str(e)}{Style.RESET_ALL}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 