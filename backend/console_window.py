from PyQt5.QtWidgets import QTextEdit, QWidget, QVBoxLayout, QPushButton
from PyQt5.QtCore import QMetaType, pyqtSignal
from PyQt5.QtGui import QTextCursor
import threading

# 注册 QTextCursor 类型
if QMetaType.type(QTextCursor.__name__) == 'QMetaType.UnknownType':
    QMetaType.registerNativeMetaType(QTextCursor.__name__, QTextCursor)
print(f'QTextCursor type Id: {QMetaType.type(QTextCursor.__name__)}')


# Create a custom console window class
class CustomConsole(QWidget):
    # Define a new signal to be emitted when the visibility changes
    visibilityChanged = pyqtSignal(bool)

    def __init__(self, title: str):
        super().__init__()
        self.initUI(title)

    def initUI(self, title):
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

        # Set the window properties
        self.setWindowTitle(title)
        self.setGeometry(100, 100, 1200, 800)

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

    def append_text(self, text):
        if text.endswith('\n'):
            text = text[:-1]
        self.text_edit.append(text)

# Custom console writer class
class CustomConsoleWriter:
    def __init__(self, console, logger):
        self.console = console
        self.logger = logger
        self.lock = threading.Lock()

    def write(self, text):
        with self.lock:
            try:
                self.console.append_text(text)
            except Exception as e:
                self.logger.error(f"Failed in writing to console: {repr(e)}")

    def flush(self):
        pass

    def isatty(self):
        return False
