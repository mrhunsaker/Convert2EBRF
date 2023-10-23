from PySide6.QtCore import QObject, Slot, Signal, QThreadPool
from PySide6.QtWidgets import QWidget, QFormLayout, QLineEdit, QCheckBox, QDialog, QDialogButtonBox, QVBoxLayout, \
    QProgressDialog, QMessageBox, QTabWidget, QSpinBox
from convert2ebrf.utils import RunnableAdapter
# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property
from brf2ebrf.common import PageLayout, PageNumberPosition
from brf2ebrf.scripts.brf2ebrf import create_brf2ebrf_parser, convert_brf2ebrf

from convert2ebrf.widgets import DirectoryPickerWidget

_DEFAULT_PAGE_LAYOUT = PageLayout(
    braille_page_number=PageNumberPosition.BOTTOM_RIGHT,
    print_page_number=PageNumberPosition.TOP_RIGHT,
    cells_per_line=40,
    lines_per_page=25
)


class ConvertTask(QObject):
    started = Signal()
    progress = Signal(float)
    finished = Signal()

    def __init__(self, parent: QObject = None):
        super().__init__(parent=parent)
        self._cancel_requested = False

    def __call__(self, input_brf: str, output_ebrf: str, input_images: str | None, detect_running_heads: bool = True,
                 page_layout: PageLayout = _DEFAULT_PAGE_LAYOUT):
        self.started.emit()
        parser = create_brf2ebrf_parser(
            page_layout=page_layout,
            detect_running_heads=detect_running_heads,
            brf_path=input_brf,
            output_path=output_ebrf,
            images_path=input_images
        )
        parser_steps = len(parser)
        convert_brf2ebrf(input_brf, output_ebrf, parser,
                         progress_callback=lambda x: self.progress.emit(x / parser_steps),
                         is_cancelled=lambda: self._cancel_requested)
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
        self._image_dir_edit = DirectoryPickerWidget(self)
        layout.add_row("Image directory", self._image_dir_edit)
        self._output_ebrf_edit = QLineEdit(self)
        layout.add_row("Output EBRF", self._output_ebrf_edit)
        self.set_layout(layout)
        self._update_include_images_state()
        self._include_images_checkbox.stateChanged.connect(self._update_include_images_state)

    @Slot()
    def _update_include_images_state(self):
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
        return self._image_dir_edit.directory_name

    @image_directory.setter
    def image_directory(self, value: str):
        self._image_dir_edit.directory_name = value

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
        self._detect_running_heads_checkbox = QCheckBox(self)
        self._detect_running_heads_checkbox.checked = True
        layout.add_row("Detect running heads", self._detect_running_heads_checkbox)
        self._cells_per_line_spinbox = QSpinBox(parent=self)
        self._cells_per_line_spinbox.set_range(10, 100)
        self._cells_per_line_spinbox.single_step = 1
        self._cells_per_line_spinbox.value = 40
        layout.add_row("Cells per line", self._cells_per_line_spinbox)
        self._lines_per_page_spinbox = QSpinBox(parent=self)
        self._lines_per_page_spinbox.set_range(10, 100)
        self._lines_per_page_spinbox.value = 25
        self._lines_per_page_spinbox.single_step = 1
        layout.add_row("Lines per page", self._lines_per_page_spinbox)
        self.set_layout(layout)

    @property
    def detect_running_heads(self) -> bool:
        return self._detect_running_heads_checkbox.checked

    @detect_running_heads.setter
    def detect_running_heads(self, value: bool):
        self._detect_running_heads_checkbox.checked = value

    @property
    def cells_per_line(self) -> int:
        return self._cells_per_line_spinbox.value

    @cells_per_line.setter
    def cells_per_line(self, value: int):
        self._cells_per_line_spinbox.value = value

    @property
    def lines_per_page(self) -> int:
        return self._lines_per_page_spinbox.value

    @lines_per_page.setter
    def lines_per_page(self, value: int):
        self._lines_per_page_spinbox.value = value


class Brf2EbrfDialog(QDialog):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self.window_title = "Convert BRF to EBRF"
        tab_widget = QTabWidget(parent=self)
        self._brf2ebrf_form = ConversionGeneralSettingsWidget(parent=self)
        tab_widget.add_tab(self._brf2ebrf_form, "General")
        self._page_settings_form = ConversionPageSettingsWidget(parent=self)
        tab_widget.add_tab(self._page_settings_form, "Page settings")
        layout = QVBoxLayout()
        layout.add_widget(tab_widget)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        b = self.button_box.button(QDialogButtonBox.StandardButton.Close)
        b.default = False
        b.auto_default = False
        convert_button = self.button_box.add_button("Convert", QDialogButtonBox.ButtonRole.ApplyRole)
        convert_button.default = True
        layout.add_widget(self.button_box)
        self.set_layout(layout)
        self.button_box.rejected.connect(self.reject)
        convert_button.clicked.connect(self.on_apply)

    @Slot()
    def on_apply(self):
        number_of_steps = 1000
        output_ebrf = self._brf2ebrf_form.output_ebrf
        page_layout = PageLayout(
            braille_page_number=PageNumberPosition.BOTTOM_RIGHT,
            print_page_number=PageNumberPosition.TOP_RIGHT,
            cells_per_line=self._page_settings_form.cells_per_line,
            lines_per_page=self._page_settings_form.lines_per_page
        )
        pd = QProgressDialog("Conversion in progress", "Cancel", 0, number_of_steps)

        def update_progress(value: float):
            pd.value = int(value * number_of_steps)

        def finished_converting():
            update_progress(1)
            QMessageBox.information(None, "Conversion complete",
                                    f"Your file has been converted and {output_ebrf} has been created.")

        t = ConvertTask(self)
        pd.canceled.connect(t.cancel)
        t.started.connect(lambda: update_progress(0))
        t.progress.connect(update_progress)
        t.finished.connect(finished_converting)
        QThreadPool.global_instance().start(
            RunnableAdapter(t, self._brf2ebrf_form.input_brf, output_ebrf, self._brf2ebrf_form.image_directory,
                            detect_running_heads=self._page_settings_form.detect_running_heads,
                            page_layout=page_layout))
