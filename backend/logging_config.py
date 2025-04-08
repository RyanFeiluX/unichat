import sys
import logging
from PyQt5.QtWidgets import QTextEdit, QWidget

logger = None

# Set default encoding to utf-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


class CustomStream:
    def __init__(self, text_widget: QTextEdit):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.insertPlainText(message)
        # 移动光标到文档末尾
        cursor = self.text_widget.textCursor()
        cursor.movePosition(cursor.End)
        self.text_widget.setTextCursor(cursor)
        # 确保光标可见，即滚动到最新内容
        self.text_widget.ensureCursorVisible()
        # Force a refresh of the widget
        self.text_widget.repaint()

    def flush(self):
        pass  # 无缓冲操作


def setup_logging(logfile: str = None, tostream: bool = True, iostream = None):
    global logger
    if logger:
        logger.info(f'Logging object has already been created.')
        return logger

    print(f'About to create logging object...', flush=True)

    # Create a logger
    logger = logging.getLogger('shared_logger')
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    if logfile:
        # Create a file handler
        file_handler = logging.FileHandler(logfile)
        file_handler.setLevel(logging.INFO)

        # Create a formatter and add it to the handler
        file_handler.setFormatter(formatter)

        file_handler.encoding = 'utf-8'

        # Add the handler to the logger
        logger.addHandler(file_handler)

    if tostream:
        # Create a stream handler to print logs to the console
        stream_handler = logging.StreamHandler(iostream) if iostream else logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(formatter)
        stream_handler.encoding = 'utf-8'

        # Add the stream handler to the logger
        logger.addHandler(stream_handler)

    if logger.hasHandlers():
        logger.info(f'Logging object is created successfully.')
    else:
        logger.warning(f'No approach is specified to gather logs.')
    return logger

def redirect_stream(logger, new_stream):
    sindex = -1
    for index in range(len(logger.handlers)-1, 0, -1):
        if isinstance(logger.handlers[index], logging.StreamHandler):
            sindex = index
            break
    if sindex < 0:
        logger.warning(f'No stream handler exists.')
    else:
        new_handler = logging.StreamHandler(new_stream)
        new_handler.setLevel(logger.handlers[sindex].level)
        new_handler.setFormatter(logger.handlers[sindex].formatter)
        new_handler.encoding = logger.handlers[sindex].encoding
        logger.removeHandler(logger.handlers[sindex])
        logger.addHandler(new_handler)
