import time

from PySide6.QtCore import QObject, Slot, Signal, QThreadPool
from PySide6.QtWidgets import QWidget, QFormLayout, QLineEdit, QCheckBox, QDialog, QDialogButtonBox, QVBoxLayout, \
    QProgressDialog
from convert2ebrf.utils import RunnableAdapter
# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property


class ConvertTask(QObject):
    started = Signal()
    progress = Signal(int)
    finished = Signal()

    def __init__(self, parent: QObject = None):
        super().__init__(parent=parent)
        self._cancel_requested = False

    def __call__(self, input_brf: str, input_images: str | None, output_ebrf: str):
        self.started.emit()
        for i in range(20):
            print(f"Processing {i}")
            self.progress.emit(i)
            time.sleep(1)
            if self._cancel_requested:
                break
        self.finished.emit()

    def cancel(self):
        self._cancel_requested = True


class Brf2EbrfWidget(QWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        layout = QFormLayout()
        self._input_brf_edit = QLineEdit(self)
        layout.add_row("Input BRF", self._input_brf_edit)
        self._include_images_checkbox = QCheckBox(self)
        layout.add_row("Include images", self._include_images_checkbox)
        self._image_dir_edit = QLineEdit(self)
        layout.add_row("Image directory", self._image_dir_edit)
        self._output_ebrf_edit = QLineEdit(self)
        layout.add_row("Output EBRF", self._output_ebrf_edit)
        self.set_layout(layout)
        self.update_include_images_state()
        self._include_images_checkbox.stateChanged.connect(self.update_include_images_state)

    @Slot()
    def update_include_images_state(self):
        self._image_dir_edit.enabled = self._include_images_checkbox.checked

    @property
    def input_brf(self) -> str:
        return self._input_brf_edit.text

    @input_brf.setter
    def input_brf(self, value: str):
        self._input_brf_edit.text = value

    @property
    def include_images(self) -> bool:
        return self._include_images_checkbox.checked

    @include_images.setter
    def include_images(self, value: bool):
        self._include_images_checkbox.checked = value

    @property
    def image_directory(self) -> str:
        return self._image_dir_edit.text

    @image_directory.setter
    def image_directory(self, value: str):
        self._image_dir_edit.text = value

    @property
    def output_ebrf(self) -> str:
        return self._output_ebrf_edit.text

    @output_ebrf.setter
    def output_ebrf(self, value: str):
        self._output_ebrf_edit.text = value


class Brf2EbrfDialog(QDialog):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self.window_title = "Convert BRF to EBRF"
        layout = QVBoxLayout()
        self._brf2ebrf_form = Brf2EbrfWidget()
        layout.add_widget(self._brf2ebrf_form)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        convert_button = self.button_box.add_button("Convert", QDialogButtonBox.ButtonRole.ApplyRole)
        layout.add_widget(self.button_box)
        self.set_layout(layout)
        self.button_box.rejected.connect(self.reject)
        convert_button.clicked.connect(self.on_apply)

    @Slot()
    def on_apply(self):
        pd = QProgressDialog("Conversion in progress", "Cancel", 0, 20)

        def update_progress(value: int):
            pd.value = value

        t = ConvertTask(self)
        pd.canceled.connect(t.cancel)
        t.started.connect(lambda: update_progress(0))
        t.progress.connect(update_progress)
        t.finished.connect(lambda: update_progress(20))
        QThreadPool.global_instance().start(
            RunnableAdapter(t, self._brf2ebrf_form.input_brf, self._brf2ebrf_form.image_directory,
                            self._brf2ebrf_form.output_ebrf))
