import logging
import sys
from collections.abc import Sequence

from PySide6.QtWidgets import QApplication
# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property

from convert2ebrf.brf_to_ebrf import Brf2EbrfDialog


def run_app(args: Sequence[str]):
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s:%(asctime)s:%(module)s:%(message)s"
    )
    app = QApplication(args)
    app.organization_name = "American Printing House for the Blind"
    app.organization_domain = "aph.org"
    app.application_name = "Convert2EBRF"
    w = Brf2EbrfDialog()
    w.show()
    app.exec()


def main():
    run_app(sys.argv)


if __name__ == "__main__":
    main()
