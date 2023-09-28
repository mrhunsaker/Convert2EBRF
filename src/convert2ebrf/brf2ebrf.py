from PySide6.QtCore import QObject
from PySide6.QtWidgets import QWidget, QFormLayout, QLineEdit, QCheckBox
# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property


class Brf2EbrfWidget(QWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        layout = QFormLayout(self)
        layout.add_row("Input BRF", QLineEdit(self))
        self.include_images_checkbox = QCheckBox(self)
        layout.add_row("Include images", self.include_images_checkbox)
        self.image_dir_edit = QLineEdit(self)
        layout.add_row("Image directory", self.image_dir_edit)
        layout.add_row("Output EBRF", QLineEdit(self))
        self.layout = layout
        self.update_include_images_state_changed()
        self.include_images_checkbox.stateChanged.connect(self.update_include_images_state_changed)

    def update_include_images_state_changed(self):
        self.image_dir_edit.enabled = self.include_images_checkbox.checked
