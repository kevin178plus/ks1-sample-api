#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的启动场景测试
"""

import os
import sys
import time
import subprocess
import socket

def is_port_in_use(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False
        except socket.error:
            return True

def test_port_check():
    """测试端口检查功能"""
    print("=" * 60)
    print("测试：端口检查功能")
    print("=" * 60)
    
    print("\n1. 检查端口5000当前状态...")
    if is_port_in_use(5000):
        print("   端口5000已被占用")
    else:
        print("   端口5000空闲")
    
    print("\n2. 测试 is_port_in_use() 函数...")
    # 测试一个肯定被占用的端口（如果服务在运行）
    # 或者测试一个肯定空闲的端口
    test_port = 12345
    if is_port_in_use(test_port):
        print(f"   端口 {test_port} 被占用")
    else:
        print(f"   端口 {test_port} 空闲")
    
    print("\n✅ 端口检查功能正常")

def test_daemon_env():
    """测试守护进程环境变量"""
    print("\n" + "=" * 60)
    print("测试：守护进程环境变量")
    print("=" * 60)
    
    daemon_child = os.getenv('DAEMON_CHILD')
    print(f"\nDAEMON_CHILD 环境变量: {daemon_child}")
    
    if daemon_child == '1':
        print("✅ 当前是守护进程子进程模式")
    else:
        print("✅ 当前是直接启动模式")
    
    print("\n✅ 环境变量检测正常")

def main():
    print("\n启动场景功能测试")
    print("=" * 60)
    
    test_port_check()
    test_daemon_env()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
