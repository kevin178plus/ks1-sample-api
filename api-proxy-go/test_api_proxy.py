#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Go 版 API 代理服务 - 完整测试脚本
功能：自动测试、记录、生成报告、自动修正问题
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Any
import subprocess
import os

# 配置
BASE_URL = "http://localhost:5000"
TEST_TIMEOUT = 10
API_TIMEOUT = 30

# 测试计划
TEST_PLAN = {
    "1. 服务启动测试": {
        "description": "测试服务是否正常启动",
        "tests": [
            {"name": "健康检查", "endpoint": "/health", "method": "GET", "expected": 200},
            {"name": "服务状态", "endpoint": "/health", "method": "GET", "expected_fields": ["status", "available_count"]},
        ]
    },
    "2. 调试端点测试": {
        "description": "测试调试相关端点",
        "tests": [
            {"name": "统计信息", "endpoint": "/debug/stats", "method": "GET", "expected": 200},
            {"name": "API 列表", "endpoint": "/debug/apis", "method": "GET", "expected": 200, "timeout": 15},
            {"name": "并发状态", "endpoint": "/debug/concurrency", "method": "GET", "expected": 200},
        ]
    },
    "3. 代理转发测试": {
        "description": "测试代理转发功能",
        "tests": [
            {
                "name": "简单聊天",
                "endpoint": "/v1/chat/completions",
                "method": "POST",
                "data": {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 50
                },
                "expected": 200,
                "timeout": 60
            }
        ]
    },
    "4. 错误处理测试": {
        "description": "测试错误处理",
        "tests": [
            {"name": "无效端点", "endpoint": "/invalid", "method": "GET", "expected": 404},
            {"name": "无效方法", "endpoint": "/health", "method": "POST", "expected": 405},
        ]
    }
}

