#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
服务器环境诊断和测试脚本
专为 Windows Server 2012 R2 设计，无需安装额外工具
"""

import os
import sys
import socket
import subprocess
import platform
import json
from pathlib import Path

class ServerDiagnostic:
    def __init__(self):
        self.results = {
            "system": {},
            "python": {},
            "dependencies": {},
            "configuration": {},
            "network": {},
            "service": {}
        }
        self.script_dir = Path(__file__).parent
        self.win2012_dir = self.script_dir / "scenarios" / "win2012-server"
    
    def check_system_info(self):
        """检查系统信息"""
        print("=" * 70)
        print("1. 系统信息检查")
        print("=" * 70)
        
        self.results["system"]["os"] = platform.system()
        self.results["system"]["os_version"] = platform.version()
        self.results["system"]["os_release"] = platform.release()
        self.results["system"]["machine"] = platform.machine()
        self.results["system"]["processor"] = platform.processor()
        
        print(f"操作系统: {self.results['system']['os']} {self.results['system']['os_release']}")
        print(f"版本: {self.results['system']['os_version']}")
        print(f"架构: {self.results['system']['machine']}")
        print(f"处理器: {self.results['system']['processor']}")
        
        # 检查内存
        try:
            result = subprocess.run(
                ['wmic', 'OS', 'get', 'TotalVisibleMemorySize'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    memory_kb = int(lines[1].strip())
                    memory_mb = memory_kb // 1024
                    self.results["system"]["total_memory_mb"] = memory_mb
                    print(f"总内存: {memory_mb} MB")
                    
                    if memory_mb < 2048:
                        print("⚠️  警告：内存不足2GB，可能影响性能")
                    else:
                        print("✅ 内存充足")
        except Exception as e:
            print(f"⚠️  无法获取内存信息: {e}")
        
        print()
    
    def check_python_environment(self):
        """检查Python环境"""
        print("=" * 70)
        print("2. Python环境检查")
        print("=" * 70)
        
        self.results["python"]["version"] = sys.version
        self.results["python"]["executable"] = sys.executable
        self.results["python"]["path"] = sys.path
        
        print(f"Python版本: {self.results['python']['version']}")
        print(f"Python路径: {self.results['python']['executable']}")
        
        # 检查Python版本
        major, minor = sys.version_info[:2]
        if major == 3 and minor >= 7:
            print("✅ Python版本符合要求（3.7+）")
        else:
            print("❌ Python版本过低，建议使用3.7+")
        
        # 检查pip
        try:
            subprocess.run(
                [sys.executable, '-m', 'pip', '--version'],
                capture_output=True,
                check=True,
                timeout=10
            )
            print("✅ pip可用")
        except Exception as e:
            print(f"❌ pip不可用: {e}")
        
        print()
    
    def check_dependencies(self):
        """检查依赖包"""
        print("=" * 70)
        print("3. 依赖包检查")
        print("=" * 70)
        
        required_packages = {
            'flask': 'Flask',
            'requests': 'Requests',
            'werkzeug': 'Werkzeug'
        }
        
        for module_name, display_name in required_packages.items():
            try:
                __import__(module_name)
                print(f"✅ {display_name} 已安装")
                self.results["dependencies"][module_name] = True
            except ImportError:
                print(f"❌ {display_name} 未安装")
                self.results["dependencies"][module_name] = False
                # 尝试安装
                try:
                    print(f"   正在安装 {display_name}...")
                    subprocess.run(
                        [sys.executable, '-m', 'pip', 'install', module_name],
                        capture_output=True,
                        check=True,
                        timeout=60
                    )
                    print(f"   ✅ {display_name} 安装成功")
                    self.results["dependencies"][module_name] = True
                except Exception as e:
                    print(f"   ❌ {display_name} 安装失败: {e}")
        
        print()
    
    def check_configuration(self):
        """检查配置文件"""
        print("=" * 70)
        print("4. 配置文件检查")
        print("=" * 70)
        
        # 检查.env文件
        env_file = self.script_dir / ".env"
        if env_file.exists():
            print("✅ .env文件存在")
            self.results["configuration"]["env_file"] = True
            
            # 检查API密钥
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'OPENROUTER_API_KEY' in content:
                        print("✅ OPENROUTER_API_KEY已配置")
                        self.results["configuration"]["api_key"] = True
                    else:
                        print("❌ OPENROUTER_API_KEY未配置")
                        self.results["configuration"]["api_key"] = False
            except Exception as e:
                print(f"❌ 读取.env文件失败: {e}")
        else:
            print("❌ .env文件不存在")
            self.results["configuration"]["env_file"] = False
            self.results["configuration"]["api_key"] = False
        
        # 检查缓存目录
        cache_dir = os.getenv('CACHE_DIR', 'R:\\api_proxy_cache')
        try:
            if os.path.exists(cache_dir):
                print(f"✅ 缓存目录存在: {cache_dir}")
                self.results["configuration"]["cache_dir"] = True
            else:
                print(f"⚠️  缓存目录不存在: {cache_dir}")
                self.results["configuration"]["cache_dir"] = False
        except Exception as e:
            print(f"⚠️  无法检查缓存目录: {e}")
        
        print()
    
    def check_network(self):
        """检查网络连接"""
        print("=" * 70)
        print("5. 网络连接检查")
        print("=" * 70)
        
        # 检查端口5000
        port = 5000
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"⚠️  端口{port}已被占用")
            self.results["network"]["port_5000"] = "occupied"
        else:
            print(f"✅ 端口{port}空闲")
            self.results["network"]["port_5000"] = "free"
        
        # 检查网络连接
        try:
            import requests
            response = requests.get('https://www.google.com', timeout=10)
            if response.status_code == 200:
                print("✅ 网络连接正常")
                self.results["network"]["internet"] = True
            else:
                print("⚠️  网络连接异常")
                self.results["network"]["internet"] = False
        except Exception as e:
            print(f"⚠️  网络连接检查失败: {e}")
            self.results["network"]["internet"] = False
        
        print()
    
    def check_service_files(self):
        """检查服务文件"""
        print("=" * 70)
        print("6. 服务文件检查")
        print("=" * 70)
        
        required_files = [
            "minimal_server_proxy.py",
            "a10-minimal_setup.bat",
            "a20-monitor_service.bat",
            "a21-safe_start.bat",
            "a22-start_minimal.bat"
        ]
        
        for filename in required_files:
            file_path = self.win2012_dir / filename
            if file_path.exists():
                print(f"✅ {filename} 存在")
                self.results["service"][filename] = True
            else:
                print(f"❌ {filename} 不存在")
                self.results["service"][filename] = False
        
        print()
    
    def test_service_startup(self):
        """测试服务启动"""
        print("=" * 70)
        print("7. 服务启动测试")
        print("=" * 70)
        
        proxy_script = self.win2012_dir / "minimal_server_proxy.py"
        if not proxy_script.exists():
            print("❌ minimal_server_proxy.py 不存在，无法测试")
            return
        
        print("正在启动服务...")
        try:
            process = subprocess.Popen(
                [sys.executable, str(proxy_script)],
                cwd=self.win2012_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待服务启动
            import time
            time.sleep(5)
            
            # 检查端口
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', 5000))
            sock.close()
            
            if result == 0:
                print("✅ 服务启动成功，端口5000已监听")
                self.results["service"]["startup"] = True
                
                # 测试健康检查
                try:
                    import requests
                    response = requests.get('http://localhost:5000/health', timeout=5)
                    if response.status_code == 200:
                        print("✅ 健康检查通过")
                        self.results["service"]["health_check"] = True
                    else:
                        print(f"⚠️  健康检查失败: {response.status_code}")
                        self.results["service"]["health_check"] = False
                except Exception as e:
                    print(f"⚠️  健康检查失败: {e}")
                    self.results["service"]["health_check"] = False
            else:
                print("❌ 服务启动失败，端口5000未监听")
                self.results["service"]["startup"] = False
            
            # 停止服务
            process.terminate()
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ 服务启动测试失败: {e}")
            self.results["service"]["startup"] = False
        
        print()
    
    def generate_report(self):
        """生成诊断报告"""
        print("=" * 70)
        print("诊断报告")
        print("=" * 70)
        
        # 保存报告到文件
        report_file = self.script_dir / "server_diagnostic_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 详细报告已保存到: {report_file}")
        print()
        
        # 总结
        print("=" * 70)
        print("问题总结和建议")
        print("=" * 70)
        
        issues = []
        
        if not all(self.results["dependencies"].values()):
            issues.append("部分依赖包未安装")
        
        if not self.results["configuration"].get("api_key", False):
            issues.append("OPENROUTER_API_KEY未配置")
        
        if not all(self.results["service"].values()):
            issues.append("部分服务文件缺失")
        
        if not self.results["service"].get("startup", False):
            issues.append("服务启动失败")
        
        if issues:
            print("发现以下问题:")
            for i, issue in enumerate(issues, 1):
                print(f"{i}. {issue}")
            print()
            print("建议:")
            print("1. 确保所有依赖包已安装")
            print("2. 检查.env文件配置")
            print("3. 查看详细报告了解具体问题")
            print("4. 参考scenarios/win2012-server/README.md进行配置")
        else:
            print("✅ 所有检查通过，系统配置正常")
        
        print()
    
    def run_all_checks(self):
        """运行所有检查"""
        print("\n" + "=" * 70)
        print("服务器环境诊断工具")
        print("专为 Windows Server 2012 R2 设计")
        print("=" * 70)
        print()
        
        self.check_system_info()
        self.check_python_environment()
        self.check_dependencies()
        self.check_configuration()
        self.check_network()
        self.check_service_files()
        self.test_service_startup()
        self.generate_report()
        
        print("=" * 70)
        print("诊断完成")
        print("=" * 70)

def main():
    try:
        diagnostic = ServerDiagnostic()
        diagnostic.run_all_checks()
        return 0
    except KeyboardInterrupt:
        print("\n\n⚠️  诊断被用户中断")
        return 1
    except Exception as e:
        print(f"\n\n❌ 诊断过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
