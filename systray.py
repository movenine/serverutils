import os
import sys
import qdarktheme
import Hapconvert
from PyQt5 import QtWidgets, QtGui

main_icon_path = f'{os.getcwd()}\\resources\\main_icon.png'
hap_icon_path = f'{os.getcwd()}\\resources\\app_title_icon.png'

class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    """
    CREATE A SYSTEM TRAY ICON CLASS AND ADD MENU
    """
    def __init__(self, icon, parent=None):
        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)
        self.setToolTip(f'CUDO LED Server Tools-v1.0.0')

        menu = QtWidgets.QMenu(parent)
        #Hap 코덱 변환 메뉴
        app_encoder = menu.addAction("HAP코덱변환")
        app_encoder.setToolTip(f'고해상도용 무압축 HAP 코덱으로 변환함')
        app_encoder.triggered.connect(self.open_Encoder)
        app_encoder.setIcon(QtGui.QIcon(hap_icon_path))

        # #장치등록/제어 관리 창 메뉴
        # app_controlpanel = menu.addAction("장치등록/제어")
        # app_controlpanel.setToolTip(f'컨트롤러 및 제어장치를 리스트 등록하고 제어함')
        # app_controlpanel.triggered.connect(self.open_controlpanel)
        # app_controlpanel.setIcon(QtGui.QIcon(icon_path))

        # #설정 메뉴
        # app_preferences = menu.addAction("환경설정")
        # app_preferences.setToolTip(f'옵션/사용자등록/서버설정/제품업데이트 제공')
        # app_preferences.triggered.connect(self.open_preferences)
        # app_preferences.setIcon(QtGui.QIcon(icon_path))

        # #모니터링 웹 뷰어 메뉴
        # app_monitoring = menu.addAction("모니터링 웹 뷰어")
        # app_monitoring.setToolTip(f'웹페이지 접속/장치상태정보/유지보수정보 제공')
        # app_monitoring.triggered.connect(self.open_monitoring)
        # app_monitoring.setIcon(QtGui.QIcon(icon_path))

        # 프로그램 종료
        exit_ = menu.addAction("프로그램 종료")
        exit_.triggered.connect(lambda: sys.exit())

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

    # --------------------- Open HapEncoder window ---------------------- #
    def open_Encoder(self):
        self.encoder_window = Hapconvert.uiShow()
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
    QtWidgets.QApplication.setQuitOnLastWindowClosed(False) # tray 아이템을 종료시 app 종료를 하지 않음
    #app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
    qdarktheme.setup_theme(theme="auto", corner_shape="sharp")
    app.setStyleSheet(qdarktheme.load_stylesheet())
    w = QtWidgets.QWidget()
    tray_icon = SystemTrayIcon(QtGui.QIcon(image), w)
    tray_icon.show()
    tray_icon.showMessage('Cudo Communication', 'www.ailed.co.kr')
    sys.exit(app.exec())


if __name__ == '__main__':
    main(main_icon_path)