#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书SSL连接测试脚本
用于诊断飞书API的SSL连接问题
"""

import requests
import ssl
import socket
import sys
import traceback
from urllib.parse import urlparse
from datetime import datetime
import certifi
import urllib3

# 飞书API基础URL
FEISHU_BASE_URL = "https://open.feishu.cn"
FEISHU_AUTH_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"

def test_basic_ssl_connection():
    """测试基本的SSL连接"""
    print("\n=== 基本SSL连接测试 ===")
    
    try:
        # 解析URL
        parsed_url = urlparse(FEISHU_BASE_URL)
        hostname = parsed_url.hostname
        port = parsed_url.port or 443
        
        print(f"连接目标: {hostname}:{port}")
        
        # 创建SSL上下文
        context = ssl.create_default_context()
        
        # 创建socket连接
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                print(f"SSL连接成功!")
                print(f"协议版本: {ssock.version()}")
                print(f"加密套件: {ssock.cipher()}")
                
                # 获取证书信息
                cert = ssock.getpeercert()
                print(f"证书主题: {cert.get('subject', 'N/A')}")
                print(f"证书颁发者: {cert.get('issuer', 'N/A')}")
                print(f"证书有效期: {cert.get('notBefore', 'N/A')} - {cert.get('notAfter', 'N/A')}")
                
        return True
        
    except Exception as e:
        print(f"SSL连接失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        traceback.print_exc()
        return False

def test_requests_ssl():
    """测试requests库的SSL连接"""
    print("\n=== Requests库SSL测试 ===")
    
    try:
        # 测试不同的SSL配置
        configs = [
            {"name": "默认配置", "verify": True},
            {"name": "使用certifi证书", "verify": certifi.where()},
            {"name": "禁用SSL验证", "verify": False}
        ]
        
        for config in configs:
            print(f"\n测试配置: {config['name']}")
            try:
                # 禁用SSL警告（仅用于测试）
                if not config['verify']:
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                
                response = requests.get(
                    FEISHU_BASE_URL,
                    verify=config['verify'],
                    timeout=10
                )
                
                print(f"状态码: {response.status_code}")
                print(f"响应头: {dict(list(response.headers.items())[:3])}")
                print("连接成功!")
                
                return True
                
            except requests.exceptions.SSLError as e:
                print(f"SSL错误: {e}")
            except requests.exceptions.ConnectionError as e:
                print(f"连接错误: {e}")
            except Exception as e:
                print(f"其他错误: {e}")
        
        return False
        
    except Exception as e:
        print(f"测试过程出错: {e}")
        traceback.print_exc()
        return False

def test_feishu_auth_endpoint():
    """测试飞书认证端点"""
    print("\n=== 飞书认证端点测试 ===")
    
    try:
        # 测试认证端点的连接性
        response = requests.post(
            FEISHU_AUTH_URL,
            json={"app_id": "test", "app_secret": "test"},
            timeout=10,
            verify=True
        )
        
        print(f"认证端点状态码: {response.status_code}")
        print(f"响应内容: {response.text[:200]}")
        
        if response.status_code in [200, 400, 401]:  # 这些都表示连接成功
            print("认证端点连接正常")
            return True
        else:
            print(f"认证端点返回异常状态码: {response.status_code}")
            return False
            
    except requests.exceptions.SSLError as e:
        print(f"认证端点SSL错误: {e}")
        return False
    except Exception as e:
        print(f"认证端点测试错误: {e}")
        traceback.print_exc()
        return False

def check_ssl_environment():
    """检查SSL环境配置"""
    print("\n=== SSL环境检查 ===")
    
    try:
        # 检查Python SSL模块
        print(f"Python版本: {sys.version}")
        print(f"SSL模块版本: {ssl.OPENSSL_VERSION}")
        print(f"SSL模块版本号: {ssl.OPENSSL_VERSION_NUMBER}")
        
        # 检查证书路径
        print(f"默认CA证书路径: {ssl.get_default_verify_paths()}")
        print(f"Certifi证书路径: {certifi.where()}")
        
        # 检查支持的协议
        print(f"支持的SSL协议: {ssl.PROTOCOL_TLS}")
        
        # 检查环境变量
        import os
        ssl_env_vars = ['SSL_CERT_FILE', 'SSL_CERT_DIR', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE']
        print("\nSSL相关环境变量:")
        for var in ssl_env_vars:
            value = os.environ.get(var, 'Not set')
            print(f"  {var}: {value}")
            
    except Exception as e:
        print(f"环境检查出错: {e}")
        traceback.print_exc()

def provide_ssl_diagnostics(test_results):
    """提供SSL问题诊断建议"""
    print("\n=== SSL问题诊断建议 ===")
    
    if all(test_results.values()):
        print("✅ 所有SSL测试都通过了，连接正常!")
        return
    
    print("❌ 检测到SSL连接问题，以下是可能的解决方案:")
    
    if not test_results.get('basic_ssl', True):
        print("\n🔧 基本SSL连接失败:")
        print("  1. 检查网络连接是否正常")
        print("  2. 检查防火墙设置")
        print("  3. 检查代理设置")
        print("  4. 尝试更新系统时间")
    
    if not test_results.get('requests_ssl', True):
        print("\n🔧 Requests SSL连接失败:")
        print("  1. 更新requests库: pip install --upgrade requests")
        print("  2. 更新certifi库: pip install --upgrade certifi")
        print("  3. 更新urllib3库: pip install --upgrade urllib3")
        print("  4. 检查是否有企业代理或防火墙拦截")
    
    if not test_results.get('feishu_auth', True):
        print("\n🔧 飞书认证端点连接失败:")
        print("  1. 检查是否能访问飞书官网")
        print("  2. 检查DNS设置")
        print("  3. 尝试使用VPN或更换网络")
        print("  4. 联系网络管理员检查企业网络策略")
    
    print("\n💡 通用解决方案:")
    print("  1. 重启Python环境")
    print("  2. 清除pip缓存: pip cache purge")
    print("  3. 重新安装SSL相关库")
    print("  4. 检查系统证书存储")

def main():
    """主函数"""
    print(f"飞书SSL连接诊断工具")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 检查SSL环境
    check_ssl_environment()
    
    # 执行各项测试
    test_results = {}
    
    test_results['basic_ssl'] = test_basic_ssl_connection()
    test_results['requests_ssl'] = test_requests_ssl()
    test_results['feishu_auth'] = test_feishu_auth_endpoint()
    
    # 提供诊断建议
    provide_ssl_diagnostics(test_results)
    
    print("\n=== 测试完成 ===")
    print(f"测试结果汇总:")
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")

if __name__ == "__main__":
    main()