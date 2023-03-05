import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox
import logical_parser
from gui import Ui_MainWindow


class MyWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # кнопка РЕШИТЬ
        self.ui.btn_go.clicked.connect(self.btn_clicked)

        # Кнопки, добавляющие операторы в строку
        self.ui.btn_and.clicked.connect(lambda: self.add_sign("&"))
        self.ui.btn_or.clicked.connect(lambda: self.add_sign("|"))
        self.ui.btn_eq.clicked.connect(lambda: self.add_sign("~"))
        self.ui.btn_imp.clicked.connect(lambda: self.add_sign("->"))
        self.ui.btn_not.clicked.connect(lambda: self.add_sign("!"))
        self.ui.btn_pirs.clicked.connect(lambda: self.add_sign("↑"))
        self.ui.btn_sh.clicked.connect(lambda: self.add_sign("↓"))
        self.ui.btn_xor.clicked.connect(lambda: self.add_sign("^"))
        self.ui.btn_to_csv.clicked.connect(self.show_dialog)

    def btn_clicked(self):
        try:
            data, headers = logical_parser.table_data(self.ui.lineEdit.text())
            if data:
                self.ui.table.setColumnCount(len(headers))
                self.ui.table.setRowCount(len(data))
                self.ui.table.setHorizontalHeaderLabels(headers)
                for i, row in zip(range(len(data)), data):
                    for j, elem in zip(range(len(row)), row):
                        self.ui.table.setItem(i, j, QTableWidgetItem(f"{elem}"))
            else:
                self.ui.table.setColumnCount(1)
                self.ui.table.setRowCount(1)
                self.ui.table.setHorizontalHeaderLabels(["Ошибка", ])
                self.ui.table.setItem(0, 0, QTableWidgetItem(headers))
        except Exception as e:
            self.show_modal_window("Произошла ошибка", f"{e}")

    def add_sign(self, symbol: str):
        self.ui.lineEdit.insert(symbol)

    def show_dialog(self):
        fname = QtWidgets.QFileDialog.getSaveFileName(self)[0]
        if fname:
            try:
                data, headers = logical_parser.table_data(self.ui.lineEdit.text())
                f = open(fname, "w")
                for i in headers:
                    f.write(f"{i};")
                f.write("\n")
                for row in data:
                    for elem in row:
                        f.write(f"{elem};")
                    f.write("\n")
                f.close()
                self.show_modal_window("Успех", f"Файл записан по пути {fname}")
            except Exception as e:
                self.show_modal_window("Произошла ошибка", f"{e}")

    def show_modal_window(self, header, message):
        msg_box = QMessageBox()
        msg_box.setText(message)
        msg_box.setWindowTitle(header)
        msg_box.exec()


app = QtWidgets.QApplication([])
application = MyWindow()
application.show()

sys.exit(app.exec())