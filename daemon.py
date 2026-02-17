import os
import sys
import time
import signal
import subprocess
import threading
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_SCRIPT = os.path.join(SCRIPT_DIR, "local_api_proxy.py")

# 读取 CACHE_DIR 环境变量，如果未设置则使用 SCRIPT_DIR
CACHE_DIR = os.getenv("CACHE_DIR", SCRIPT_DIR)
LOG_FILE = os.path.join(CACHE_DIR, "daemon.log")
PID_FILE = os.path.join(CACHE_DIR, "daemon.pid")

MAX_RESTART_DELAY = 5
MAX_RESTART_COUNT = 10
RESTART_WINDOW = 60


def is_process_running(pid):
    """Check if process is running (cross-platform)"""
    try:
        process = subprocess.Popen(
            ['tasklist', '/FI', f'PID eq {pid}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        output, _ = process.communicate()
        return str(pid) in output
    except Exception:
        return False


class Daemon:
    def __init__(self):
        self.process = None
        self.restart_count = 0
        self.restart_times = []
        self.running = True
    
    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_message + "\n")
        except Exception:
            pass
    
    def write_pid(self):
        try:
            with open(PID_FILE, "w", encoding="utf-8") as f:
                f.write(str(os.getpid()))
        except Exception:
            pass
    
    def delete_pid(self):
        try:
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
        except Exception:
            pass
    
    def signal_handler(self, signum, frame):
        self.log(f"Received signal {signum}, stopping daemon...")
        self.running = False
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.delete_pid()
        sys.exit(0)
    
    def check_restart_limit(self):
        now = time.time()
        self.restart_times = [t for t in self.restart_times if now - t < RESTART_WINDOW]
        
        if len(self.restart_times) >= MAX_RESTART_COUNT:
            self.log(f"Restart limit exceeded ({MAX_RESTART_COUNT}/{RESTART_WINDOW}s), stopping daemon")
            return False
        
        return True
    
    def start_process(self):
        self.log("Starting main program...")
        
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["DAEMON_CHILD"] = "1"
        
        self.process = subprocess.Popen(
            [sys.executable, MAIN_SCRIPT],
            cwd=SCRIPT_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        self.output_thread = threading.Thread(target=self.read_output, daemon=True)
        self.output_thread.start()
        
        self.log(f"Main program started (PID: {self.process.pid})")
        return self.process
    
    def read_output(self):
        if self.process and self.process.stdout:
            for line in self.process.stdout:
                if line:
                    print(f"[API] {line.rstrip()}")
    
    def monitor(self):
        self.start_process()
        
        while self.running:
            time.sleep(1)
            
            if self.process.poll() is not None:
                exit_code = self.process.returncode
                
                if exit_code == 0:
                    self.log("Main program exited normally")
                    break
                
                self.log(f"Main program crashed (exit code: {exit_code})")
                
                self.restart_count += 1
                self.restart_times.append(time.time())
                
                if not self.check_restart_limit():
                    break
                
                delay = min(MAX_RESTART_DELAY, self.restart_count)
                self.log(f"Restarting in {delay}s... (attempt {self.restart_count})")
                time.sleep(delay)
                
                if not self.running:
                    break
                
                self.start_process()
        
        self.delete_pid()
        self.log("Daemon stopped")
    
    def run(self):
        # 确保 CACHE_DIR 目录存在
        if not os.path.exists(CACHE_DIR):
            try:
                os.makedirs(CACHE_DIR, exist_ok=True)
                self.log(f"Created cache directory: {CACHE_DIR}")
            except Exception as e:
                self.log(f"Failed to create cache directory: {e}")
                sys.exit(1)
        
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, "r") as f:
                    old_pid = int(f.read().strip())
                if is_process_running(old_pid):
                    print(f"Daemon already running (PID: {old_pid})")
                    sys.exit(1)
            except (ValueError, ProcessLookupError, PermissionError):
                self.delete_pid()
        
        self.write_pid()
        
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        if sys.platform == "win32":
            signal.signal(signal.SIGBREAK, self.signal_handler)
        
        self.log("=" * 50)
        self.log("Daemon starting")
        self.log(f"Working directory: {SCRIPT_DIR}")
        self.log(f"Main script: {MAIN_SCRIPT}")
        self.log(f"Cache directory: {CACHE_DIR}")
        self.log(f"Log file: {LOG_FILE}")
        self.log(f"PID file: {PID_FILE}")
        self.log("=" * 50)
        
        self.monitor()


def status():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            if is_process_running(pid):
                print(f"Daemon is running (PID: {pid})")
                return True
            else:
                print("PID file exists but process not running")
                return False
        except (ValueError, ProcessLookupError, PermissionError):
            print("PID file exists but process not running")
            return False
    else:
        print("Daemon not running")
        return False


def stop():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            subprocess.run(['taskkill', '/PID', str(pid), '/T', '/F'], check=True)
            print(f"Daemon stopped (PID: {pid})")
            return True
        except Exception as e:
            print(f"Stop failed: {e}")
            return False
    else:
        print("Daemon not running")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "start":
            daemon = Daemon()
            daemon.run()
        elif command == "stop":
            stop()
        elif command == "status":
            status()
        elif command == "restart":
            if stop():
                time.sleep(2)
                daemon = Daemon()
                daemon.run()
        else:
            print("Usage: python daemon.py [start|stop|status|restart]")
    else:
        daemon = Daemon()
        daemon.run()
