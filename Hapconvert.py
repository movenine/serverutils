import os, sys
import ffmpeg
import subprocess
import qdarkstyle
from dataclasses import dataclass
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QRunnable, QThreadPool, QObject, pyqtSignal
from PyQt5 import uic

form_class = uic.loadUiType("hapconvert.ui")[0]
# form_class = uic.loadUiType("D:\\MyJobs\\Software\\02_Project\\pythonProject\\ServerUtils\\hapconvert.ui")[0]

class uiShow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.dataOpt = DataOpt(1920,1080,"hap",'','')    # 데이터클래스 초기화
        self.thread_pool = QThreadPool()
        self.setupUi(self)  # Ui 초기화

    # make a openfile dialog using Qt only video files
    def fileOpen(self):
        fname = QFileDialog.getOpenFileName(self, 'Select a video file', './', 'Video files(*.mp4 *.avi *.mkv *.mov *.webm);;All files(*)')
        print(type(fname), fname)

        if fname[0] != None:
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

        self.statusBar().showMessage("File Opened")
    
    # 체크박스 시그널
    def getCheck(self):
        if self.cb_originalRes.isChecked() == False:
            self.le_width.clear()
            self.le_height.clear()
            self.statusBar().showMessage("가로해상도와 세로해상도를 입력하세요!")
        else:
            self.le_width.setText(str(self.dataOpt.width))
            self.le_height.setText(str(self.dataOpt.height))
            self.statusBar().showMessage("원본해상도로 변환합니다.")

    # 변환옵션 시그널
    def getOpt(self):
        self.dataOpt.cvtOpt = self.cbb_option.currentText()
        self.statusBar().showMessage("변환옵션을 설정했습니다.")

    # start convert to a Hap codec 
    def fileConvert(self):
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
        
        task = ConversionTask(input_file, output_file, resolution, codec, format)
        task.progress_signal.connect(self.update_progress)
        self.thread_pool.start(task)
        self.statusBar().showMessage("File Converting ...")
    
    def update_progress(self, progress):
        print(progress)
        self.progressBar.setValue(progress)  # QProgressBar의 값을 업데이트

# QRunnable을 사용하는 방식은 QThread를 사용하는 방식과 비슷하지만, 스레드 풀을 사용하여 스레드 생성 및 관리를 자동으로 처리하기 때문에 더 편리
class ConversionTask(QRunnable, QObject):
    progress_signal = pyqtSignal(int)
    
    def __init__(self, inputFile, outputFile, resolution, codec, format):
        super().__init__()
        QObject.__init__(self)
        self.inputFile = inputFile
        self.outputFile = outputFile
        self.resolution = resolution
        self.codec = codec
        self.format = format

    def run(self):
        command = [
            'cmd', '/c',
            'ffmpeg',
            '-y',
            '-i', self.inputFile,
            '-s', self.resolution,
            '-c:v', self.codec,
            '-f', self.format,
            self.outputFile
        ]
        self.proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        total_frames = None
        # (
        #     ffmpeg
        #     .input(self.inputFile)
        #     .output(self.outputFile, vcodec='hap', format='mov')
        #     .run_async(pipe_stdout=True, pipe_stderr=True)
        # )
        # ffmpeg의 출력을 읽어서 변환 상태를 체크
        while True:
            line = self.proc.stderr.readline()
            if not line:
                break
            if b'frame=' in line:
                progress_str = line.split(b'frame=')[-1].split(b'fps=')[0].strip()
                progress = int(progress_str)
                if total_frames is None:  # 전체 프레임 수를 계산하여 total_frames 변수에 저장
                    total_frames_str = line.split(b'frame=')[-1].split(b'fps=')[-1].split(b' ')[0].strip()
                    total_frames = int(total_frames_str)
                self.progress_signal.emit(progress / total_frames * 100)  # 백분율 값으로 계산하여 progress_signal 시그널 발생
                print(progress, total_frames)
            print(line.decode().strip()) # cmd 창에 출력

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


