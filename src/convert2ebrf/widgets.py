#  Copyright (c) 2024. American Printing House for the Blind.
#
# This file is part of Convert2EBRF.
# Convert2EBRF is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# Convert2EBRF is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with Convert2EBRF. If not, see <https://www.gnu.org/licenses/>.

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
        file_name_edit.minimum_width = 400
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
