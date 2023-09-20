from PySide6.QtCore import QObject
from PySide6.QtWidgets import QWidget, QFormLayout, QLineEdit
# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property


class Brf2EbrfWidget(QWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        layout = QFormLayout(self)
        layout.add_row("Input BRF", QLineEdit(self))
        layout.add_row("Output EBRF", QLineEdit(self))
        self.layout = layout
