#!/usr/bin/env python3
"""
测试新增功能的脚本
- 并发控制
- 智能重试机制
"""

import requests
import time
import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://localhost:5000"

def test_single_request():
    """测试单个请求"""
    print("\n=== 测试单个请求 ===")
    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json={
                "model": "any-model",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 100
            },
            timeout=30
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应: {data.get('choices', [{}])[0].get('message', {}).get('content', 'N/A')[:100]}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")

def test_concurrent_requests(num_requests=10):
    """测试并发请求"""
    print(f"\n=== 测试并发请求 (共 {num_requests} 个) ===")
    
    def make_request(request_id):
        start_time = time.time()
        try:
            response = requests.post(
                f"{BASE_URL}/v1/chat/completions",
                json={
                    "model": "any-model",
                    "messages": [{"role": "user", "content": f"Request {request_id}"}],
                    "max_tokens": 100
                },
                timeout=30
            )
            elapsed = time.time() - start_time
            status = "✓" if response.status_code == 200 else "✗"
            print(f"  [{status}] 请求 {request_id}: {elapsed:.2f}s")
            return request_id, response.status_code, elapsed
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  [✗] 请求 {request_id}: 失败 ({e}) - {elapsed:.2f}s")
            return request_id, None, elapsed
    
    start_time = time.time()
    results = []
    
    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = [executor.submit(make_request, i) for i in range(1, num_requests + 1)]
        for future in as_completed(futures):
            results.append(future.result())
    
    total_time = time.time() - start_time
    successful = sum(1 for _, status, _ in results if status == 200)
    
    print(f"\n并发测试结果:")
    print(f"  总耗时: {total_time:.2f}s")
    print(f"  成功: {successful}/{num_requests}")
    print(f"  平均响应时间: {sum(t for _, _, t in results) / len(results):.2f}s")

def test_concurrency_status():
    """查看并发状态"""
    print("\n=== 查看并发状态 ===")
    try:
        response = requests.get(f"{BASE_URL}/debug/concurrency")
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")

def test_stats():
    """查看统计信息"""
    print("\n=== 查看统计信息 ===")
    try:
        response = requests.get(f"{BASE_URL}/debug/stats")
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")

def test_health():
    """健康检查"""
    print("\n=== 健康检查 ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print(f"服务状态: {response.json()}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")

def main():
    print("=" * 60)
    print("API 代理新功能测试")
    print("=" * 60)
    
    # 检查服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("错误: 服务未运行或返回异常")
            return
    except Exception as e:
        print(f"错误: 无法连接到服务 ({e})")
        print("请确保服务已启动: python local_api_proxy.py")
        return
    
    # 运行测试
    test_health()
    test_single_request()
    test_concurrency_status()
    test_stats()
    
    # 并发测试
    print("\n" + "=" * 60)
    print("开始并发测试...")
    print("=" * 60)
    test_concurrent_requests(num_requests=10)
    
    # 最后查看状态
    test_concurrency_status()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
