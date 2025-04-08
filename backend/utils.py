import os
import psutil

def running_in_pycharm():
    try:
        current_process = psutil.Process(os.getpid())
        parent_process = current_process.parent()
        if parent_process:
            parent_name = parent_process.name()
            # PyCharm 在不同操作系统上的进程名可能不同
            if 'pycharm' in parent_name.lower():
                return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass
    return False

def pycharm_hosted():
    return bool(os.getenv('PYCHARM_HOSTED'))

if running_in_pycharm():
    print("应用程序正在 PyCharm 的终端中运行。")
else:
    print("应用程序正在其他终端中运行。")