#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import threading
import webbrowser
import asyncio
import random
import time
import ipaddress
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, SelectField, IntegerField, FloatField, FileField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, URL, Optional, NumberRange

# 导入主程序和工具模块
from request_handler import RequestHandler
from async_request_handler import AsyncRequestHandler
from utils import load_payload_file, save_results

# 初始化Flask应用
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = os.urandom(24)
csrf = CSRFProtect(app)

# 确保目录存在
os.makedirs('static', exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('uploads', exist_ok=True)
os.makedirs('results', exist_ok=True)

# 定义表单类
class RequestTestForm(FlaskForm):
    # 基本参数
    url = StringField('目标URL', validators=[DataRequired(), URL()])
    method = SelectField('请求方式', 
                       choices=[('GET', 'GET'), ('POST', 'POST'), ('PUT', 'PUT'), 
                                ('DELETE', 'DELETE'), ('HEAD', 'HEAD'), ('OPTIONS', 'OPTIONS'),
                                ('PATCH', 'PATCH')],
                       default='GET')
    headers = TextAreaField('请求头 (每行一个 key=value)')
    params = TextAreaField('URL参数 (每行一个 key=value)')
    data = TextAreaField('请求数据 (JSON或表单数据)')
    payload_file = FileField('测试数据文件 (每行一个值)')
    payload_placeholder = StringField('数据占位符', default='PAYLOAD_PLACEHOLDER')
    
    # 网络设置参数
    use_proxy = BooleanField('启用代理服务器')
    proxy_mode = StringField('代理模式')
    proxy = StringField('代理服务器地址')
    proxy_type = SelectField('代理类型', choices=[
        ('http', 'HTTP'), ('https', 'HTTPS'), ('socks4', 'SOCKS4'), ('socks5', 'SOCKS5')
    ], default='http')
    proxy_file_input = FileField('代理服务器列表文件')
    
    # User-Agent参数
    rotate_user_agents = BooleanField('随机轮换User-Agent')
    ua_mode = StringField('User-Agent模式')
    user_agents_file = FileField('User-Agent列表文件')
    
    # IP地址设置
    spoof_ip = BooleanField('自定义源IP地址')
    spoof_ip_address = StringField('自定义IP地址')
    random_ip = BooleanField('随机生成IP')
    
    # 性能优化参数
    use_async_mode = BooleanField('使用异步高性能模式')
    concurrency = IntegerField('并发连接数', validators=[NumberRange(min=1, max=5000)], default=100)
    threads = IntegerField('并发线程数', validators=[NumberRange(min=1, max=100)], default=10)
    num_requests = IntegerField('请求次数', validators=[NumberRange(min=1)], default=100)
    timeout = FloatField('超时时间(秒)', validators=[NumberRange(min=0.1)], default=10.0)
    delay = FloatField('请求延迟(秒)', validators=[NumberRange(min=0.0)], default=0.0)
    rate_limit = IntegerField('速率限制', validators=[NumberRange(min=0)], default=0)
    verbose = BooleanField('详细输出模式')

# 全局变量，存储当前任务状态
task_status = {
    'is_running': False,
    'total': 0,
    'completed': 0,
    'success': 0,
    'failed': 0,
    'progress': 0,
    'results': []
}

# 创建一个任务锁，防止并发问题
task_lock = threading.Lock()

# 初始化函数，重置任务状态
def reset_task_status():
    global task_status
    with task_lock:
        task_status.update({
            'is_running': False,
            'total': 0,
            'completed': 0,
            'success': 0,
            'failed': 0,
            'progress': 0,
            'results': []
        })

@app.route('/')
def index():
    # 当用户访问首页时，确保任务状态是正确的
    if not task_status.get('is_running', False):
        reset_task_status()
    form = RequestTestForm()
    return render_template('index.html', form=form, task_status=task_status)

@app.route('/start_test', methods=['POST'])
def start_test():
    try:
        # 打印请求数据，帮助调试
        app.logger.info(f"收到的表单数据: {request.form}")
        
        # 使用锁来检查和更新任务状态，避免竞态条件
        with task_lock:
            # 如果已有任务在运行，则拒绝请求
            if task_status['is_running']:
                return jsonify({'success': False, 'message': '已有任务正在运行，请等待完成或停止当前任务'})
            
            # 重置任务状态
            task_status.update({
                'is_running': True,
                'total': 0,
                'completed': 0,
                'success': 0,
                'failed': 0,
                'progress': 0,
                'results': []
            })
        
        # 获取表单数据
        config = {}
        
        # 基本参数 - 直接从request.form获取
        config['url'] = request.form.get('url')
        if not config['url']:
            raise ValueError("URL是必需的参数")
            
        config['method'] = request.form.get('method', 'GET')
        config['timeout'] = float(request.form.get('timeout', 10.0))
        config['delay'] = float(request.form.get('delay', 0.0))
        
        # 异步模式
        config['use_async_mode'] = request.form.get('use_async_mode') == 'on'
        
        # 并发控制参数
        try:
            config['threads'] = int(request.form.get('threads', 10))
        except (TypeError, ValueError):
            config['threads'] = 10
            
        try:
            config['concurrency'] = int(request.form.get('concurrency', 100))
        except (TypeError, ValueError):
            config['concurrency'] = 100
            
        try:
            rate_limit = request.form.get('rate_limit', '0')
            config['rate_limit'] = int(rate_limit) if rate_limit and int(rate_limit) > 0 else None
        except (TypeError, ValueError):
            config['rate_limit'] = None
            
        # 请求次数
        try:
            config['num_requests'] = int(request.form.get('num_requests', 100))
        except (TypeError, ValueError):
            config['num_requests'] = 100
        
        # IP伪装配置
        config['use_proxy'] = request.form.get('use_proxy') == 'on'
        config['proxy_mode'] = request.form.get('proxy_mode', 'single')
        config['proxy'] = request.form.get('proxy', '')
        config['proxy_type'] = request.form.get('proxy_type', 'http')
        config['rotate_user_agents'] = request.form.get('rotate_user_agents') == 'on'
        config['ua_mode'] = request.form.get('ua_mode', 'built_in')
        config['spoof_ip'] = request.form.get('spoof_ip') == 'on'
        config['spoof_ip_address'] = request.form.get('spoof_ip_address', '')
        config['random_ip'] = request.form.get('random_ip') == 'on'
        config['verbose'] = request.form.get('verbose') == 'on'
        
        # 占位符设置
        config['placeholder'] = request.form.get('payload_placeholder', 'PAYLOAD_PLACEHOLDER')
        
        app.logger.info(f"处理后的配置: {config}")
        
        # 处理请求头
        headers = {}
        headers_text = request.form.get('headers', '')
        if headers_text:
            for line in headers_text.split('\n'):
                line = line.strip()
                if line and '=' in line:
                    key, value = line.split('=', 1)
                    headers[key.strip()] = value.strip()
        
        # 处理URL参数
        params = {}
        params_text = request.form.get('params', '')
        if params_text:
            for line in params_text.split('\n'):
                line = line.strip()
                if line and '=' in line:
                    key, value = line.split('=', 1)
                    params[key.strip()] = value.strip()
        
        # 处理请求数据
        data = request.form.get('data', '')
        if not data:
            data = None
        
        # 处理载荷文件
        payloads = []
        payload_file = request.files.get('payload_file')
        if payload_file and payload_file.filename:
            file_path = os.path.join('uploads', payload_file.filename)
            payload_file.save(file_path)
            payloads = load_payload_file(file_path)
            app.logger.info(f"已加载 {len(payloads)} 个载荷项")
        
        # 处理代理文件
        proxy_list = []
        if config['use_proxy'] and config['proxy_mode'] == 'file':
            proxy_file = request.files.get('proxy_file_input')
            if proxy_file and proxy_file.filename:
                file_path = os.path.join('uploads', proxy_file.filename)
                proxy_file.save(file_path)
                
                # 从文件读取代理列表
                try:
                    with open(file_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                # 处理代理格式
                                if not line.startswith(('http://', 'https://', 'socks4://', 'socks5://')):
                                    line = f"{config['proxy_type']}://{line}"
                                proxy_list.append(line)
                    app.logger.info(f"已加载 {len(proxy_list)} 个代理")
                except Exception as e:
                    app.logger.error(f"读取代理文件错误: {str(e)}")
        
        # 处理User-Agent文件
        user_agents = []
        if config['rotate_user_agents'] and config['ua_mode'] == 'file':
            ua_file = request.files.get('user_agents_file')
            if ua_file and ua_file.filename:
                file_path = os.path.join('uploads', ua_file.filename)
                ua_file.save(file_path)
                
                # 从文件读取User-Agent列表
                try:
                    with open(file_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                user_agents.append(line)
                    app.logger.info(f"已加载 {len(user_agents)} 个User-Agent")
                except Exception as e:
                    app.logger.error(f"读取User-Agent文件错误: {str(e)}")
        
        # 处理IP地址伪装
        if config['spoof_ip']:
            if config['random_ip']:
                config['spoof_ip_address'] = generate_random_ip()
            elif not config['spoof_ip_address']:
                config['spoof_ip_address'] = "192.168.1.1"  # 默认IP
        
        # 配置请求参数
        num_requests = len(payloads) if payloads else config['num_requests']
        
        # 更新任务状态
        with task_lock:
            task_status['total'] = num_requests
        
        app.logger.info(f"准备启动任务: 请求数={num_requests}, 是否异步={config['use_async_mode']}")
        
        # 在新线程中启动测试任务
        try:
            thread = threading.Thread(
                target=run_request_test_task, 
                args=(config, headers, params, data, payloads, num_requests, proxy_list, user_agents)
            )
            thread.daemon = True
            thread.start()
            
            return jsonify({'success': True, 'message': '任务已启动'})
        except Exception as e:
            # 如果启动失败，重置任务状态
            reset_task_status()
            app.logger.error(f"启动任务失败: {str(e)}")
            return jsonify({'success': False, 'message': f'启动任务失败: {str(e)}'})
            
    except Exception as e:
        # 捕获所有异常，确保任务状态被重置
        reset_task_status()
        app.logger.error(f"处理请求时出错: {str(e)}")
        return jsonify({'success': False, 'message': f'处理请求时出错: {str(e)}'})

def generate_random_ip():
    """生成随机IP地址"""
    # 生成常规范围的随机IP
    octets = [random.randint(1, 254) for _ in range(4)]
    return '.'.join(str(octet) for octet in octets)

# 在run_standard_task函数中，修复请求发送逻辑
def run_standard_task(config, headers, params, data, payloads, num_requests, proxy_list, user_agents):
    """标准模式执行HTTP请求测试任务"""
    try:
        app.logger.info(f"启动标准任务: 请求数={num_requests}")
        
        # 初始化请求处理器
        handler = RequestHandler(url=config['url'], method=config['method'], timeout=config['timeout'])
        
        # 设置请求头
        if headers:
            # 处理IP伪装
            if config['spoof_ip'] and config['spoof_ip_address']:
                headers['X-Forwarded-For'] = config['spoof_ip_address']
                headers['X-Real-IP'] = config['spoof_ip_address']
                headers['Client-IP'] = config['spoof_ip_address']
                
            handler.set_headers(headers)
        elif config['spoof_ip'] and config['spoof_ip_address']:
            # 只设置IP伪装头
            handler.set_headers({
                'X-Forwarded-For': config['spoof_ip_address'],
                'X-Real-IP': config['spoof_ip_address'],
                'Client-IP': config['spoof_ip_address']
            })
        
        # 设置请求参数
        if params:
            handler.set_params(params)
        
        # 设置请求数据
        if data:
            handler.set_data(data)
        
        app.logger.info(f"配置完成，开始执行请求: 总数={num_requests}, payload数量={len(payloads) if payloads else 0}")
        
        completed_count = 0
        
        # 执行请求
        for i in range(num_requests):
            # 首先检查任务是否应该继续
            with task_lock:
                if not task_status['is_running']:
                    app.logger.info("任务已被停止，中断执行")
                    break
                
            try:
                # 处理User-Agent轮换
                if config['rotate_user_agents']:
                    if config['ua_mode'] == 'built_in':
                        # 使用内置列表随机选择
                        user_agent = get_random_user_agent()
                    elif user_agents:
                        # 从自定义列表随机选择
                        user_agent = random.choice(user_agents)
                    else:
                        user_agent = None
                    
                    if user_agent:
                        current_headers = handler.headers.copy() if handler.headers else {}
                        current_headers['User-Agent'] = user_agent
                        handler.set_headers(current_headers)
                
                # 处理代理服务器
                if config['use_proxy'] and proxy_list:
                    # 目前标准模式不支持直接的代理功能
                    # 但可以在结果中记录使用了哪个代理，方便调试
                    selected_proxy = random.choice(proxy_list)
                
                # 处理请求 - 根据是否有载荷区分处理
                if payloads and i < len(payloads):
                    payload = payloads[i]
                    app.logger.debug(f"使用载荷: {payload}")
                    
                    # 处理请求中的占位符
                    placeholder = config['placeholder']
                    
                    # 对URL中的占位符进行替换
                    temp_url = config['url'].replace(placeholder, payload) if placeholder in config['url'] else config['url']
                    handler.url = temp_url
                    
                    # 对请求头中的占位符进行替换
                    temp_headers = {}
                    if handler.headers:
                        for key, value in handler.headers.items():
                            if isinstance(value, str):
                                temp_headers[key] = value.replace(placeholder, payload) if placeholder in value else value
                            else:
                                temp_headers[key] = value
                        
                        if temp_headers != handler.headers:
                            handler.set_headers(temp_headers)
                    
                    # 对参数中的占位符进行替换
                    temp_params = {}
                    if handler.params:
                        for key, value in handler.params.items():
                            if isinstance(value, str):
                                temp_params[key] = value.replace(placeholder, payload) if placeholder in value else value
                            else:
                                temp_params[key] = value
                        
                        if temp_params != handler.params:
                            handler.set_params(temp_params)
                    
                    # 对数据中的占位符进行替换
                    if handler.data and isinstance(handler.data, str):
                        temp_data = handler.data.replace(placeholder, payload) if placeholder in handler.data else handler.data
                        if temp_data != handler.data:
                            handler.set_data(temp_data)
                    
                    # 发送请求
                    response = handler.send_request()
                    response['payload'] = payload
                    
                    # 还原原始值
                    handler.url = config['url']
                    if handler.headers and temp_headers != handler.headers:
                        handler.set_headers(headers)
                    if handler.params and temp_params != handler.params:
                        handler.set_params(params)
                    if handler.data and isinstance(handler.data, str) and temp_data != handler.data:
                        handler.set_data(data)
                else:
                    # 普通请求，不需要替换占位符
                    app.logger.debug(f"发送普通请求: {i+1}/{num_requests}")
                    response = handler.send_request()
                
                # 再次检查任务是否已被停止
                with task_lock:
                    if not task_status['is_running']:
                        app.logger.info("任务已被停止，中断处理响应")
                        break
                
                # 更新任务状态
                with task_lock:
                    task_status['completed'] += 1
                    completed_count += 1
                    
                    if response.get('success', False):
                        task_status['success'] += 1
                    else:
                        task_status['failed'] += 1
                
                    # 添加到结果列表
                    task_status['results'].append(response)
                
                    # 更新进度
                    task_status['progress'] = int((task_status['completed'] / task_status['total']) * 100)
                    
                    app.logger.debug(f"任务进度: {task_status['progress']}%, 完成: {task_status['completed']}/{task_status['total']}")
                
                # 添加延迟
                if config['delay'] > 0:
                    time.sleep(config['delay'])
                    
            except Exception as e:
                app.logger.error(f"请求执行错误: {str(e)}")
                with task_lock:
                    if not task_status['is_running']:
                        break
                        
                    task_status['failed'] += 1
                    task_status['completed'] += 1
                    completed_count += 1
                    task_status['progress'] = int((task_status['completed'] / task_status['total']) * 100)
                    task_status['results'].append({
                        'url': config['url'],
                        'success': False,
                        'error': str(e)
                    })
        
        # 保存结果
        with task_lock:
            result_count = len(task_status['results'])
            app.logger.info(f"任务完成: 总数={task_status['total']}, 完成={completed_count}, 成功={task_status['success']}, 失败={task_status['failed']}, 结果数={result_count}")
            
            # 如果任务是正常完成的，更新总数为实际完成数
            if task_status['is_running']:
                app.logger.info("任务正常完成")
                task_status['is_running'] = False
                
                # 如果实际完成的请求数与计划的不一致，更新总数
                if completed_count != num_requests:
                    app.logger.info(f"更新总请求数: {num_requests} -> {completed_count}")
                    task_status['total'] = completed_count
            
            result_file = os.path.join('results', f'result_{int(time.time())}.json')
            save_results({
                'total': task_status['total'],
                'success': task_status['success'],
                'failed': task_status['failed'],
                'responses': task_status['results']
            }, result_file)
            
            app.logger.info(f"结果已保存到: {result_file}")
        
    except Exception as e:
        app.logger.error(f"标准任务执行错误: {str(e)}")
        app.logger.exception(e)
    finally:
        # 确保任务标记为已完成
        with task_lock:
            if task_status['is_running']:
                task_status['is_running'] = False
                app.logger.info("在finally块中重置任务状态")
                
        app.logger.info("标准任务执行结束")

async def run_async_task(config, headers, params, data, payloads, num_requests, proxy_list, user_agents):
    """异步模式执行HTTP请求测试任务"""
    try:
        app.logger.info(f"启动异步任务: 请求数={num_requests}, 并发数={config['concurrency']}")
        
        completed_count = 0
        
        # 准备代理设置
        if config['use_proxy']:
            if config['proxy_mode'] == 'single' and config['proxy']:
                # 单个代理
                proxy = config['proxy']
                if not proxy.startswith(('http://', 'https://', 'socks4://', 'socks5://')):
                    proxy = f"{config['proxy_type']}://{proxy}"
                proxy_list = [proxy]
            elif not proxy_list:
                # 没有有效代理
                proxy_list = None
        else:
            proxy_list = None
        
        # 初始化异步请求处理器
        handler = AsyncRequestHandler(
            url=config['url'],
            method=config['method'],
            timeout=config['timeout'],
            max_connections=config['concurrency'],
            proxy_pool=proxy_list,
            proxy_type=config['proxy_type'],
            rotate_user_agents=config['rotate_user_agents']
        )
        
        # 设置请求头
        if headers:
            # 处理IP伪装
            if config['spoof_ip'] and config['spoof_ip_address']:
                headers['X-Forwarded-For'] = config['spoof_ip_address']
                headers['X-Real-IP'] = config['spoof_ip_address']
                headers['Client-IP'] = config['spoof_ip_address']
            
            # 自定义User-Agent文件
            if config['rotate_user_agents'] and config['ua_mode'] == 'file' and user_agents:
                # 让asyncio处理随机选择，我们不需要自己设置
                handler.set_user_agents(user_agents)
            
            handler.set_headers(headers)
        elif config['spoof_ip'] and config['spoof_ip_address']:
            # 只设置IP伪装头
            handler.set_headers({
                'X-Forwarded-For': config['spoof_ip_address'],
                'X-Real-IP': config['spoof_ip_address'],
                'Client-IP': config['spoof_ip_address']
            })
        
        # 设置请求参数
        if params:
            handler.set_params(params)
        
        # 设置请求数据
        if data:
            handler.set_data(data)
        
        app.logger.info(f"异步处理器配置完成，开始执行请求")
        
        # 批量发送请求
        if payloads:
            app.logger.info(f"使用载荷发送请求: {len(payloads)}个载荷项")
            # 按批次处理载荷，避免创建过多任务
            batch_size = min(500, config['concurrency'])
            for i in range(0, len(payloads), batch_size):
                # 检查任务是否应该继续
                with task_lock:
                    if not task_status['is_running']:
                        app.logger.info("任务已被停止")
                        break
                
                batch_payloads = payloads[i:i+batch_size]
                app.logger.debug(f"处理批次: {i//batch_size + 1}, 载荷数: {len(batch_payloads)}")
                
                # 处理每个载荷
                batch_tasks = []
                for payload in batch_payloads:
                    # 替换占位符
                    custom_url = config['url'].replace(config['placeholder'], payload) if config['placeholder'] in config['url'] else None
                    task = handler.send_request(payload=payload, custom_url=custom_url)
                    batch_tasks.append(task)
                
                # 使用as_completed执行所有任务
                for future in asyncio.as_completed(batch_tasks):
                    try:
                        response = await future
                        
                        # 再次检查任务是否已被停止
                        with task_lock:
                            if not task_status['is_running']:
                                app.logger.info("任务已被停止，中断处理响应")
                                break
                        
                        # 更新任务状态
                        with task_lock:
                            task_status['completed'] += 1
                            completed_count += 1
                            
                            if response.get('success', False):
                                task_status['success'] += 1
                            else:
                                task_status['failed'] += 1
                            
                            # 添加到结果列表
                            task_status['results'].append(response)
                            
                            # 更新进度
                            task_status['progress'] = int((task_status['completed'] / task_status['total']) * 100)
                        
                    except Exception as e:
                        app.logger.error(f"异步请求执行错误: {str(e)}")
                        
                        # 再次检查任务是否已被停止
                        with task_lock:
                            if not task_status['is_running']:
                                break
                                
                            task_status['failed'] += 1
                            task_status['completed'] += 1
                            completed_count += 1
                            task_status['progress'] = int((task_status['completed'] / task_status['total']) * 100)
                            task_status['results'].append({
                                'url': config['url'],
                                'success': False,
                                'error': str(e)
                            })
                
                # 批次间延迟
                if config['delay'] > 0:
                    await asyncio.sleep(config['delay'])
        else:
            app.logger.info(f"发送普通请求: 请求数={num_requests}")
            # 直接发送指定数量的请求
            result = await handler.send_requests_batch(
                count=num_requests,
                concurrency=config['concurrency']
            )
            
            # 更新任务状态
            with task_lock:
                task_status['success'] = result['success']
                task_status['failed'] = result['failed']
                task_status['completed'] = result['total']
                completed_count = result['total']
                task_status['results'] = result['responses']
                task_status['progress'] = 100
        
        # 保存结果
        with task_lock:
            app.logger.info(f"异步任务完成: 总数={task_status['total']}, 完成={completed_count}, 成功={task_status['success']}, 失败={task_status['failed']}")
            
            # 如果任务是正常完成的，更新总数为实际完成数
            if task_status['is_running']:
                app.logger.info("异步任务正常完成")
                task_status['is_running'] = False
                
                # 如果实际完成的请求数与计划的不一致，更新总数
                if completed_count != num_requests:
                    app.logger.info(f"更新总请求数: {num_requests} -> {completed_count}")
                    task_status['total'] = completed_count
            
            result_file = os.path.join('results', f'result_{int(time.time())}.json')
            save_results({
                'total': task_status['total'],
                'success': task_status['success'],
                'failed': task_status['failed'],
                'responses': task_status['results']
            }, result_file)
            
            app.logger.info(f"结果已保存到: {result_file}")
        
    except Exception as e:
        app.logger.error(f"异步任务执行错误: {str(e)}")
        app.logger.exception(e)  # 打印完整堆栈信息
    finally:
        # 确保任务标记为已完成
        with task_lock:
            if task_status['is_running']:
                task_status['is_running'] = False
                app.logger.info("在finally块中重置异步任务状态")
        
        app.logger.info("异步任务执行结束")

def run_request_test_task(config, headers, params, data, payloads, num_requests, proxy_list, user_agents):
    """在后台线程中执行HTTP请求测试任务"""
    task_thread = None
    
    try:
        app.logger.info(f"启动HTTP请求测试任务: 异步模式={config['use_async_mode']}, 请求数={num_requests}")
        
        # 使用异步模式
        if config['use_async_mode']:
            # 创建并执行异步任务
            asyncio.run(run_async_task(config, headers, params, data, payloads, num_requests, proxy_list, user_agents))
        # 使用标准模式
        else:
            run_standard_task(config, headers, params, data, payloads, num_requests, proxy_list, user_agents)
    except Exception as e:
        app.logger.error(f"任务执行错误: {str(e)}")
        app.logger.exception(e)  # 打印完整堆栈信息
    finally:
        # 确保任务标记为已完成
        with task_lock:
            if task_status['is_running']:
                app.logger.info("任务执行完成，重置状态")
                task_status['is_running'] = False
                
                # 检查是否所有请求都已完成
                if task_status['completed'] < task_status['total']:
                    app.logger.info(f"任务提前结束: {task_status['completed']}/{task_status['total']} 请求已完成")
                    # 更新总数以反映实际情况
                    task_status['total'] = task_status['completed']
        
        app.logger.info("任务执行完成，状态已重置")

def get_random_user_agent():
    """获取随机User-Agent"""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
    ]
    return random.choice(user_agents)

@app.route('/task_status')
def get_task_status():
    """获取当前任务状态"""
    try:
        with task_lock:
            status_copy = task_status.copy()
            # 只发送最近的10个结果，避免数据过大
            status_copy['results'] = status_copy['results'][-10:]
            
            # 确保任务状态是最新的
            if status_copy['completed'] >= status_copy['total'] and status_copy['total'] > 0:
                status_copy['is_running'] = False
                # 同步更新原始状态
                task_status['is_running'] = False
                app.logger.info("任务已完成，状态已更新为停止")
        
        return jsonify(status_copy)
    except Exception as e:
        app.logger.error(f"获取任务状态时出错: {str(e)}")
        return jsonify({'success': False, 'message': f'获取任务状态时出错: {str(e)}'})

@app.route('/stop_task')
def stop_task():
    """停止当前运行的任务"""
    try:
        app.logger.info("收到停止任务请求")
        with task_lock:
            # 检查任务是否正在运行
            if not task_status['is_running']:
                app.logger.warning("尝试停止一个未运行的任务")
                return jsonify({'success': True, 'message': '没有正在运行的任务'})
            
            # 标记任务为停止状态
            task_status['is_running'] = False
            app.logger.info("任务已被标记为停止")
        
        return jsonify({'success': True, 'message': '任务已停止'})
    except Exception as e:
        app.logger.error(f"停止任务时出错: {str(e)}")
        return jsonify({'success': False, 'message': f'停止任务时出错: {str(e)}'})

@app.route('/reset_task')
def reset_task():
    """重置任务状态API，用于解决任务状态卡住的问题"""
    reset_task_status()
    return jsonify({'success': True, 'message': '任务状态已重置'})

@app.route('/download_results')
def download_results():
    with task_lock:
        if not task_status['results']:
            return jsonify({'success': False, 'message': '没有可下载的结果'})
        
        # 保存当前结果到临时文件
        result_file = os.path.join('results', f'result_{int(time.time())}.json')
        save_results({
            'total': task_status['total'],
            'success': task_status['success'],
            'failed': task_status['failed'],
            'responses': task_status['results']
        }, result_file)
    
    return jsonify({'success': True, 'file': os.path.basename(result_file)})

@app.route('/results/<filename>')
def get_result_file(filename):
    return send_from_directory('results', filename, as_attachment=True)

def open_browser():
    """打开浏览器访问Web UI"""
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    import time
    
    # 确保任务状态正确初始化
    reset_task_status()
    
    # 创建线程打开浏览器
    threading.Timer(1.0, open_browser).start()
    
    # 启动Flask应用
    app.run(debug=False) 