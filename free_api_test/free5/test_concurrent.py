"""
测试并发请求以重现问题
"""
import requests
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def make_request(request_id):
    """发送单个请求"""
    url = "http://localhost:5005/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "iflow",
        "messages": [{"role": "user", "content": f"测试请求 {request_id}"}]
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        print(f"[请求 {request_id}] 状态码: {response.status_code}")

        if response.status_code == 200:
            try:
                result = response.json()
                print(f"[请求 {request_id}] 成功 - 响应长度: {len(str(result))}")
                return {"id": request_id, "status": "success", "response": result}
            except json.JSONDecodeError as e:
                print(f"[请求 {request_id}] JSON解析错误: {e}")
                print(f"[请求 {request_id}] 响应内容: {response.text[:200]}")
                return {"id": request_id, "status": "json_error", "error": str(e), "response": response.text}
        else:
            print(f"[请求 {request_id}] HTTP错误: {response.text}")
            return {"id": request_id, "status": "http_error", "code": response.status_code, "error": response.text}

    except requests.exceptions.Timeout:
        print(f"[请求 {request_id}] 超时")
        return {"id": request_id, "status": "timeout"}
    except requests.exceptions.ConnectionError as e:
        print(f"[请求 {request_id}] 连接错误: {e}")
        return {"id": request_id, "status": "connection_error", "error": str(e)}
    except Exception as e:
        print(f"[请求 {request_id}] 未知错误: {e}")
        return {"id": request_id, "status": "unknown_error", "error": str(e)}

def main():
    print("=" * 60)
    print("开始并发测试")
    print("=" * 60)

    # 测试不同数量的并发请求
    test_sizes = [5, 10, 15, 20]

    for size in test_sizes:
        print(f"\n测试 {size} 个并发请求...")
        print("-" * 60)

        results = []
        success_count = 0
        error_count = 0

        with ThreadPoolExecutor(max_workers=size) as executor:
            futures = [executor.submit(make_request, i+1) for i in range(size)]

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

                if result["status"] == "success":
                    success_count += 1
                else:
                    error_count += 1

        print(f"\n测试结果: 成功={success_count}, 失败={error_count}")

        # 统计错误类型
        error_types = {}
        for result in results:
            if result["status"] != "success":
                error_type = result["status"]
                error_types[error_type] = error_types.get(error_type, 0) + 1

        if error_types:
            print("错误类型分布:")
            for error_type, count in error_types.items():
                print(f"  {error_type}: {count}")

        time.sleep(2)  # 等待服务恢复

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()