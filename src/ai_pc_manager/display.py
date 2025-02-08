import os
import sys
import time
import threading
from contextlib import contextmanager

class WaitingSpinner:
    """等待动画和计时器"""
    def __init__(self):
        self.spinning = False
        self.spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        self.spinner_idx = 0
        self.start_time = 0
        self.thread = None

        self.provider = None

    def _spin(self):
        while self.spinning:
            elapsed = time.time() - self.start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)

            sys.stdout.write(f"\r正在等待AI响应 {self.spinner_chars[self.spinner_idx]} ({minutes:02d}:{seconds:02d}) ")
            sys.stdout.flush()

            self.spinner_idx = (self.spinner_idx + 1) % len(self.spinner_chars)
            time.sleep(0.1)

    def start(self):
        """开始显示等待动画"""
        self.spinning = True
        self.start_time = time.time()
        self.thread = threading.Thread(target=self._spin)
        self.thread.start()

    def stop(self):
        """停止显示等待动画"""
        self.spinning = False
        if self.thread:
            self.thread.join()
        elapsed = time.time() - self.start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        provider_info = f" [{self.provider}]" if self.provider else ""
        sys.stdout.write(f"\rAI响应完成{provider_info} ✓ (用时 {minutes:02d}:{seconds:02d})\n")
        sys.stdout.flush()

    def set_provider(self, provider: str):
        """设置提供者信息"""
        self.provider = provider

@contextmanager
def show_waiting_spinner():
    """上下文管理器，用于显示等待动画"""
    spinner = WaitingSpinner()
    spinner.start()
    try:
        yield spinner
    finally:
        spinner.stop()

def print_command_execution(command: str, output: str, return_code: int):
    """以指定格式打印命令执行过程"""
    current_path = os.getcwd()
    print(f"\nai-pc-manage:{current_path}# {command}")
    print(f"(return code: {return_code})")
    print(output)