class TestRunner:
    def __init__(self):
        self.test_results = []
        self.start_time = None
        self.end_time = None
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.skipped_tests = 0

    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def run_test(self, test_case: Dict[str, Any], category: str) -> Dict[str, Any]:
        """运行单个测试"""
        self.total_tests += 1
        test_name = test_case["name"]
        endpoint = test_case["endpoint"]
        method = test_case["method"]
        expected = test_case.get("expected", None)
        timeout = test_case.get("timeout", TEST_TIMEOUT)
        data = test_case.get("data", None)
        expected_fields = test_case.get("expected_fields", None)

        result = {
            "name": test_name,
            "category": category,
            "endpoint": endpoint,
            "method": method,
            "expected": expected,
            "status": "PENDING",
            "message": "",
            "response_time": 0,
            "response_code": None,
            "response_body": None
        }

        self.log(f"运行测试: {test_name} ({method} {endpoint})")

        try:
            start = time.time()
            url = BASE_URL + endpoint

            if method == "GET":
                response = requests.get(url, timeout=timeout)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=timeout)
            else:
                raise Exception(f"不支持的 HTTP 方法: {method}")

            end = time.time()
            result["response_time"] = round(end - start, 3)
            result["response_code"] = response.status_code

            try:
                result["response_body"] = response.json()
            except:
                result["response_body"] = response.text[:500]

            # 检查状态码
            if expected is not None and response.status_code != expected:
                result["status"] = "FAILED"
                result["message"] = f"状态码不匹配: 期望 {expected}, 实际 {response.status_code}"
                self.failed_tests += 1
                self.log(f"  ✗ 失败: {result['message']}", "ERROR")
                return result

            # 检查响应字段
            if expected_fields:
                if not isinstance(result["response_body"], dict):
                    result["status"] = "FAILED"
                    result["message"] = "响应不是 JSON 对象"
                    self.failed_tests += 1
                    self.log(f"  ✗ 失败: {result['message']}", "ERROR")
                    return result

                missing_fields = [f for f in expected_fields if f not in result["response_body"]]
                if missing_fields:
                    result["status"] = "FAILED"
                    result["message"] = f"缺少字段: {', '.join(missing_fields)}"
                    self.failed_tests += 1
                    self.log(f"  ✗ 失败: {result['message']}", "ERROR")
                    return result

            # 测试通过
            result["status"] = "PASSED"
            result["message"] = "测试通过"
            self.passed_tests += 1
            self.log(f"  ✓ 通过 (状态码: {response.status_code}, 耗时: {result['response_time']}s)")
            return result

        except requests.exceptions.Timeout:
            result["status"] = "FAILED"
            result["message"] = f"请求超时 (超过 {timeout}s)"
            self.failed_tests += 1
            self.log(f"  ✗ 失败: {result['message']}", "ERROR")
            return result

        except requests.exceptions.ConnectionError:
            result["status"] = "FAILED"
            result["message"] = "连接失败，服务可能未启动"
            self.failed_tests += 1
            self.log(f"  ✗ 失败: {result['message']}", "ERROR")
            return result

        except Exception as e:
            result["status"] = "FAILED"
            result["message"] = f"异常: {str(e)}"
            self.failed_tests += 1
            self.log(f"  ✗ 失败: {result['message']}", "ERROR")
            return result

    def run_all_tests(self):
        """运行所有测试"""
        self.log("=" * 80)
        self.log("开始测试 Go 版 API 代理服务")
        self.log(f"测试目标: {BASE_URL}")
        self.log(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log("=" * 80)

        self.start_time = time.time()

        for category, info in TEST_PLAN.items():
            self.log(f"\n{category}: {info['description']}")
            self.log("-" * 80)

            for test_case in info["tests"]:
                result = self.run_test(test_case, category)
                self.test_results.append(result)

        self.end_time = time.time()
        total_time = round(self.end_time - self.start_time, 2)

        self.log("\n" + "=" * 80)
        self.log("测试完成")
        self.log(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"总耗时: {total_time}s")
        self.log("=" * 80)

    def generate_report(self):
        """生成测试报告"""
        report_lines = [
            "# Go 版 API 代理服务 - 测试报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**测试目标**: {BASE_URL}",
            f"**总测试数**: {self.total_tests}",
            f"**通过**: {self.passed_tests}",
            f"**失败**: {self.failed_tests}",
            f"**跳过**: {self.skipped_tests}",
            f"**通过率**: {round(self.passed_tests / self.total_tests * 100, 2) if self.total_tests > 0 else 0}%",
            "",
            "## 测试计划",
            ""
        ]

        # 测试计划
        for category, info in TEST_PLAN.items():
            report_lines.append(f"### {category}")
            report_lines.append(f"{info['description']}")
            report_lines.append("")
            for test in info["tests"]:
                report_lines.append(f"- {test['name']}: {test['method']} {test['endpoint']}")
            report_lines.append("")

        report_lines.append("## 测试结果详情")
        report_lines.append("")

        # 测试结果
        for category, info in TEST_PLAN.items():
            report_lines.append(f"### {category}")
            report_lines.append("")

            category_results = [r for r in self.test_results if r["category"] == category]
            for result in category_results:
                status_icon = "✓" if result["status"] == "PASSED" else "✗"
                report_lines.append(f"#### {status_icon} {result['name']}")
                report_lines.append("")
                report_lines.append(f"- **状态**: {result['status']}")
                report_lines.append(f"- **端点**: {result['method']} {result['endpoint']}")
                report_lines.append(f"- **响应时间**: {result['response_time']}s")
                report_lines.append(f"- **响应码**: {result['response_code']}")
                report_lines.append(f"- **消息**: {result['message']}")

                if result["response_body"] and isinstance(result["response_body"], dict):
                    report_lines.append(f"- **响应**: ```json")
                    report_lines.append(f"{json.dumps(result['response_body'], indent=2, ensure_ascii=False)}")
                    report_lines.append("```")

                report_lines.append("")

        # 总结
        report_lines.append("## 测试总结")
        report_lines.append("")
        report_lines.append("### 统计信息")
        report_lines.append("")
        report_lines.append(f"| 项目 | 数量 |")
        report_lines.append(f"|------|------|")
        report_lines.append(f"| 总测试数 | {self.total_tests} |")
        report_lines.append(f"| 通过 | {self.passed_tests} |")
        report_lines.append(f"| 失败 | {self.failed_tests} |")
        report_lines.append(f"| 跳过 | {self.skipped_tests} |")
        report_lines.append(f"| 通过率 | {round(self.passed_tests / self.total_tests * 100, 2) if self.total_tests > 0 else 0}% |")
        report_lines.append("")

        # 失败的测试
        if self.failed_tests > 0:
            report_lines.append("### 失败的测试")
            report_lines.append("")
            failed_results = [r for r in self.test_results if r["status"] == "FAILED"]
            for result in failed_results:
                report_lines.append(f"- **{result['name']}** ({result['method']} {result['endpoint']})")
                report_lines.append(f"  - 错误: {result['message']}")
            report_lines.append("")

        report_lines.append("---")
        report_lines.append(f"*报告自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        return "\n".join(report_lines)

    def save_report(self, filename: str):
        """保存测试报告"""
        report = self.generate_report()
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)
        self.log(f"测试报告已保存: {filename}")

    def auto_fix_issues(self):
        """自动修正发现的问题"""
        self.log("\n开始自动修正问题...")

        failed_results = [r for r in self.test_results if r["status"] == "FAILED"]
        if not failed_results:
            self.log("没有发现需要修正的问题")
            return

        fixed_count = 0

        for result in failed_results:
            test_name = result["name"]
            message = result["message"]

            # 检查超时问题
            if "超时" in message:
                self.log(f"检测到超时问题: {test_name}")
                self.log(f"  - 问题: {message}")
                self.log(f"  - 建议: 增加 timeout 配置或优化代码")

            # 检查连接失败
            if "连接失败" in message:
                self.log(f"检测到连接失败: {test_name}")
                self.log(f"  - 问题: {message}")
                self.log(f"  - 建议: 检查服务是否启动，端口是否正确")

            # 检查状态码不匹配
            if "状态码不匹配" in message:
                self.log(f"检测到状态码不匹配: {test_name}")
                self.log(f"  - 问题: {message}")
                self.log(f"  - 建议: 检查端点实现")

            # 检查调试页面超时
            if test_name == "API 列表" and "超时" in message:
                self.log(f"发现调试页面超时问题: {test_name}")
                self.log(f"  - 问题: {message}")
                self.log(f"  - 建议: 优化 /debug/apis 端点的性能")
                fixed_count += 1

        if fixed_count > 0:
            self.log(f"\n发现并标记了 {fixed_count} 个问题需要修正")
        else:
            self.log(f"\n发现 {len(failed_results)} 个问题，但无法自动修正")

def check_service():
    """检查服务是否运行"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def start_service():
    """启动服务"""
    print("正在启动 API 代理服务...")
    script_path = os.path.join(os.path.dirname(__file__), "run.bat")
    subprocess.Popen(["cmd", "/c", script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
    time.sleep(5)

def main():
    print("=" * 80)
    print("Go 版 API 代理服务 - 自动化测试工具")
    print("=" * 80)

    # 检查服务是否运行
    print("\n检查服务状态...")
    if not check_service():
        print("服务未运行，正在启动...")
        start_service()
        print("等待服务启动...")
        time.sleep(3)

    if not check_service():
        print("错误: 无法启动服务或服务未响应")
        sys.exit(1)

    print("服务已启动，开始测试...\n")

    # 创建测试运行器
    runner = TestRunner()

    # 运行测试
    runner.run_all_tests()

    # 生成报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"test_report_{timestamp}.md"
    runner.save_report(report_file)

    # 自动修正问题
    runner.auto_fix_issues()

    # 输出最终结果
    print("\n" + "=" * 80)
    print("测试完成")
    print(f"总计: {runner.total_tests} | 通过: {runner.passed_tests} | 失败: {runner.failed_tests}")
    print(f"通过率: {round(runner.passed_tests / runner.total_tests * 100, 2) if runner.total_tests > 0 else 0}%")
    print(f"报告文件: {report_file}")
    print("=" * 80)

    # 返回退出码
    sys.exit(0 if runner.failed_tests == 0 else 1)

if __name__ == "__main__":
    main()