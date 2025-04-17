import os
import shutil
from typing import Tuple
from PyQt5.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFileDialog,
                             QMessageBox, QProgressDialog, QLineEdit, QSpacerItem, QSizePolicy, QTableWidget,
                             QTableWidgetItem)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import ollama


class OllamaSetting:
    def __init__(self, logger, app_root):
        self.logger = logger
        self.app_root = app_root

    # Function to move files from old directory to new directory with progress indication
    def move_files(self, old_dir, new_dir):
        files = os.listdir(old_dir)
        total_files = len(files)
        progress_dialog = QProgressDialog("Moving files...", "Cancel", 0, total_files)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.show()

        for i, file in enumerate(files):
            old_file_path = os.path.join(old_dir, file)
            new_file_path = os.path.join(new_dir, file)
            try:
                shutil.move(old_file_path, new_file_path)
            except Exception as e:
                self.logger.error(f"Error in moving file {file}: {e}")
            progress_dialog.setValue(i + 1)
            QApplication.processEvents()
            if progress_dialog.wasCanceled():
                break

        progress_dialog.close()

    # Function to save the Ollama model location
    def save_ollama_settings(self, location, window, line_edit):
        old_location = os.getenv('OLLAMA_MODELS', '')
        if old_location and old_location != location:
            reply = QMessageBox.question(window, 'Confirm Move',
                                         f"Are you sure you want to move all files from {old_location} to {location}?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                if not os.path.exists(location):
                    os.makedirs(location)
                self.move_files(old_location, location)
        os.environ['OLLAMA_MODELS'] = location
        self.logger.info(f"Ollama model location updated to: {location}")
        line_edit.setText(location)

    # Function to open the directory picker dialog
    def pick_directory(self, window, line_edit):
        directory = QFileDialog.getExistingDirectory(window, "Select Directory")
        if directory:
            self.save_ollama_settings(directory, window, line_edit)

    def get_ollama_models(self):
        modlist = ollama.list()
        return modlist.models

    # Function to open the Ollama settings window
    def open_ollama_settings(self):
        settings_window = QWidget()
        settings_window.setWindowTitle("Ollama Settings")
        # Remove the close/maximize/minimize button hint
        settings_window.setWindowFlags(settings_window.windowFlags() & ~Qt.WindowCloseButtonHint)
        settings_window.setWindowFlags(settings_window.windowFlags() & ~Qt.WindowMaximizeButtonHint)
        settings_window.setWindowFlags(settings_window.windowFlags() & ~Qt.WindowMinimizeButtonHint)

        # Set the window icon
        icon_path = os.path.join(self.app_root, "resources", "ollama.png")
        if os.path.exists(icon_path):
            settings_window.setWindowIcon(QIcon(icon_path))
        else:
            self.logger.warning(f"Icon file {icon_path} not found. Using default icon.")

        main_layout = QVBoxLayout()

        # Create a horizontal layout for the textbox and button
        h_layout = QHBoxLayout()
        h_layout.setSpacing(5)

        # Label for Ollama model location
        label = QLabel("Models Location:")
        h_layout.addWidget(label, alignment=Qt.AlignLeft)

        # Readonly textbox
        line_edit = QLineEdit()
        line_edit.setReadOnly(True)
        current_location = os.getenv('OLLAMA_MODELS', '')
        line_edit.setText(current_location)
        line_edit.setStyleSheet("padding-top: 5px; padding-bottom: 5px; padding-left: 2px;")
        h_layout.addWidget(line_edit, stretch=10)

        # Directory picker button
        pick_button = QPushButton("...")
        pick_button.clicked.connect(lambda x: self.pick_directory(settings_window, line_edit))
        pick_button.setStyleSheet("padding: 5px 5px;")
        h_layout.addWidget(pick_button, stretch=1, alignment=Qt.AlignRight)

        # Add the horizontal layout to the main vertical layout
        main_layout.addLayout(h_layout)

        # # Add a vertical spacer to increase the space
        # spacer = QSpacerItem(5, 5, QSizePolicy.Minimum, QSizePolicy.Expanding)
        # main_layout.addItem(spacer)

        label = QLabel("Downloaded Ollama Models:")
        main_layout.addWidget(label, alignment=Qt.AlignLeft)

        # Table to list all models
        table = QTableWidget()
        titles = ["Name", "Families", "Para#", "Size"]  #, "Quantization", "Format"
        table.setColumnCount(len(titles))
        table.setHorizontalHeaderLabels(titles)
        models = self.get_ollama_models()
        table.setRowCount(len(models))
        table_width = table.size().width()
        table.setColumnWidth(0, int(table_width * 0.5))
        table.setColumnWidth(1, int(table_width * 0.2))
        table.setColumnWidth(2, int(table_width * 0.16))
        table.setColumnWidth(3, int(table_width * 0.16))
        # Set the background color for the table header row
        header = table.horizontalHeader()
        header.setStyleSheet("QHeaderView::section { background-color: lightblue; }")

        for i, model in enumerate(models):
            model_name_item = QTableWidgetItem(model.model)
            model_family_item = QTableWidgetItem(','.join(model.details.families) if model.details.families else '')
            model_parasize_item = QTableWidgetItem(model.details.parameter_size)
            try:
                # Convert bytes to megabytes
                n,u = self.bytes_to_gb(model.size)
                model_bytesize_str = "{:.2f} {}".format(n, u)
                model_bytesize_item = QTableWidgetItem(model_bytesize_str)
            except AttributeError:
                self.logger.error(f"Model {model.model} does not have a valid size attribute.")
                model_bytesize_item = QTableWidgetItem("N/A")
            # model_quant_item = QTableWidgetItem(model.details.quantization_level)
            # model_format_item = QTableWidgetItem(model.details.format)
            table.setItem(i, 0, model_name_item)
            table.setItem(i, 1, model_family_item)
            table.setItem(i, 2, model_parasize_item)
            table.setItem(i, 3, model_bytesize_item)
        main_layout.addWidget(table)

        # Close button in the bottom-right corner
        close_button = QPushButton("Close")
        close_button.clicked.connect(settings_window.hide)  # Use hide instead of close
        main_layout.addWidget(close_button, alignment=Qt.AlignRight)

        settings_window.setLayout(main_layout)
        settings_window.setFixedSize(800, 600)
        settings_window.show()

    def bytes_to_gb(self, bytes_size)->Tuple[float, str]:
        ret = (0, 'B')
        try:
            # Convert bytes to megabytes
            granularity = ['B','K','M','G']
            result = float(bytes_size)
            r = (bytes_size, granularity[0])
            for u in granularity[1:]:
                if result > 1.0:
                    result /= 1024
                    r = (result, u)
                else:
                    break
            ret = r
        except ValueError:
            self.logger.error(f"Invalid byte size value: {bytes_size}")
        return ret