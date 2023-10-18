from PySide6.QtCore import QObject, Slot, Signal, QThreadPool
from PySide6.QtWidgets import QWidget, QFormLayout, QLineEdit, QCheckBox, QDialog, QDialogButtonBox, QVBoxLayout, \
    QProgressDialog, QMessageBox
# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property
from brf2ebrf.common import PageLayout, PageNumberPosition
from brf2ebrf.scripts.brf2ebrf import create_brf2ebrf_parser, convert_brf2ebrf

from convert2ebrf.utils import RunnableAdapter


class ConvertTask(QObject):
    started = Signal()
    progress = Signal(float)
    finished = Signal()

    def __init__(self, parent: QObject = None):
        super().__init__(parent=parent)
        self._cancel_requested = False

    def __call__(self, input_brf: str, input_images: str | None, output_ebrf: str):
        self.started.emit()
        page_layout = PageLayout(
            braille_page_number=PageNumberPosition.BOTTOM_RIGHT,
            print_page_number=PageNumberPosition.TOP_RIGHT,
            cells_per_line=40,
            lines_per_page=25
        )
        parser = create_brf2ebrf_parser(
            page_layout=page_layout,
            detect_running_heads=True,
            brf_path=input_brf,
            output_path=output_ebrf,
            images_path=input_images
        )
        parser_steps = len(parser)
        convert_brf2ebrf(input_brf, output_ebrf, parser, progress_callback=lambda x: self.progress.emit(x/parser_steps), is_cancelled=lambda: self._cancel_requested)
        self.finished.emit()

    def cancel(self):
        self._cancel_requested = True


class ConversionGeneralSettingsWidget(QWidget):
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


class ConversionPageSettingsWidget(QWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent=parent)
        layout = QFormLayout()
        self.detect_running_heads_checkbox = QCheckBox(self)
        layout.add_row("Detect running heads", self.detect_running_heads_checkbox)
        self.set_layout(layout)


class Brf2EbrfDialog(QDialog):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self.window_title = "Convert BRF to EBRF"
        layout = QVBoxLayout()
        self._brf2ebrf_form = ConversionGeneralSettingsWidget()
        layout.add_widget(self._brf2ebrf_form)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        convert_button = self.button_box.add_button("Convert", QDialogButtonBox.ButtonRole.ApplyRole)
        layout.add_widget(self.button_box)
        self.set_layout(layout)
        self.button_box.rejected.connect(self.reject)
        convert_button.clicked.connect(self.on_apply)

    @Slot()
    def on_apply(self):
        number_of_steps = 1000
        output_ebrf = self._brf2ebrf_form.output_ebrf
        pd = QProgressDialog("Conversion in progress", "Cancel", 0, number_of_steps)

        def update_progress(value: float):
            pd.value = int(value * number_of_steps)

        def finished_converting():
            update_progress(1)
            QMessageBox.information(None, "Conversion complete", f"Your file has been converted and {output_ebrf} has been created.")

        t = ConvertTask(self)
        pd.canceled.connect(t.cancel)
        t.started.connect(lambda: update_progress(0))
        t.progress.connect(update_progress)
        t.finished.connect(finished_converting)
        QThreadPool.global_instance().start(
            RunnableAdapter(t, self._brf2ebrf_form.input_brf, self._brf2ebrf_form.image_directory,
                            output_ebrf))
