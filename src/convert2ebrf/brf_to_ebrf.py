import os
import pathlib
import shutil
from collections.abc import Iterable
from tempfile import TemporaryDirectory

from PySide6.QtCore import QObject, Slot, Signal, QThreadPool
from PySide6.QtWidgets import QWidget, QFormLayout, QCheckBox, QDialog, QDialogButtonBox, QVBoxLayout, \
    QProgressDialog, QMessageBox, QTabWidget, QSpinBox, QFileDialog
# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property
from brf2ebrf.common import PageLayout, PageNumberPosition
from brf2ebrf.scripts.brf2ebrf import create_brf2ebrf_parser, convert_brf2ebrf

from convert2ebrf.utils import RunnableAdapter
from convert2ebrf.widgets import FilePickerWidget

_DEFAULT_PAGE_LAYOUT = PageLayout(
    braille_page_number=PageNumberPosition.BOTTOM_RIGHT,
    print_page_number=PageNumberPosition.TOP_RIGHT,
    cells_per_line=40,
    lines_per_page=25
)


class ConvertTask(QObject):
    started = Signal()
    progress = Signal(int, float)
    finished = Signal()
    cancelled = Signal()
    errorRaised = Signal(Exception)

    def __init__(self, parent: QObject = None):
        super().__init__(parent=parent)
        self._cancel_requested = False

    def __call__(self, input_brf_list: Iterable[str], output_ebrf: str, input_images: str | None,
                 detect_running_heads: bool = True,
                 page_layout: PageLayout = _DEFAULT_PAGE_LAYOUT):
        self.started.emit()
        try:
            with TemporaryDirectory() as temp_dir:
                os.makedirs(os.path.join(temp_dir, "images"), exist_ok=True)
                for index, brf in enumerate(input_brf_list):
                    temp_file = os.path.join(temp_dir, f"vol{index}.xml")
                    parser = create_brf2ebrf_parser(
                        page_layout=page_layout,
                        detect_running_heads=detect_running_heads,
                        brf_path=brf,
                        output_path=temp_file,
                        images_path=input_images
                    )
                    parser_steps = len(parser)
                    convert_brf2ebrf(brf, temp_file, parser,
                                     progress_callback=lambda x: self.progress.emit(index, x / parser_steps),
                                     is_cancelled=lambda: self._cancel_requested)
                    if self._cancel_requested:
                        self.cancelled.emit()
                        return
                with TemporaryDirectory() as out_temp_dir:
                    temp_ebrf = shutil.make_archive(os.path.join(out_temp_dir, "output_ebrf"), "zip", temp_dir)
                    shutil.copyfile(temp_ebrf, output_ebrf)
            self.finished.emit()
        except Exception as e:
            self.errorRaised.emit(e)

    def cancel(self):
        self._cancel_requested = True


class ConversionGeneralSettingsWidget(QWidget):
    inputBrfChanged = Signal(str)
    imagesDirectoryChanged = Signal(str)
    outputEbrfChanged = Signal(str)

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        layout = QFormLayout(self)
        self._input_brf_edit = FilePickerWidget(
            lambda x: os.path.pathsep.join(QFileDialog.get_open_file_names(parent=x, dir=str(pathlib.Path.home()),
                                                                           filter="Braille Ready Files (*.brf)")[0]))
        layout.add_row("Input BRF", self._input_brf_edit)
        self._include_images_checkbox = QCheckBox()
        layout.add_row("Include images", self._include_images_checkbox)
        self._image_dir_edit = FilePickerWidget(
            lambda x: QFileDialog.get_existing_directory(parent=x, dir=str(pathlib.Path.home())))
        layout.add_row("Image directory", self._image_dir_edit)
        self._output_ebrf_edit = FilePickerWidget(lambda x:
                                                  QFileDialog.get_save_file_name(parent=x, dir=str(pathlib.Path.home()),
                                                                                 filter="eBraille Files (*.ebrf)")[0])
        layout.add_row("Output EBRF", self._output_ebrf_edit)
        self._update_include_images_state(self._include_images_checkbox.checked)
        self._include_images_checkbox.toggled.connect(self._update_include_images_state)
        self._input_brf_edit.fileChanged.connect(self.inputBrfChanged.emit)
        self._image_dir_edit.fileChanged.connect(self.imagesDirectoryChanged.emit)
        self._output_ebrf_edit.fileChanged.connect(self.outputEbrfChanged.emit)

    @Slot(bool)
    def _update_include_images_state(self, checked: bool):
        self._image_dir_edit.enabled = checked
        if not checked:
            self._image_dir_edit.file_name = ""

    @property
    def input_brf(self) -> str:
        return self._input_brf_edit.file_name

    @input_brf.setter
    def input_brf(self, value: str):
        self._input_brf_edit.file_name = value

    @property
    def image_directory(self) -> str | None:
        return self._image_dir_edit.file_name if self._include_images_checkbox.checked else None

    @image_directory.setter
    def image_directory(self, value: str | None):
        if value is None:
            self._include_images_checkbox.checked = False
        else:
            self._include_images_checkbox.checked = True
            self._image_dir_edit.file_name = value

    @property
    def output_ebrf(self) -> str:
        return self._output_ebrf_edit.file_name

    @output_ebrf.setter
    def output_ebrf(self, value: str):
        self._output_ebrf_edit.text = value


