
from PyQt5.QtWidgets import QDialog,QLineEdit, QListWidget, QAbstractItemView, QDesktopWidget, QVBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal
from file_types_module import *
class DirectoryAndFileTypesDialog(QDialog):
    directory_and_file_types_selected = pyqtSignal(str, list)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.directory_line_edit = QLineEdit()
        self.layout.addWidget(self.directory_line_edit)

        self.file_types_list_widget = QListWidget()
        self.file_types_list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.file_types_list_widget.addItems(file_types)  # Add your file types here
        self.layout.addWidget(self.file_types_list_widget)

        self.ok_button = QPushButton('OK')
        self.ok_button.clicked.connect(self.on_ok_clicked)
        self.layout.addWidget(self.ok_button)

    def on_ok_clicked(self):
        directory = self.directory_line_edit.text()
        selected_file_types = [item.text() for item in self.file_types_list_widget.selectedItems()]
        self.directory_and_file_types_selected.emit(directory, selected_file_types)
