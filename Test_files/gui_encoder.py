import sys
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo
from dataclasses import dataclass

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


# data class
@dataclass
class data_windowSize:
    width: int
    height: int

    def get_size(self):
        return self.width, self.height


# main window class
class mainGUI(QMainWindow):
    def __init__(self, parent=None):
        super(mainGUI, self).__init__(parent)
        self.initUI()
        self.control_widgets = controlWidgets(self)
        self.control_widgets.setMouseTracking(False)
        self.setCentralWidget(self.control_widgets)
        self.statusbar = self.statusBar()
        self.statusbar.setStyleSheet("background-color : gainsboro")

    def initUI(self):
        self.window_size = data_windowSize(400, 400)
        file_path_control_icon = "H:\Work\Donggujobs\dglee\software\pythonProject\myTestSite\icons\control.png"
        self.setWindowTitle("HAP Codec 변환툴")

        self.setWindowIcon(QIcon(f"{file_path_control_icon}"))
        # self.resize(400, 400)
        self.setGeometry(500, 500, self.window_size.width, self.window_size.height)
        # 윈도우 사이즈 고정
        self.setFixedSize(self.window_size.width, self.window_size.height)

    def resizeEvent(self, event):
        print('윈도우 사이즈 변경됨')
        print(self.width(), self.height())

# sub widget class
class controlWidgets(QWidget):
    def __init__(self, parent):
        super(controlWidgets, self).__init__(parent)
        self.parent = parent
        self.initUI()  # 이벤트필터 설정을 위해 선행

    def initUI(self):


        # grid layout
        self.layout = QGridLayout()
        self.layout.addWidget(QLabel('Slice Select:'), 0, 0)
        self.layout.addWidget(QLabel('Slice Size:'), 1, 0)
        self.setLayout(self.layout)

    # ---------------------------internal function ------------------------- #

    # ---------------------------event function ------------------------- #

# 프로그램의 시작점
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QFont('Arial', 9))
    ex = mainGUI()
    ex.show()
    # sys.exit(app.exec())