class ConversionPageSettingsWidget(QWidget):
    detectRunningHeadsChanged = Signal(bool)
    cellsPerLineChanged = Signal(int)
    linesPerPageChanged = Signal(int)

    def __init__(self, parent: QObject = None):
        super().__init__(parent=parent)
        layout = QFormLayout(self)
        self._detect_running_heads_checkbox = QCheckBox()
        self._detect_running_heads_checkbox.checked = True
        layout.add_row("Detect running heads", self._detect_running_heads_checkbox)
        self._cells_per_line_spinbox = QSpinBox()
        self._cells_per_line_spinbox.set_range(10, 100)
        self._cells_per_line_spinbox.single_step = 1
        self._cells_per_line_spinbox.value = 40
        layout.add_row("Cells per line", self._cells_per_line_spinbox)
        self._lines_per_page_spinbox = QSpinBox()
        self._lines_per_page_spinbox.set_range(10, 100)
        self._lines_per_page_spinbox.value = 25
        self._lines_per_page_spinbox.single_step = 1
        layout.add_row("Lines per page", self._lines_per_page_spinbox)
        self._detect_running_heads_checkbox.toggled.connect(self.detectRunningHeadsChanged.emit)
        self._cells_per_line_spinbox.valueChanged.connect(self.cellsPerLineChanged.emit)
        self._lines_per_page_spinbox.valueChanged.connect(self.linesPerPageChanged.emit)

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
        tab_widget = QTabWidget()
        self._brf2ebrf_form = ConversionGeneralSettingsWidget()
        tab_widget.add_tab(self._brf2ebrf_form, "General")
        self._page_settings_form = ConversionPageSettingsWidget()
        tab_widget.add_tab(self._page_settings_form, "Page settings")
        layout = QVBoxLayout(self)
        layout.add_widget(tab_widget)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        b = self.button_box.button(QDialogButtonBox.StandardButton.Close)
        b.default = False
        b.auto_default = False
        self._convert_button = self.button_box.add_button("Convert", QDialogButtonBox.ButtonRole.ApplyRole)
        self._convert_button.default = True
        layout.add_widget(self.button_box)
        self._update_validity()
        self.button_box.rejected.connect(self.reject)
        self._convert_button.clicked.connect(self.on_apply)
        self._brf2ebrf_form.inputBrfChanged.connect(lambda x: self._update_validity())
        self._brf2ebrf_form.imagesDirectoryChanged.connect(lambda x: self._update_validity())
        self._brf2ebrf_form.outputEbrfChanged.connect(lambda x: self._update_validity())

    @Slot()
    def _update_validity(self):
        general_settings = self._brf2ebrf_form
        self._convert_button.enabled = "" not in [general_settings.input_brf, general_settings.image_directory,
                                                  general_settings.output_ebrf]

    @Slot()
    def on_apply(self):
        number_of_steps = 1000
        brf_list = self._brf2ebrf_form.input_brf.split(os.path.pathsep)
        num_of_inputs = len(brf_list)
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
        def error_raised(error: Exception):
            pd.cancel()
            QMessageBox.critical(None, "Error encountered", f"Encountered an error\n{error}")

        t = ConvertTask(self)
        pd.canceled.connect(t.cancel)
        t.started.connect(lambda: update_progress(0))
        t.progress.connect(lambda i, p: update_progress((i + p) / num_of_inputs))
        t.finished.connect(finished_converting)
        t.errorRaised.connect(error_raised)
        QThreadPool.global_instance().start(
            RunnableAdapter(t, brf_list, output_ebrf, self._brf2ebrf_form.image_directory,
                            detect_running_heads=self._page_settings_form.detect_running_heads,
                            page_layout=page_layout))
