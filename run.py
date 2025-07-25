#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import argparse
import subprocess

def print_banner():
    """打印工具横幅"""
    banner = """
╔═══════════════════════════════════════════════════╗
║          HTTP模拟请求与IP伪装工具 v2.0            ║
║        模拟HTTP请求并提供高级IP伪装能力           ║
╚═══════════════════════════════════════════════════╝
    """
    print(banner)

def check_dependencies():
    """检查依赖项是否已安装"""
    try:
        import requests
        import colorama
        import tqdm
        import flask
        import aiohttp
        import aiofiles
        return True
    except ImportError as e:
        print(f"缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def start_web_ui():
    """启动Web界面模式"""
    print("正在启动Web界面模式...")
    try:
        import web_ui
        web_ui.app.run(debug=False)
    except Exception as e:
        print(f"启动Web界面失败: {str(e)}")
        sys.exit(1)

def start_cli_mode(args, use_async=False):
    """
    启动命令行模式
    
    Args:
        args: 命令行参数
        use_async: 是否使用异步模式
    """
    print(f"正在启动{'异步' if use_async else '标准'}命令行模式...")
    # 构建命令行参数
    cmd_args = [sys.executable, "async_main.py" if use_async else "main.py"]
    
    # 添加所有传递的参数
    cmd_args.extend(args)
    
    try:
        # 执行main.py或async_main.py并传递所有参数
        subprocess.call(cmd_args)
    except Exception as e:
        print(f"执行失败: {str(e)}")
        sys.exit(1)

def start_benchmark_mode(args):
    """启动基准测试模式"""
    print("正在启动基准测试模式...")
    # 构建命令行参数
    cmd_args = [sys.executable, "benchmark.py"]
    
    # 添加所有传递的参数
    cmd_args.extend(args)
    
    try:
        # 执行benchmark.py并传递所有参数
        subprocess.call(cmd_args)
    except Exception as e:
        print(f"执行基准测试失败: {str(e)}")
        sys.exit(1)

def main():
    """主函数"""
    print_banner()
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="精准爆破工具运行脚本")
    parser.add_argument("--web", action="store_true", help="启动Web界面模式")
    parser.add_argument("--async", dest="use_async", action="store_true", help="使用异步高性能模式")
    parser.add_argument("--compare", action="store_true", help="对比测试模式（同时使用标准和异步模式）")
    parser.add_argument("--benchmark", action="store_true", help="运行全面的性能基准测试")
    
    # 分离我们的参数和传递给main.py的参数
    if any(arg in sys.argv for arg in ["--web", "--async", "--compare", "--benchmark"]):
        args, main_args = parser.parse_known_args()
    else:
        # 所有参数都传递给main.py
        args = parser.parse_args([])
        main_args = sys.argv[1:]
    
    # 根据参数启动相应模式
    if args.web:
        start_web_ui()
    elif args.benchmark:
        start_benchmark_mode(main_args)
    elif args.compare:
        print("对比测试模式：将依次使用标准模式和异步模式执行相同的请求")
        print("\n=== 标准模式测试 ===")
        start_cli_mode(main_args, use_async=False)
        print("\n=== 异步模式测试 ===")
        start_cli_mode(main_args, use_async=True)
    else:
        if not main_args:
            # 如果没有参数，打印使用帮助
            print("用法:")
            print("  1. Web界面模式:  python run.py --web")
            print("  2. 标准命令行模式:  python run.py [main.py的参数]")
            print("  3. 异步高性能模式:  python run.py --async [async_main.py的参数]")
            print("  4. 对比测试模式:  python run.py --compare [公共参数]")
            print("  5. 基准测试模式:  python run.py --benchmark [benchmark.py的参数]")
            print("\n例如:")
            print("  python run.py -u https://example.com -m GET -n 10")
            print("  python run.py --async -u https://example.com -m POST -d '{\"username\":\"admin\",\"password\":\"PAYLOAD_PLACEHOLDER\"}' -f sample_payloads.txt -c 200")
            print("  python run.py --async -u https://example.com --proxy-file sample_proxies.txt --rotate-user-agents")
            print("  python run.py --benchmark -u https://example.com -n 100 -q")
            print("\n要查看完整的命令行参数，请运行: python run.py --help")
        else:
            start_cli_mode(main_args, use_async=args.use_async)

if __name__ == "__main__":
    main() 