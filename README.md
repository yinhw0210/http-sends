# HTTP 请求测试工具 v2.0

一个强大的HTTP请求测试工具，具备高级网络配置功能，支持配置请求地址、请求方式、请求参数和请求次数。主要用于性能测试、API调试、接口测试和服务器负载评估。

## 最新特性

- **高级网络配置功能**：支持代理池、UA轮换和源IP设置，有效优化网络请求和避免频率限制
- **高性能异步模式**：基于asyncio和aiohttp实现的异步协程架构，支持高并发请求，性能提升5-10倍
- **灵活的HTTP请求测试**：精确控制HTTP请求的每个方面，包括请求头、参数、数据和方法
- **可视化WebUI界面**：直观的Web界面操作，实时监控请求状态和结果
- **完整的代理功能**：支持HTTP/HTTPS/SOCKS代理，可从文件加载代理池并自动轮换

## 功能特点

- **HTTP请求测试**：支持多种HTTP请求方法（GET, POST, PUT, DELETE, HEAD, OPTIONS）
- **网络优化配置**：多层次的网络配置机制，包括代理服务器、User-Agent轮换和X-Forwarded-For头部控制
- **高性能设计**：支持多线程和异步协程两种并发模式，适应不同场景需求
- **灵活配置**：支持自定义请求头、URL参数、表单数据和JSON数据
- **参数化测试**：支持从文件加载测试数据，灵活插入到请求中的任何位置
- **实时监控**：可视化显示请求进度、成功率、响应时间等关键指标
- **结果分析**：详细记录请求结果，支持导出为JSON格式进行深入分析

## 界面预览

