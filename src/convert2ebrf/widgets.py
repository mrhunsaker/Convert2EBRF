import pathlib

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QWidget, QLineEdit, QPushButton, QHBoxLayout, QFileDialog
# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property


class DirectoryPickerWidget(QWidget):
    directoryChanged = Signal(str)

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        directory_name_edit = QLineEdit()
        directory_name_edit.read_only = True
        browse_button = QPushButton("Browse...")
        layout = QHBoxLayout(self)
        layout.add_widget(directory_name_edit)
        layout.add_widget(browse_button)
        browse_button.clicked.connect(self._browse_clicked)
        directory_name_edit.textChanged.connect(lambda x: self.directoryChanged.emit(x))
        self._directory_name_edit = directory_name_edit

    @Slot()
    def _browse_clicked(self):
        directory = QFileDialog.get_existing_directory(parent=self, caption="Select file",
                                                                            dir=str(pathlib.Path.home()))
        if directory:
            self._directory_name_edit.text = directory

    @property
    def directory_name(self) -> str:
        return self._directory_name_edit.text

    @directory_name.setter
    def directory_name(self, value: str):
        self._directory_name_edit.text = value
