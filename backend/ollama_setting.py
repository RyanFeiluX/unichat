import os
import shutil
from PyQt5.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFileDialog,
                             QMessageBox, QProgressDialog, QLineEdit, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt


class OllamaSetting:
    def __init__(self, logger):
        self.logger = logger

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

    # Function to open the Ollama settings window
    def open_ollama_settings(self):
        settings_window = QWidget()
        settings_window.setWindowTitle("Ollama Settings")
        # Remove the close/maximize/minimize button hint
        settings_window.setWindowFlags(settings_window.windowFlags() & ~Qt.WindowCloseButtonHint)
        settings_window.setWindowFlags(settings_window.windowFlags() & ~Qt.WindowMaximizeButtonHint)
        settings_window.setWindowFlags(settings_window.windowFlags() & ~Qt.WindowMinimizeButtonHint)

        main_layout = QVBoxLayout()

        # Label for Ollama model location
        label = QLabel("Models Location:")
        main_layout.addWidget(label)

        # Create a horizontal layout for the textbox and button
        h_layout = QHBoxLayout()
        h_layout.setSpacing(5)

        # Readonly textbox
        line_edit = QLineEdit()
        line_edit.setReadOnly(True)
        current_location = os.getenv('OLLAMA_MODELS', '')
        line_edit.setText(current_location)
        line_edit.setStyleSheet("padding-top: 5px; padding-bottom: 5px; padding-left: 2px;")
        h_layout.addWidget(line_edit, stretch=10, alignment=Qt.AlignLeft)

        # Directory picker button
        pick_button = QPushButton("...")
        pick_button.clicked.connect(lambda x: self.pick_directory(settings_window, line_edit))
        pick_button.setStyleSheet("padding: 5px 5px;")
        h_layout.addWidget(pick_button, stretch=1, alignment=Qt.AlignRight)

        # Add the horizontal layout to the main vertical layout
        main_layout.addLayout(h_layout)

        # Add a vertical spacer to increase the space
        spacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        main_layout.addItem(spacer)

        # Close button in the bottom-right corner
        close_button = QPushButton("Close")
        close_button.clicked.connect(settings_window.hide)  # Use hide instead of close
        main_layout.addWidget(close_button, alignment=Qt.AlignRight)

        settings_window.setLayout(main_layout)
        settings_window.setFixedSize(600, 300)
        settings_window.show()