![HTTP 请求测试工具界面](https://cdn.picui.cn/vip/2025/07/25/68832e4f6c1fa.png)

*现代化的Web界面，支持实时监控请求状态和结果分析*

## 安装

### 前提条件

- Python 3.7+
- pip 包管理器

### 安装步骤

1. 克隆或下载本仓库

```bash
git clone https://github.com/your-username/precision-bruteforce.git
cd precision-bruteforce
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 统一启动方式

使用`run.py`统一启动脚本，可以方便地选择不同的使用模式：

```bash
# 查看帮助
python run.py

# 启动Web界面模式
python run.py --web

# 使用标准模式(多线程)
python run.py -u https://example.com -m POST -d '{"password":"PAYLOAD_PLACEHOLDER"}' -f sample_payloads.txt

# 使用高性能异步模式(协程)
python run.py --async -u https://example.com -m POST -d '{"password":"PAYLOAD_PLACEHOLDER"}' -f sample_payloads.txt -c 200

# 对比测试模式(同时使用两种模式并比较性能)
python run.py --compare -u https://example.com -n 1000
```

### 网络配置功能

使用代理服务器和UA轮换功能优化网络请求：

```bash
# 使用单个代理
python run.py --async -u https://example.com --proxy "http://user:pass@proxy.example.com:8080"

# 从文件加载代理池
python run.py --async -u https://example.com --proxy-file sample_proxies.txt

# 启用User-Agent随机轮换
python run.py --async -u https://example.com --rotate-user-agents

# 指定自定义User-Agent文件
python run.py --async -u https://example.com --rotate-user-agents --user-agents-file sample_user_agents.txt

# 自定义源IP地址(X-Forwarded-For)
python run.py --async -u https://example.com --spoof-ip "192.168.1.1"

# 组合使用多种网络优化技术
python run.py --async -u https://example.com --proxy-file sample_proxies.txt --rotate-user-agents --spoof-ip "192.168.1.1"
```

### 高性能压测模式

使用异步模式进行高并发压力测试：

```bash
# 使用1000并发连接对目标进行压测
python run.py --async -u https://example.com -c 1000 -n 100000

# 使用代理池进行大规模测试
python run.py --async -u https://example.com -c 500 -n 50000 --proxy-file sample_proxies.txt
```

### Web界面使用

1. 启动Web界面

```bash
python run.py --web
# 或者直接使用
python web_ui.py
```

2. 浏览器会自动打开 http://127.0.0.1:5000，如未自动打开，请手动访问该地址

3. 在Web界面中配置参数：
   - 输入目标URL
   - 选择请求方式
   - 配置请求头、URL参数、请求数据
   - 上传载荷文件或设置请求次数
   - 配置并发线程数、超时时间等参数

4. 点击"开始测试"按钮开始测试

5. 实时查看任务进度和结果统计

6. 任务完成后可下载结果JSON文件

### 命令行参数

#### 标准模式参数 (main.py)

```
参数:
  -h, --help            显示帮助信息并退出
  -u URL, --url URL     目标URL地址 (必需)
  -m METHOD, --method METHOD
                        HTTP请求方法 [GET|POST|PUT|DELETE|HEAD|OPTIONS] (默认: GET)
  -p PARAMS, --params PARAMS
                        请求参数，格式为key=value,key2=value2
  -d DATA, --data DATA  POST请求数据，JSON格式字符串或表单数据
  -H HEADERS, --headers HEADERS
                        请求头，格式为key=value,key2=value2
  -t THREADS, --threads THREADS
                        并发线程数 (默认: 10)
  -n NUM_REQUESTS, --num-requests NUM_REQUESTS
                        请求次数 (默认: 100)
  -f PAYLOAD_FILE, --payload-file PAYLOAD_FILE
                        载荷文件，每行一个值
  -o OUTPUT, --output OUTPUT
                        结果保存文件
  -T TIMEOUT, --timeout TIMEOUT
                        请求超时时间(秒) (默认: 10.0)
  --delay DELAY         请求间延迟时间(秒) (默认: 0.0)
  --placeholder PLACEHOLDER
                        载荷占位符文本 (默认: PAYLOAD_PLACEHOLDER)
```

#### 异步模式参数 (async_main.py)

```
参数:
  -h, --help            显示帮助信息并退出
  -u URL, --url URL     目标URL地址 (必需)
  -m METHOD, --method METHOD
                        HTTP请求方法 [GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH] (默认: GET)
  -p PARAMS, --params PARAMS
                        请求参数，格式为key=value,key2=value2
  -d DATA, --data DATA  请求数据，JSON格式字符串或表单数据
  -H HEADERS, --headers HEADERS
                        请求头，格式为key=value,key2=value2
  
  -c CONCURRENCY, --concurrency CONCURRENCY
                        并发连接数 (默认: 100)
  -n NUM_REQUESTS, --num-requests NUM_REQUESTS
                        请求次数 (默认: 1000)
  -T TIMEOUT, --timeout TIMEOUT
                        请求超时时间(秒) (默认: 10.0)
  --delay DELAY         请求间延迟时间(秒) (默认: 0.0)
  --rate-limit RATE_LIMIT
                        每秒请求速率限制
  
  -f PAYLOAD_FILE, --payload-file PAYLOAD_FILE
                        载荷文件，每行一个值
  --placeholder PLACEHOLDER
                        载荷占位符文本 (默认: PAYLOAD_PLACEHOLDER)
  
  --proxy PROXY         代理服务器，格式为http(s)://host:port或socks5://host:port
  --proxy-file PROXY_FILE
                        代理服务器列表文件，每行一个代理
  --proxy-type {http,https,socks4,socks5}
                        代理服务器类型 (默认: http)
  --rotate-user-agents  随机轮换User-Agent
  --user-agents-file USER_AGENTS_FILE
                        User-Agent列表文件，每行一个UA
  --spoof-ip SPOOF_IP   伪造源IP地址，将添加到X-Forwarded-For头
  
  -o OUTPUT, --output OUTPUT
                        结果保存文件
  -v, --verbose         显示详细输出
```

### 快速入门示例

工具已包含样本载荷文件、代理列表和User-Agent列表，可以直接用于测试：

```bash
# 使用样本数据进行登录表单测试(标准模式)
python run.py -u "https://example.com/login" -m POST -d '{"username":"admin","password":"PAYLOAD_PLACEHOLDER"}' -f sample_payloads.txt -t 5 --delay 0.5

# 使用异步模式和网络优化功能
python run.py --async -u "https://example.com/login" -m POST -d '{"username":"admin","password":"PAYLOAD_PLACEHOLDER"}' -f sample_payloads.txt -c 50 --proxy-file sample_proxies.txt --rotate-user-agents

# 对比测试两种模式的性能差异
python run.py --compare -u "https://example.com/api" -n 1000
```

### 代理文件格式

代理服务器列表文件格式：

```
# HTTP代理
http://127.0.0.1:8080
http://user:pass@proxy.example.com:8080

# HTTPS代理
https://secure-proxy.example.com:8443

# SOCKS代理
socks4://127.0.0.1:1080
socks5://socks-proxy.example.com:1080

# 无类型前缀的代理(将按照--proxy-type参数指定的类型处理)
192.168.1.1:3128
```

### User-Agent文件格式

User-Agent列表文件格式：

```
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36
Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15
```

### 标准模式和异步模式的选择

- **标准模式(多线程)**：适合简单测试、小规模请求，不需要高并发
- **异步模式(协程)**：适合大规模压测、高并发场景，性能显著高于标准模式
- **对比测试**：通过`--compare`参数可以依次使用两种模式并比较性能差异

## 高级用法

### 自定义载荷插入位置

在URL参数、请求头或请求体中使用`PAYLOAD_PLACEHOLDER`占位符：

```bash
# URL中的占位符
python run.py --async -u "https://example.com/api?id=PAYLOAD_PLACEHOLDER" -f ids.txt

# 请求头中的占位符
python run.py --async -u "https://example.com/api" -H "Authorization=Bearer PAYLOAD_PLACEHOLDER" -f tokens.txt

# JSON数据中的占位符
python run.py --async -u "https://example.com/login" -m POST -d '{"token":"PAYLOAD_PLACEHOLDER"}' -f tokens.txt

# 使用自定义占位符
python run.py --async -u "https://example.com/api" -H "X-Custom-Token=##TOKEN##" -f tokens.txt --placeholder "##TOKEN##"
```

### 限制请求速率

为避免触发目标站点的安全防护机制或造成过大负载，可以使用`--delay`参数设置请求间隔或使用`--rate-limit`参数限制每秒请求速率：

```bash
# 使用延迟控制速率
python run.py --async -u "https://example.com/api" -f payloads.txt --delay 0.5

# 限制每秒请求数
python run.py --async -u "https://example.com/api" -f payloads.txt --rate-limit 10
```

## 项目结构

```
.
├── main.py                # 标准模式主程序(多线程)
├── async_main.py          # 异步模式主程序(协程)
├── web_ui.py              # Web界面程序入口
├── run.py                 # 统一启动脚本
├── request_handler.py     # 标准请求处理模块
├── async_request_handler.py # 异步请求处理模块
├── utils.py               # 工具函数模块
├── static/                # 静态资源目录
│   └── style.css          # CSS样式文件
├── templates/             # HTML模板目录
│   └── index.html         # Web界面首页
├── sample_payloads.txt    # 样本载荷文件
├── sample_proxies.txt     # 样本代理列表
├── sample_user_agents.txt # 样本User-Agent列表
├── uploads/               # 上传文件存储目录
├── results/               # 结果文件存储目录
├── requirements.txt       # 项目依赖
├── README.md              # 项目文档
└── .gitignore             # Git忽略配置
```

## 性能对比

异步模式(协程)相比标准模式(多线程)的性能优势：

| 场景 | 请求数 | 标准模式(秒) | 异步模式(秒) | 性能提升 |
|------|--------|-------------|-------------|---------|
| 简单GET | 1,000 | 32.5 | 5.8 | 5.6倍 |
| POST表单 | 1,000 | 47.2 | 6.9 | 6.8倍 |
| API爆破 | 10,000 | 385.6 | 42.3 | 9.1倍 |

*以上数据基于本地测试环境，实际性能可能因网络条件和目标服务器而异。*

## 注意事项

- **合法使用**：请仅在获得授权的系统上进行测试，未经授权的测试可能违反法律法规
- **避免滥用**：过于频繁的请求可能会触发目标站点的安全防护机制或造成服务中断
- **渗透测试**：在进行正式渗透测试前，建议先使用较小的并发数和较长的延迟进行测试
- **数据保护**：测试过程中获取的敏感数据应妥善保管，避免泄露
- **代理安全**：使用代理服务器时，应确保代理服务器的安全性和可靠性
- **资源消耗**：高并发异步模式可能会消耗大量系统资源，请根据系统配置调整并发数

## 故障排除

- **连接错误**：检查网络连接和目标URL是否可访问
- **超时频繁**：尝试增加超时时间或减少并发数
- **内存占用过高**：减少并发连接数或分批处理大型载荷文件
- **结果保存失败**：检查输出路径是否有写入权限
- **Web界面无法打开**：检查端口5000是否被其他程序占用
- **代理连接失败**：检查代理服务器是否可用，格式是否正确
- **异步模式报错**：检查Python版本是否>=3.7，某些系统可能需要安装额外的SSL证书

## 许可证

MIT

## 贡献指南

欢迎提交问题报告、功能请求和代码贡献。请遵循以下步骤：

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 免责声明

本工具仅供安全研究和授权测试使用。用户须遵守相关法律法规，未经授权对任何系统进行测试属于违法行为。开发者对因滥用本工具导致的任何直接或间接损失不承担任何责任。 