import sys
from collections.abc import Sequence

from PySide6.QtWidgets import QApplication
# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property

from convert2ebrf.bef2ebrf import Brf2EbrfWidget


def main(args: Sequence[str] = sys.argv):
    app = QApplication(args)
    w = Brf2EbrfWidget()
    w.show()
    app.exec()


if __name__ == "__main__":
    main(sys.argv)
