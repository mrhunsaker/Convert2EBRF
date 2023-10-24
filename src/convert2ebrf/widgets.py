from collections.abc import Callable

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QWidget, QLineEdit, QPushButton, QHBoxLayout
# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property


class FilePickerWidget(QWidget):
    fileChanged = Signal(str)

    def __init__(self, browse_func: Callable[[QWidget], str], parent: QObject = None):
        super().__init__(parent)
        self._browse_func = browse_func
        file_name_edit = QLineEdit()
        file_name_edit.read_only = True
        browse_button = QPushButton("Browse...")
        browse_button.auto_default = False
        browse_button.default = False
        layout = QHBoxLayout(self)
        layout.add_widget(file_name_edit)
        layout.add_widget(browse_button)
        browse_button.clicked.connect(self._browse_clicked)
        file_name_edit.textChanged.connect(lambda x: self.fileChanged.emit(x))
        self._file_name_edit = file_name_edit

    @Slot()
    def _browse_clicked(self):
        directory = self._browse_func(self)
        if directory:
            self._file_name_edit.text = directory

    @property
    def file_name(self) -> str:
        return self._file_name_edit.text

    @file_name.setter
    def file_name(self, value: str):
        self._file_name_edit.text = value
