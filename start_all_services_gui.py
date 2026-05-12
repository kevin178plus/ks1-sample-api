"""
多Free API代理服务 - GUI启动器
在一个窗口中显示三个服务的输出
"""

import os
import sys
import subprocess
import threading
import time
import json
from pathlib import Path
from tkinter import ttk, scrolledtext, Tk, StringVar, messagebox
import tkinter as tk

CONFIG_FILE = "gui_config.json"


class ServiceManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("多Free API代理服务 - 启动器")
        self.root.geometry("1000x700")

        self.processes = {}
        self.running = False
        self.is_minimized = False

        self.load_config()

        # 检查调试模式文件是否存在
        self.debug_mode = tk.BooleanVar(value=self.check_debug_mode_file())
        self.max_lines = 1000
        self.output_buffers = {
            "free8": [],
            "main": []
        }

        self.root.bind('<Unmap>', self.on_minimize)
        self.root.bind('<Map>', self.on_restore)

        self.create_widgets()

    def load_config(self):
        config_path = Path(__file__).parent / CONFIG_FILE
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "free8": {"auto_start": True}
            }
            self.save_config()

    def save_config(self):
        config_path = Path(__file__).parent / CONFIG_FILE
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def check_debug_mode_file(self):
        """检查调试模式文件是否存在（检查主服务目录）"""
        debug_file = Path(__file__).parent / "multi_free_api_proxy" / "DEBUG_MODE.txt"
        return debug_file.exists()

    def toggle_debug_mode(self):
        """切换调试模式（在主服务目录创建/删除文件）"""
        debug_file = Path(__file__).parent / "multi_free_api_proxy" / "DEBUG_MODE.txt"
        if self.debug_mode.get():
            # 启用调试模式，创建文件
            debug_file.parent.mkdir(parents=True, exist_ok=True)
            debug_file.touch()
            self.append_output("main", "[调试模式] 已启用调试模式", "info")
            self.append_output("free8", "[调试模式] 已启用调试模式", "info")
        else:
            # 禁用调试模式，删除文件
            if debug_file.exists():
                debug_file.unlink()
            self.append_output("main", "[调试模式] 已禁用调试模式", "info")
            self.append_output("free8", "[调试模式] 已禁用调试模式", "info")

    def create_widgets(self):
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)

        self.status_label = ttk.Label(control_frame, text="状态: 未启动", font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.LEFT, padx=5)

        self.start_button = ttk.Button(control_frame, text="启动所有服务", command=self.start_all_services)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(control_frame, text="停止所有服务", command=self.stop_all_services, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        service_control_frame = ttk.Frame(control_frame)
        service_control_frame.pack(side=tk.LEFT, padx=20)

        self.free8_enabled = tk.BooleanVar(value=self.config.get("free8", {}).get("auto_start", True))

        ttk.Label(service_control_frame, text="服务控制:").pack(side=tk.LEFT, padx=5)

        free8_check = ttk.Checkbutton(
            service_control_frame,
            text="Free8",
            variable=self.free8_enabled,
            command=self.on_free8_toggle
        )
        free8_check.pack(side=tk.LEFT, padx=5)

        # 调试模式开关
        debug_control_frame = ttk.Frame(control_frame)
        debug_control_frame.pack(side=tk.LEFT, padx=20)

        ttk.Label(debug_control_frame, text="调试模式:").pack(side=tk.LEFT, padx=5)

        debug_check = ttk.Checkbutton(
            debug_control_frame,
            text="启用",
            variable=self.debug_mode,
            command=self.toggle_debug_mode
        )
        debug_check.pack(side=tk.LEFT, padx=5)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.create_service_tab("free8", "Free8 服务 (端口 5008)")
        self.create_service_tab("main", "主服务 (端口 5000 - 优化版)")

    def on_free8_toggle(self):
        self.config["free8"] = {"auto_start": self.free8_enabled.get()}
        self.save_config()
        
        if not self.free8_enabled.get() and "free8" in self.processes:
            self.stop_service("free8")

    def stop_service(self, service_id):
        """停止单个服务"""
        if service_id in self.processes:
            process = self.processes[service_id]
            try:
                self.append_output(service_id, "[停止] 正在停止服务...", "warning")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.append_output(service_id, "[停止] 强制终止进程...", "error")
                    process.kill()
                    process.wait()
                del self.processes[service_id]
                self.update_service_status(service_id, "已停止", "gray")
            except Exception as e:
                self.append_output(service_id, f"[错误] 停止失败: {str(e)}", "error")

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
        python_path = sys.executable

        if self.free8_enabled.get():
            self.append_output("free8", "=" * 50, "info")
            self.append_output("free8", "正在启动 Free8 服务...", "info")
            free8_cmd = [python_path, "friendli_service.py"]
            free8_dir = script_dir / "free_api_test" / "free8"
            self.start_service("free8", free8_cmd, free8_dir)
            time.sleep(2)
        else:
            self.append_output("free8", "=" * 50, "info")
            self.append_output("free8", "已禁用，跳过启动", "info")
            self.update_service_status("free8", "已禁用", "gray")

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

    auto_start_services = []
    if app.free8_enabled.get():
        auto_start_services.append("free8")

    if auto_start_services:
        delay_ms = 3000
        root.after(delay_ms, app.start_all_services)

    root.mainloop()

if __name__ == "__main__":
    main()
