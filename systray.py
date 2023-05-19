import os
import sys
import subprocess
import gui_encoder
import pystray
from PyQt5 import QtWidgets, QtCore, QtGui

#from PySide6 import QtWidgets, QtGui

class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    """
    CREATE A SYSTEM TRAY ICON CLASS AND ADD MENU
    """
    def __init__(self, icon, parent=None):
        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)
        self.setToolTip(f'CUDO Server Manager - v1.00')

        menu = QtWidgets.QMenu(parent)
        #Hap 코덱 변환 메뉴
        app_encoder = menu.addAction("인코딩")
        app_encoder.setToolTip(f'코덱변환툴')
        app_encoder.triggered.connect(self.open_Encoder)
        app_encoder.setIcon(QtGui.QIcon("icon.png"))

        #장치등록/제어 관리 창 메뉴
        app_controlpanel = menu.addAction("장치등록/제어")
        app_controlpanel.setToolTip(f'컨트롤러 및 제어장치를 리스트 등록하고 제어함')
        app_controlpanel.triggered.connect(self.open_controlpanel)
        app_controlpanel.setIcon(QtGui.QIcon("icon.png"))

        #설정 메뉴
        app_preferences = menu.addAction("환경설정")
        app_preferences.setToolTip(f'옵션/사용자등록/서버설정/제품업데이트 제공')
        app_preferences.triggered.connect(self.open_preferences)
        app_preferences.setIcon(QtGui.QIcon("icon.png"))

        # 모니터링 웹 뷰어 메뉴
        app_monitoring = menu.addAction("모니터링 웹 뷰어")
        app_monitoring.setToolTip(f'웹페이지 접속/장치상태정보/유지보수정보 제공')
        app_monitoring.triggered.connect(self.open_monitoring)
        app_monitoring.setIcon(QtGui.QIcon("icon.png"))

        #프로그램 종료
        exit_ = menu.addAction("프로그램 종료")
        exit_.triggered.connect(lambda: sys.exit())
        exit_.setIcon(QtGui.QIcon("icon.png"))

        menu.addSeparator()
        self.setContextMenu(menu)
        self.activated.connect(self.onTrayIconActivated)

    # --------------------- Action event function ---------------------- #
    def onTrayIconActivated(self, reason):
        """
        This function will trigger function on click or double click
        :param reason:
        :return:
        """
        if reason == self.DoubleClick:
            self.open_Encoder()
        # if reason == self.Trigger:
        #     self.open_notepad()

    # --------------------- Open HapEncoder window ---------------------- #
    def open_Encoder(self):
        self.encoder_window = gui_encoder.mainGUI()
        self.encoder_window.show()

    # --------------------- Open Control panel window ---------------------- #
    def open_controlpanel(self):
        return 0
    # --------------------- Open Preferences window ---------------------- #
    def open_preferences(self):
        return 0
    # --------------------- Open Monitoring window ---------------------- #
    def open_monitoring(self):
        return 0

def main(image):
    app = QtWidgets.QApplication(sys.argv)
    w = QtWidgets.QWidget()
    tray_icon = SystemTrayIcon(QtGui.QIcon(image), w)
    tray_icon.show()
    tray_icon.showMessage('Cudo Communication', 'www.ailed.co.kr')
    sys.exit(app.exec())


if __name__ == '__main__':
    icon = "icon.png"
    main(icon)