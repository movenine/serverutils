import sys
import ffmpeg

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
        return  self.width, self.height

@dataclass
class data_sliceSize:
    slice_address: str
    slice_x1: float
    slice_y1: float
    slice_x2: float
    slice_y2: float

    def get_tuple(self):
        return self.slice_x1, self.slice_y1, self.slice_x2, self.slice_y2

@dataclass
class data_sliceMove:
    slice_address_bl_x: str
    slice_address_bl_y: str
    slice_address_br_x: str
    slice_address_br_y: str
    slice_address_tl_x: str
    slice_address_tl_y: str
    slice_address_tr_x: str
    slice_address_tr_y: str
    slice_cur_value_x: int
    slice_cur_value_y: int
    mouse_x: int
    mouse_y: int

    def get_x_dir(self):
        temp = self.mouse_x - self.slice_cur_value_x
        if temp > 0:
            return 1    # right
        elif temp < 0:
            return -1   # left
        else:
            return 0

    def get_y_dir(self):
        temp = self.mouse_y - self.slice_cur_value_y
        if temp > 0:
            return -1    # down
        elif temp < 0:
            return 1   # up
        else:
            return 0


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
        self.data_size = data_sliceSize('', 0, 0, 0, 0)  # data size 인스턴스 초기화
        self.data_move = data_sliceMove('','','','','','','','', 0, 0, 0, 0)  # data move 인스턴스 초기화
        self.initUI()   # 이벤트필터 설정을 위해 선행

        self.slicePad.installEventFilter(self)  # slicePad에 마우스 이벤트 필터를 사용

    def initUI(self):
        self.lbl_slice_size = QLabel('100 %', self)
        self.lbl_slice_size.setFixedWidth(50)

        # slice combobox
        self.cbb_slice = QComboBox(self)
        self.cbb_slice.setStatusTip('컨트롤할 slice를 선택')
        items = ['slice1', 'slice2', 'slice3', 'slice4', 'slice5', 'slice6']
        self.cbb_slice.addItems(items)
        self.cbb_slice.activated[str].connect(self.cbb_selected)

        # slice Hslider
        self.sld_slice_size = QSlider(Qt.Horizontal, self)
        self.sld_slice_size.setStatusTip('Slice의 크기를 조정(%)')
        self.sld_slice_size.setRange(0, 100)  # 0.00 - 1.00 소수점 환산
        self.sld_slice_size.setValue(100)
        self.sld_slice_size.setSingleStep(1)  # 1 step : 0.01
        self.sld_slice_size.valueChanged.connect(self.cbb_sizeChanged)

        # slice move pad
        self.slicePad = QGroupBox('Slice move pad')
        self.slicePad.setStatusTip('마우스로 끌어서 Slice를 이동')
        self.slicePad.setCursor(QCursor(Qt.PointingHandCursor))

        # grid layout
        self.layout = QGridLayout()
        self.layout.addWidget(QLabel('Slice Select:'), 0, 0)
        self.layout.addWidget(QLabel('Slice Size:'), 1, 0)
        self.layout.addWidget(self.slicePad, 2, 0, 1, 3)
        self.layout.addWidget(self.cbb_slice, 0, 1)
        self.layout.addWidget(self.sld_slice_size, 1, 1)
        self.layout.addWidget(self.lbl_slice_size, 1, 2)
        self.setLayout(self.layout)

    # ---------------------------internal function ------------------------- #

    def input_size_address(self, slice):
        self.data_size.slice_address = '/mapio/project/' + slice + '/output/rect'

    def input_move_address(self, slice):
        self.data_move.slice_address_bl_x = '/mapio/project/' + slice + '/output/bottomleft/x'
        self.data_move.slice_address_bl_y = '/mapio/project/' + slice + '/output/bottomleft/y'
        self.data_move.slice_address_br_x = '/mapio/project/' + slice + '/output/bottomright/x'
        self.data_move.slice_address_br_y = '/mapio/project/' + slice + '/output/bottomright/y'
        self.data_move.slice_address_tl_x = '/mapio/project/' + slice + '/output/topleft/x'
        self.data_move.slice_address_tl_y = '/mapio/project/' + slice + '/output/topleft/y'
        self.data_move.slice_address_tr_x = '/mapio/project/' + slice + '/output/topright/x'
        self.data_move.slice_address_tr_y = '/mapio/project/' + slice + '/output/topright/y'

    def input_size_value(self, x1, y1, x2, y2):
        self.data_size.slice_x1 = float(x1)
        self.data_size.slice_y1 = float(y1)
        self.data_size.slice_x2 = float(x2)
        self.data_size.slice_y2 = float(y2)

    # ---------------------------event function ------------------------- #
    # Slice 선택하면 이벤트 발생하여 해당 address 저장
    def cbb_selected(self, text):
        self.input_size_address(text)
        self.input_move_address(text)

    def cbb_sizeChanged(self):
        try:

            self.lbl_slice_size.setText(str(self.sld_slice_size.value()) + ' %')
            xy_rate = float(self.sld_slice_size.value())/100
            self.input_size_value(0, 0, xy_rate, xy_rate)

            address = self.data_size.slice_address
            value = self.data_size.get_tuple()

        except (OSError, TypeError) as e:
            QMessageBox.information(self, '오류', '유효하지 않는 요청입니다.')
            print(e)
            pass

    def mousePressEvent(self, event):
        print(event.x(), event.y())
        self.data_move.slice_cur_value_x = event.x()
        self.data_move.slice_cur_value_y = event.y()

    def mouseReleaseEvent(self, event):
        print(event.x(), event.y())

    def mouseMoveEvent(self, event):
        self.data_move.mouse_x = event.x()
        self.data_move.mouse_y = event.y()
        x_dir = ''
        y_dir = ''
        if self.data_move.get_x_dir() == 1: # right
            x_dir = '우로'
        elif self.data_move.get_x_dir() == -1: # left
            x_dir = '좌로'

        if self.data_move.get_y_dir() == 1: # up
            y_dir = '위로'
        elif self.data_move.get_y_dir() == -1: # down
            y_dir = '아래로'

        msg = f'loc : ({event.x()}, {event.y()}), direction : ({x_dir}, {y_dir})'
        self.parent.statusbar.showMessage(msg)
        self.update()

        try:
            items = ['']
            address = self.data_move.slice_address_bl_x
            value = self.data_move.slice_cur_value_x

        except (OSError, TypeError) as e:
            QMessageBox.information(self, '오류', '유효하지 않는 요청입니다.')
            print(e)
            pass

    def eventFilter(self, obj, event) -> bool:
        if obj is self.slicePad:
            if event.type() == QEvent.MouseMove:
                mpos = event.pos()
                if mpos.x() < 15 or mpos.x() > 385 or mpos.y() < 75 or mpos.y() > 365:
                    print('범위밖입니다', mpos.x(), mpos.y())
                    return True
            return False
        return False


# 프로그램의 시작점
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QFont('Arial', 9))
    ex = mainGUI()
    ex.show()
    sys.exit(app.exec())
