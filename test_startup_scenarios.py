#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
启动场景测试脚本
测试不同启动顺序下的行为，验证端口检查和启动模式检测
"""

import os
import sys
import time
import subprocess
import socket
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
MAIN_SCRIPT = SCRIPT_DIR / "local_api_proxy.py"
DAEMON_SCRIPT = SCRIPT_DIR / "daemon.py"
PID_FILE = SCRIPT_DIR / "daemon.pid"

def is_port_in_use(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False
        except socket.error:
            return True

def get_daemon_status():
    """获取守护进程状态"""
    if PID_FILE.exists():
        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            result = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}'],
                capture_output=True,
                text=True
            )
            return str(pid) in result.stdout
        except Exception:
            return False
    return False

def stop_all():
    """停止所有进程"""
    print("\n" + "=" * 60)
    print("清理：停止所有进程...")
    print("=" * 60)
    
    # 停止守护进程
    if get_daemon_status():
        print("停止守护进程...")
        subprocess.run([sys.executable, str(DAEMON_SCRIPT), "stop"], capture_output=True)
        time.sleep(2)
    
    # 停止所有占用5000端口的进程
    try:
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True,
            text=True
        )
        for line in result.stdout.split('\n'):
            if ':5000' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    print(f"停止进程 {pid} (占用端口5000)...")
                    subprocess.run(['taskkill', '/PID', pid, '/F'], capture_output=True)
    except Exception as e:
        print(f"清理端口时出错: {e}")
    
    time.sleep(1)
    print("清理完成\n")

def test_scenario_1():
    """场景1：直接启动（端口空闲）"""
    print("\n" + "=" * 60)
    print("场景1：直接启动（端口空闲）")
    print("=" * 60)
    
    if is_port_in_use(5000):
        print("❌ 跳过：端口5000已被占用")
        return False
    
    print("启动 local_api_proxy.py...")
    process = subprocess.Popen(
        [sys.executable, str(MAIN_SCRIPT)],
        cwd=SCRIPT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    time.sleep(3)
    
    if is_port_in_use(5000):
        print("✅ 成功：端口5000已被占用（服务启动成功）")
        process.terminate()
        process.wait(timeout=5)
        return True
    else:
        print("❌ 失败：端口5000未被占用（服务启动失败）")
        process.terminate()
        process.wait(timeout=5)
        return False

def test_scenario_2():
    """场景2：直接启动（端口被占用）"""
    print("\n" + "=" * 60)
    print("场景2：直接启动（端口被占用）")
    print("=" * 60)
    
    # 先启动一个进程占用端口
    print("步骤1：启动第一个进程...")
    process1 = subprocess.Popen(
        [sys.executable, str(MAIN_SCRIPT)],
        cwd=SCRIPT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    time.sleep(3)
    
    if not is_port_in_use(5000):
        print("❌ 失败：第一个进程未成功启动")
        process1.terminate()
        process1.wait(timeout=5)
        return False
    
    print("步骤2：第一个进程已启动，端口5000被占用")
    
    # 尝试启动第二个进程
    print("步骤3：尝试启动第二个进程...")
    process2 = subprocess.Popen(
        [sys.executable, str(MAIN_SCRIPT)],
        cwd=SCRIPT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    time.sleep(2)
    
    # 检查第二个进程的输出
    output = process2.stdout.read()
    if "端口 5000 已被占用" in output:
        print("✅ 成功：第二个进程检测到端口占用并退出")
        result = True
    else:
        print("❌ 失败：第二个进程未检测到端口占用")
        result = False
    
    # 清理
    process1.terminate()
    process1.wait(timeout=5)
    process2.terminate()
    process2.wait(timeout=5)
    
    return result

def test_scenario_3():
    """场景3：守护进程启动"""
    print("\n" + "=" * 60)
    print("场景3：守护进程启动")
    print("=" * 60)
    
    if get_daemon_status():
        print("❌ 跳过：守护进程已在运行")
        return False
    
    print("启动守护进程...")
    process = subprocess.Popen(
        [sys.executable, str(DAEMON_SCRIPT), "start"],
        cwd=SCRIPT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    time.sleep(3)
    
    if get_daemon_status():
        print("✅ 成功：守护进程已启动")
        if is_port_in_use(5000):
            print("✅ 成功：端口5000已被占用（服务启动成功）")
            result = True
        else:
            print("❌ 失败：端口5000未被占用")
            result = False
    else:
        print("❌ 失败：守护进程未启动")
        result = False
    
    # 停止守护进程
    subprocess.run([sys.executable, str(DAEMON_SCRIPT), "stop"], capture_output=True)
    time.sleep(2)
    
    return result

def test_scenario_4():
    """场景4：守护进程运行时直接启动"""
    print("\n" + "=" * 60)
    print("场景4：守护进程运行时直接启动")
    print("=" * 60)
    
    # 先启动守护进程
    print("步骤1：启动守护进程...")
    subprocess.run([sys.executable, str(DAEMON_SCRIPT), "start"], capture_output=True)
    time.sleep(3)
    
    if not get_daemon_status():
        print("❌ 失败：守护进程未启动")
        return False
    
    print("步骤2：守护进程已启动")
    
    # 尝试直接启动
    print("步骤3：尝试直接启动 local_api_proxy.py...")
    process = subprocess.Popen(
        [sys.executable, str(MAIN_SCRIPT)],
        cwd=SCRIPT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    time.sleep(2)
    
    # 检查输出
    output = process.stdout.read()
    if "端口 5000 已被占用" in output:
        print("✅ 成功：直接启动检测到端口占用并退出")
        result = True
    else:
        print("❌ 失败：直接启动未检测到端口占用")
        result = False
    
    # 清理
    process.terminate()
    process.wait(timeout=5)
    subprocess.run([sys.executable, str(DAEMON_SCRIPT), "stop"], capture_output=True)
    time.sleep(2)
    
    return result

def test_scenario_5():
    """场景5：直接启动后守护进程启动"""
    print("\n" + "=" * 60)
    print("场景5：直接启动后守护进程启动")
    print("=" * 60)
    
    # 先直接启动
    print("步骤1：直接启动 local_api_proxy.py...")
    process1 = subprocess.Popen(
        [sys.executable, str(MAIN_SCRIPT)],
        cwd=SCRIPT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    time.sleep(3)
    
    if not is_port_in_use(5000):
        print("❌ 失败：第一个进程未启动")
        process1.terminate()
        process1.wait(timeout=5)
        return False
    
    print("步骤2：第一个进程已启动，端口5000被占用")
    
    # 尝试启动守护进程
    print("步骤3：尝试启动守护进程...")
    result = subprocess.run(
        [sys.executable, str(DAEMON_SCRIPT), "start"],
        cwd=SCRIPT_DIR,
        capture_output=True,
        text=True
    )
    
    time.sleep(2)
    
    # 检查守护进程是否启动
    if get_daemon_status():
        print("✅ 成功：守护进程已启动（子进程启动失败是正常的）")
        result = True
    else:
        print("❌ 失败：守护进程未启动")
        result = False
    
    # 清理
    process1.terminate()
    process1.wait(timeout=5)
    subprocess.run([sys.executable, str(DAEMON_SCRIPT), "stop"], capture_output=True)
    time.sleep(2)
    
    return result

def test_scenario_6():
    """场景6：守护进程重复启动"""
    print("\n" + "=" * 60)
    print("场景6：守护进程重复启动")
    print("=" * 60)
    
    # 第一次启动
    print("步骤1：第一次启动守护进程...")
    subprocess.run([sys.executable, str(DAEMON_SCRIPT), "start"], capture_output=True)
    time.sleep(3)
    
    if not get_daemon_status():
        print("❌ 失败：第一次启动失败")
        return False
    
    print("步骤2：第一次启动成功")
    
    # 第二次启动
    print("步骤3：尝试第二次启动守护进程...")
    result = subprocess.run(
        [sys.executable, str(DAEMON_SCRIPT), "start"],
        cwd=SCRIPT_DIR,
        capture_output=True,
        text=True
    )
    
    if "Daemon already running" in result.stdout:
        print("✅ 成功：第二次启动被拒绝（单例保护生效）")
        result = True
    else:
        print("❌ 失败：第二次启动未被拒绝")
        result = False
    
    # 清理
    subprocess.run([sys.executable, str(DAEMON_SCRIPT), "stop"], capture_output=True)
    time.sleep(2)
    
    return result

def main():
    print("=" * 60)
    print("启动场景测试")
    print("=" * 60)
    
    # 先清理所有进程
    stop_all()
    
    # 运行所有测试场景
    results = []
    
    try:
        results.append(("场景1：直接启动（端口空闲）", test_scenario_1()))
        results.append(("场景2：直接启动（端口被占用）", test_scenario_2()))
        results.append(("场景3：守护进程启动", test_scenario_3()))
        results.append(("场景4：守护进程运行时直接启动", test_scenario_4()))
        results.append(("场景5：直接启动后守护进程启动", test_scenario_5()))
        results.append(("场景6：守护进程重复启动", test_scenario_6()))
    finally:
        # 最终清理
        stop_all()
    
    # 生成报告
    print("\n" + "=" * 60)
    print("测试报告")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print("\n" + "=" * 60)
    print(f"总计：{passed}/{total} 通过")
    print("=" * 60)
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
