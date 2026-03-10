"""
多Free API代理服务 - GUI启动器
在一个窗口中显示三个服务的输出
"""

import os
import sys
import subprocess
import threading
import time
from pathlib import Path
from tkinter import ttk, scrolledtext, Tk, StringVar, messagebox
import tkinter as tk

class ServiceManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("多Free API代理服务 - 启动器")
        self.root.geometry("1000x700")

        self.processes = {}
        self.running = False
        self.is_minimized = False

        # 性能优化：最大行数限制和缓冲区
        self.max_lines = 1000  # 每个文本框最大行数
        self.output_buffers = {
            "free5": [],
            "free8": [],
            "main": []
        }

        # 监听窗口状态变化
        self.root.bind('<Unmap>', self.on_minimize)
        self.root.bind('<Map>', self.on_restore)

        self.create_widgets()

    def create_widgets(self):
        # 顶部控制栏
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)

        self.status_label = ttk.Label(control_frame, text="状态: 未启动", font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.LEFT, padx=5)

        self.start_button = ttk.Button(control_frame, text="启动所有服务", command=self.start_all_services)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(control_frame, text="停止所有服务", command=self.stop_all_services, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # 创建Tab控件
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建三个服务的Tab
        self.create_service_tab("free5", "Free5 服务 (端口 5005)")
        self.create_service_tab("free8", "Free8 服务 (端口 5008)")
        self.create_service_tab("main", "主服务 (端口 5000 - 优化版)")

    def create_service_tab(self, service_id, title):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=title)

        # 状态标签
        status_frame = ttk.Frame(frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(status_frame, text=f"{title} 输出:").pack(side=tk.LEFT)

        # 输出文本框
        text_widget = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=("Consolas", 9))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 配置文本颜色标签
        text_widget.tag_config("info", foreground="blue")
        text_widget.tag_config("error", foreground="red")
        text_widget.tag_config("success", foreground="green")
        text_widget.tag_config("warning", foreground="orange")

        # 保存引用
        if not hasattr(self, 'service_widgets'):
            self.service_widgets = {}
        self.service_widgets[service_id] = {
            'text_widget': text_widget,
            'status_label': ttk.Label(status_frame, text="未启动", foreground="gray")
        }
        self.service_widgets[service_id]['status_label'].pack(side=tk.LEFT, padx=10)

    def append_output(self, service_id, text, tag="info"):
        """向指定服务的文本框追加输出"""
        # 如果窗口最小化，将输出存入缓冲区
        if self.is_minimized:
            if service_id in self.output_buffers:
                self.output_buffers[service_id].append((text, tag))
                # 限制缓冲区大小，避免内存占用过高
                if len(self.output_buffers[service_id]) > self.max_lines:
                    self.output_buffers[service_id] = self.output_buffers[service_id][-self.max_lines:]
            return

        # 窗口可见时，直接更新文本框
        if service_id in self.service_widgets:
            text_widget = self.service_widgets[service_id]['text_widget']

            # 限制最大行数
            line_count = int(text_widget.index('end-1c').split('.')[0])
            if line_count >= self.max_lines:
                # 删除最早的行
                text_widget.delete(1.0, f"{line_count - self.max_lines + 100}.0")

            text_widget.insert(tk.END, text + "\n", tag)
            text_widget.see(tk.END)
            text_widget.update_idletasks()  # 使用 update_idletasks 代替 update，更高效

    def update_service_status(self, service_id, status, color="gray"):
        """更新服务状态"""
        if service_id in self.service_widgets:
            self.service_widgets[service_id]['status_label'].config(text=status, foreground=color)

    def start_service(self, service_id, command, working_dir):
        """启动单个服务"""
        try:
            self.append_output(service_id, f"[启动] 启动命令: {command}", "info")
            self.append_output(service_id, f"[启动] 工作目录: {working_dir}", "info")

            process = subprocess.Popen(
                command,
                cwd=working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='gbk',
                errors='replace',
                bufsize=1,
                universal_newlines=True
            )

            self.processes[service_id] = process
            self.update_service_status(service_id, "运行中", "green")

            # 启动输出读取线程
            thread = threading.Thread(target=self.read_output, args=(service_id, process))
            thread.daemon = True
            thread.start()

            return True
        except Exception as e:
            self.append_output(service_id, f"[错误] 启动失败: {str(e)}", "error")
            self.update_service_status(service_id, "启动失败", "red")
            return False

    def read_output(self, service_id, process):
        """读取进程输出"""
        try:
            for line in process.stdout:
                line = line.rstrip()
                if line:
                    # 根据内容判断类型
                    tag = "info"
                    if "[错误]" in line or "Error" in line or "error" in line:
                        tag = "error"
                    elif "[警告]" in line or "Warning" in line or "warning" in line:
                        tag = "warning"
                    elif "[成功]" in line or "Success" in line or "success" in line:
                        tag = "success"

                    self.append_output(service_id, line, tag)

            # 进程结束
            return_code = process.poll()
            if return_code is not None:
                self.append_output(service_id, f"[停止] 进程已退出，返回码: {return_code}", "warning")
                self.update_service_status(service_id, "已停止", "gray")
                if service_id in self.processes:
                    del self.processes[service_id]

        except Exception as e:
            self.append_output(service_id, f"[错误] 读取输出失败: {str(e)}", "error")

    def start_all_services(self):
        """启动所有服务"""
        if self.running:
            messagebox.showwarning("警告", "服务已在运行中")
            return

        script_dir = Path(__file__).parent

        # 获取Python路径
        python_path = sys.executable

        # 启动 free5
        self.append_output("free5", "=" * 50, "info")
        self.append_output("free5", "正在启动 Free5 服务...", "info")
        free5_cmd = [python_path, "iflow_api_proxy.py"]
        free5_dir = script_dir / "free_api_test" / "free5"
        self.start_service("free5", free5_cmd, free5_dir)

        # 等待
        time.sleep(2)

        # 启动 free8
        self.append_output("free8", "=" * 50, "info")
        self.append_output("free8", "正在启动 Free8 服务...", "info")
        free8_cmd = [python_path, "friendli_service.py"]
        free8_dir = script_dir / "free_api_test" / "free8"
        self.start_service("free8", free8_cmd, free8_dir)

        # 等待
        time.sleep(2)

        # 启动主服务
        self.append_output("main", "=" * 50, "info")
        self.append_output("main", "正在启动主服务 (优化版)...", "info")
        main_cmd = [python_path, "multi_free_api_proxy_v3_optimized.py"]
        main_dir = script_dir / "multi_free_api_proxy"
        self.start_service("main", main_cmd, main_dir)

        self.running = True
        self.status_label.config(text="状态: 运行中", foreground="green")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

    def stop_all_services(self):
        """停止所有服务"""
        for service_id, process in list(self.processes.items()):
            try:
                self.append_output(service_id, "[停止] 正在停止服务...", "warning")
                process.terminate()

                # 等待进程结束
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.append_output(service_id, "[停止] 强制终止进程...", "error")
                    process.kill()
                    process.wait()

                self.update_service_status(service_id, "已停止", "gray")
            except Exception as e:
                self.append_output(service_id, f"[错误] 停止失败: {str(e)}", "error")

        self.processes.clear()
        self.running = False
        self.status_label.config(text="状态: 已停止", foreground="gray")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def on_minimize(self, event):
        """窗口最小化时的处理"""
        self.is_minimized = True
        print("[优化] 窗口最小化，停止UI刷新")

    def on_restore(self, event):
        """窗口恢复时的处理"""
        self.is_minimized = False
        print("[优化] 窗口恢复，刷新缓冲区内容")

        # 恢复缓冲区的内容
        for service_id, buffer in self.output_buffers.items():
            if buffer and service_id in self.service_widgets:
                text_widget = self.service_widgets[service_id]['text_widget']

                # 批量插入缓冲区内容
                for text, tag in buffer:
                    line_count = int(text_widget.index('end-1c').split('.')[0])
                    if line_count >= self.max_lines:
                        text_widget.delete(1.0, f"{line_count - self.max_lines + 100}.0")
                    text_widget.insert(tk.END, text + "\n", tag)

                text_widget.see(tk.END)
                text_widget.update_idletasks()

                # 清空缓冲区
                self.output_buffers[service_id].clear()

    def on_closing(self):
        """窗口关闭时的处理"""
        self.is_minimized = True  # 停止UI刷新
        if self.running:
            if messagebox.askokcancel("退出", "服务正在运行，确定要退出吗？"):
                self.stop_all_services()
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    root = Tk()
    app = ServiceManagerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    # 延迟 3 秒后自动启动所有服务
    root.after(3000, app.start_all_services)
    root.mainloop()

if __name__ == "__main__":
    main()
