import os
import psutil
import ollama

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

def check_model_avail(model_name):
    if not model_name:
        return False
    available_models = ollama.list()  # Get local model list
    model_names = [m.model for m in available_models.models]
    return model_name in model_names

