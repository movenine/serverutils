import os, sys
# import typing
import ffmpeg
import subprocess
import qdarkstyle
import asyncio
from dataclasses import dataclass
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QRunnable, QThreadPool, QObject, pyqtSignal, QThread
from PyQt5 import uic
from tqdm import tqdm

form_class = uic.loadUiType("hapconvert.ui")[0]
# form_class = uic.loadUiType("D:\\MyJobs\\Software\\02_Project\\pythonProject\\ServerUtils\\hapconvert.ui")[0]

class uiShow(QMainWindow, QWidget, form_class):
    def __init__(self):
        super().__init__()
        self.dataOpt = DataOpt(1920,1080,"hap",'','')    # 데이터클래스 초기화
        self.setupUi(self)  # Ui 초기화

    # make a openfile dialog using Qt only video files
    def slot_fileOpen(self):
        self.init_menu()
        fname = QFileDialog.getOpenFileName(self, 'Select a video file', './', 'Video files(*.mp4 *.avi *.mkv *.mov *.webm);;All files(*)')
        print(fname)

        if fname[0] != "":
            self.le_filepath.setText(fname[0])
            self.dataOpt.inputfilePath = fname[0]   # 데이터클래스에 저장
            try:
                file_meta = ffmpeg.probe(fname[0])
            except ffmpeg.Error as e:
                print(e.stderr, file=sys.stderr)
                self.txt_fileinfo.setText(e.stderr)
                #sys.exit(1)

            for stream in file_meta['streams']:
                if stream['codec_type'] == 'video':
                    video_codec = stream['codec_name']
                    res_width = stream['width']
                    res_height = stream['height']
                    duration = file_meta['format']['duration']
                    bitrate = stream['bit_rate']
                    file_size = int(int(bitrate) * float(duration) / 8.0)

                    # save data
                    self.dataOpt.width = res_width
                    self.dataOpt.height = res_height

                    self.txt_fileinfo.setText(f'Video Codec : {video_codec}')
                    self.txt_fileinfo.append(f'Resolution : {str(res_width)} x {str(res_height)}')
                    self.txt_fileinfo.append(f'Duration : {str(duration)} (sec)')
                    self.txt_fileinfo.append(f'File Size : {str(file_size)} bytes')
                elif stream['codec_type'] == 'audio':
                    audio_codec = stream['codec_name']
                    sample_rate = stream['sample_rate']
                    self.txt_fileinfo.append(f'Audio Codec : {audio_codec}')
                    self.txt_fileinfo.append(f'Audio Sample rate : {str(sample_rate)}')
            self.statusBar().showMessage("파일정보를 확인하였습니다")
        else:
            self.statusBar().showMessage("파일열기 취소됨")
    
    # 체크박스 시그널
    def slot_getCheck(self):
        if self.cb_originalRes.isChecked() == False:
            self.le_width.clear()
            self.le_height.clear()
            self.statusBar().showMessage("가로해상도와 세로해상도를 입력하세요!")
        else:
            self.le_width.setText(str(self.dataOpt.width))
            self.le_height.setText(str(self.dataOpt.height))
            self.statusBar().showMessage("원본해상도로 변환합니다.")

    # 변환옵션 시그널
    def slot_getOpt(self):
        self.dataOpt.cvtOpt = self.cbb_option.currentText()
        self.statusBar().showMessage("변환옵션을 설정했습니다.")

    # start convert to a Hap codec 
    def slot_fileConvert(self):
        # 파일 경로 설정
        input_file = self.dataOpt.inputfilePath
        codec = self.dataOpt.cvtOpt
        format = 'mov'
        dir, file = os.path.split(input_file)
        output_file = f'{dir}/[{codec}]{file}.{format}'
        print(output_file)

        # 해상도 설정
        if self.le_width.text() is None:
            self.statusBar().showMessage("가로해상도와 세로해상도를 입력하세요!")
            return

        width = self.le_width.text()
        height = self.le_height.text()
        resolution = f'{width}x{height}'
        
        # 커맨드 설정
        command = [
            'ffmpeg.exe',
            '-y',
            '-i', input_file,
            '-s', resolution,
            '-c:v', codec,
            '-f', format,
            output_file
        ]
        cmd = ' '.join(command)
        print(f'[ffmpeg cmd] {cmd}')

        # 알려진 예외처리
        if " " in file:
            self.statusBar().showMessage("파일경로 및 파일에 공백을 제거해 주세요!")
            return

        # 실행
        asyncio.run(self.task(cmd))
        
    async def update_progress(self, value):
        self.progress_bar.setValue(value)
        QApplication.processEvents()
        await asyncio.sleep(0.1)
    
    async def task(self, cmd):
        total_line = 0
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            for line in tqdm(iter(process.stdout.readline, b'')):
                total_line += 1
                if b'frame=' in line:    # 인코딩 시작단계
                    frame_line = line.split(b'\r') # \r 문자로 구분 리스트
                    frame_line = [v for v in frame_line if v]  # 공백 제거한 리스트
                    for i in range(len(frame_line)):
                        total_line += i
                        await self.update_progress(int((total_line/100)*total_line))            
                print(f'[line] {total_line}', line.decode().strip())
                await self.update_progress(int((total_line/100)*total_line))
            await self.update_progress(100)
            self.statusBar().showMessage("변환완료!")
        except subprocess.CalledProcessError as e:
            print(f'[Error] {e.output}')
        except Exception as e:
            print(f'[Error] {e}')

    def init_menu(self):
        self.le_width.clear()
        self.le_height.clear()
        self.progress_bar.setValue(0)
        self.cb_originalRes.setCheckState(False)
        QApplication.processEvents()

# data class
@dataclass
class DataOpt:
    width: int
    height: int
    cvtOpt: str
    inputfilePath : str
    outputfilePath : str
    
    @property
    def width(self): return self._width
    @width.setter
    def width(self, value): self._width = value
    @property
    def height(self): return self._height
    @height.setter
    def height(self, value): self._height = value
    @property
    def cvtOpt(self): return self._cvtOpt
    @cvtOpt.setter
    def cvtOpt(self, value): self._cvtOpt = value
    @property
    def inputfilePath(self): return self._inputfilePath
    @inputfilePath.setter
    def inputfilePath(self, value): self._inputfilePath = value
    @property
    def outputfilePath(self): return self._outputfilePath
    @outputfilePath.setter
    def outputfilePath(self, value): self._outputfilePath = value

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
    UiShow = uiShow()
    UiShow.show()
    sys.exit(app.exec_())