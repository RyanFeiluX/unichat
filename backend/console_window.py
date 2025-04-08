import os
from PyQt5.QtWidgets import QApplication, QTextEdit, QWidget, QVBoxLayout, QPushButton
from PyQt5.QtCore import QMetaType, pyqtSignal
from PyQt5.QtGui import QTextCursor, QIcon
import threading
from logging_config import setup_logging
from http_server import app_root

# Configure logging
logger = setup_logging(logfile=os.path.join(app_root, 'run.log'))

# 注册 QTextCursor 类型
if QMetaType.type(QTextCursor.__name__) == 'QMetaType.UnknownType':
    QMetaType.registerNativeMetaType(QTextCursor.__name__, QTextCursor)
logger.info(f'QTextCursor type Id: {QMetaType.type(QTextCursor.__name__)}')


# Create a custom console window class
class CustomConsole(QWidget):
    # Define a new signal to be emitted when the visibility changes
    visibilityChanged = pyqtSignal(bool)

    def __init__(self, title: str):
        super().__init__()
        logger.info(f"Initializing custom console with title: {title}")
        # Set the window icon
        icon_path = os.path.join(app_root, "resources", "icon3.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            logger.warning(f"Icon file {icon_path} not found. Using default icon.")
        self.initUI(title)

    def initUI(self, title):
        logger.info("Initializing UI for custom console")
        # Create a QTextEdit widget to display the output
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)

        # Create a button to toggle the window's visibility
        self.toggle_button = QPushButton('Hide Console', self)
        self.toggle_button.clicked.connect(self.toggle_visibility)

        # Create a layout and add the widgets
        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        layout.addWidget(self.toggle_button)

        # Set the layout for the window
        self.setLayout(layout)

        # Get the screen geometry
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        # Set the window size as a percentage of the screen size
        width_percentage = 0.6  # 60% of the screen width
        height_percentage = 0.6  # 60% of the screen height
        window_width = int(screen_width * width_percentage)
        window_height = int(screen_height * height_percentage)

        # Set the window position to the center of the screen
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        # Set the window properties
        self.setWindowTitle(title)
        self.setGeometry(x, y, window_width, window_height)

        logger.info("UI initialization for custom console completed")

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
            self.toggle_button.setText('Show Console')
        else:
            self.show()
            self.toggle_button.setText('Hide Console')

        # Emit the signal with the current visibility status
        self.visibilityChanged.emit(self.isVisible())

        return self.isVisible()

    def append_text(self, text: str):
        if text is None or len(text) == 0:
            logger.warning(f'Ignore null/empty log.')
            return
        self.text_edit.insertPlainText(text)
        logger.debug(f"Appended text to console: {text[:min(50,len(text))]}")

    def get_text_edit(self):
        return self.text_edit

# Custom console writer class
class CustomConsoleWriter:
    def __init__(self, console, logger):
        logger.info("Initializing custom console writer")
        self.console = console
        self.logger = logger
        self.lock = threading.Lock()

    def write(self, text):
        with self.lock:
            try:
                self.console.append_text(text)
                logger.debug(f"Successfully wrote text to console: {text[:min(50,len(text))]}")
            except Exception as e:
                self.logger.error(f"Failed in writing to console: {repr(e)}")

    def flush(self):
        logger.debug("Flushing custom console writer")
        pass

    def isatty(self):
        return False
