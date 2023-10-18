import os, sys, ffmpeg, subprocess, asyncio, shlex, json
from dataclasses import dataclass
from PyQt5.QtWidgets import *
# from PyQt5.QtCore import *
from PyQt5 import uic, QtGui, QtCore
from tqdm import tqdm
from Applog import syslog as SL
import Happlay

form_class = uic.loadUiType("hapconvert.ui")[0]
# form_class = uic.loadUiType("D:\\MyJobs\\Software\\02_Project\\pythonProject\\ServerUtils\\hapconvert.ui")[0]
log_file_path = f'{os.getcwd()}\\log\\hapConvertLog.log'
app_title_icon_path = f'{os.getcwd()}\\resources\\app_title_icon.png'
save_file_path = f'{os.getcwd()}\\Files'

class uiShow(QMainWindow, QWidget, form_class):
    def __init__(self):
        super().__init__()
        # 데이터클래스 초기화
        self.dataOpt = DataOpt(
            inputfilePath='',
            outputfilePath='',
            width=0,
            ori_width=0,
            height=0,
            ori_height=0,
            cvtOpt="hap",
            originalRes=False,
            multiCPU=6,
            scaleRatio=False,
            scaleAlgo='',
            usrScript='',
            frameRate=0,
            duration=0
            )
        self.subProc = subProcCheck(
            pid=0,
            run=False,
            returnCode=-1,
            progress=0
        )
        # 로거 초기화
        self.mCvtLog = SL('hapConvertlogger')
        self.mCvtLog = self.mCvtLog.rotating_filehandler(
            filename=log_file_path,
            mode='a',
            level="DEBUG",
            backupCount=10,
            logMaxSize=1048576
            )
        self.setupUi(self)  # Ui 초기화
        self.setWindowIcon(QtGui.QIcon(app_title_icon_path))
        self.init_Menu()
        
        # 메뉴바 이벤트 핸들링
        self.actionManual.triggered.connect(self.openManual)
        self.actionInfo.triggered.connect(self.openInfo)
        self.actionImport.triggered.connect(self.getImport)
        self.actionExport.triggered.connect(self.saveExport)

    def init_Menu(self):
        # Core 업데이트
        n_cores = os.cpu_count()
        self.lb_cpunumber.setText(f'({str(n_cores)} of CPU Cores)')
        # Scale 옵션 비활성화
        self.cb_aspertRatio.setEnabled(False)
        self.cbb_algorithm.setEnabled(False)
        self.bt_preViewer.setEnabled(False)
        # Json 파일 import

    def init_fileOpen(self):
        self.txt_fileinfo.clear()
        self.le_width.clear()
        self.le_height.clear()
        self.progress_bar.setValue(0)
        self.cb_originalRes.setCheckState(False)
        self.bt_preViewer.setEnabled(True)
        QApplication.processEvents()

    ## 메뉴바 이벤트 콜백
    def openManual(self):
        result = QMessageBox.information(self, "메뉴얼", "메뉴얼을 여시겠습니까?", QMessageBox.Ok)
        return
    
    ## 프로그램정보 이벤트 콜백
    def openInfo(self):
        pixmap = QtGui.QPixmap(app_title_icon_path)
        msg = QMessageBox()
        msg.setIconPixmap(pixmap)
        msg.setWindowIcon(QtGui.QIcon(app_title_icon_path))
        msg.setTextFormat(QtCore.Qt.RichText)
        msg.setWindowTitle("About")
        msg.setText(
            "<p><b>HAP Codec Convert</b><br><br>"
            "Author : leedg, 2023<br>"
            "Version : v1.0.0<br>"
            "Licence : <a href=http://ffmpeg.org>FFmpeg</a> licensed under the <a href=http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html>LGPLv2.1</a>"
            "<br><br>"
            "이 소프트웨어는 LGPLv2.1에 따라 FFmpeg 프로젝트의 라이브러리를 사용합니다<br>"
        )
        msg.exec_()
        return

    ## 설정 가져오기 이벤트 콜백
    def getImport(self):
        return

    ## 설정 내보내기 이벤트 콜백
    def saveExport(self):
        try:
            fname = QFileDialog.getSaveFileName(self, 'Export a option file', save_file_path, 'Option files(*.opt);;All files(*)')
            print(fname)

            if fname[0] != "":
                fileData = self.dataOpt.getOptDict()
                serial_fileData = json.dumps(fileData, indent=10)
                # 옵션 파일 쓰기
                with open(fname[0], "w") as outfile:
                    outfile.write(serial_fileData)
                
                dir, file = os.path.split(fname[0])
                self.statusBar().showMessage(f'{dir}/{file}.opt 옵션파일 저장')
            else:
                self.statusBar().showMessage("옵션파일저장 취소")
        except Exception as e:
            self.mCvtLog.error(e)
        return

    #region private method
    #parameter : file path
    #return : fileinfo of dict type
    def func_fileinfo(self, path):
        file_meta = ffmpeg.probe(path)
        for stream in file_meta['streams']:
            if stream['codec_type'] == 'video':
                video_codec = stream['codec_name']
                res_width = stream['width']
                res_height = stream['height']
                duration = file_meta['format']['duration']
                bitrate = stream['bit_rate']
                size = file_meta['format']['size']
                frate = stream['avg_frame_rate']
                list = frate.split('/')
                frame = float(int(list[0])/int(list[1]))
                bit_rate = float(int(bitrate) / (1000 * 1000))
                file_size = float(int(size) / (1024 * 1024))
            elif stream['codec_type'] == 'audio':
                audio_codec = stream['codec_name']
                sample_rate = stream['sample_rate']

        dic = dict()
        dic['video_codec'] = video_codec
        dic['res_width'] = res_width
        dic['res_height'] = res_height
        dic['duration'] = duration
        dic['frame'] = frame
        dic['bit_rate'] = bit_rate
        dic['file_size'] = file_size
        dic['audio_codec'] = audio_codec
        dic['sample_rate'] = sample_rate
        return dic
    #endregion private method
    
    #region 버튼 시그널
    # make a openfile dialog using Qt only video files
    def slot_fileOpen(self):
        self.init_fileOpen()
        fname = QFileDialog.getOpenFileName(self, 'Select a video file', './', 'Video files(*.mp4 *.avi *.mkv *.mov *.webm);;All files(*)')
        print(fname)

        if fname[0] != "":
            self.le_fileInputPath.setText(fname[0])
            self.dataOpt.inputfilePath = fname[0]   # 데이터클래스에 저장
            try:
                fileinfo = self.func_fileinfo(fname[0])
                dir, file = os.path.split(fname[0])
                fileCheck = file.split('.')

                if " " in file or " " in dir:
                    result = QMessageBox.warning(self, "주의", "파일경로 및 파일명에 공백은 제거해주세요", QMessageBox.Ok)
                    return
                elif len(fileCheck) > 2:
                    result = QMessageBox.warning(self, "주의", "파일명에 확장자명은 하나만 지정해주세요", QMessageBox.Ok)
                    return
                else:
                    result = QMessageBox.No
                    self.txt_fileinfo.setText(f'소스파일 : {file}')

                #save data
                self.dataOpt.ori_width = fileinfo['res_width']
                self.dataOpt.ori_height = fileinfo['res_height']
                self.dataOpt.frameRate = float(fileinfo["frame"])
                self.dataOpt.duration = float(fileinfo["duration"])

                #set textbox
                self.txt_fileinfo.append(f'Video Codec : {fileinfo["video_codec"]}')
                self.txt_fileinfo.append(f'bit rate : {fileinfo["bit_rate"]:.2f} Mb/s')
                self.txt_fileinfo.append(f'Resolution : {str(fileinfo["res_width"])} x {str(fileinfo["res_height"])}')
                self.txt_fileinfo.append(f'Frame rate : {fileinfo["frame"]}')
                self.txt_fileinfo.append(f'Duration : {str(fileinfo["duration"])} (sec)')
                self.txt_fileinfo.append(f'File Size : {fileinfo["file_size"]:.2f} Mbytes')
                self.txt_fileinfo.append(f'Audio Codec : {fileinfo["audio_codec"]}')
                self.txt_fileinfo.append(f'Audio Sample rate : {str(fileinfo["sample_rate"])}')
            except ffmpeg.Error as e:
                print(e.stderr, file=sys.stderr)
                self.txt_fileinfo.setText(e.stderr)
                self.mCvtLog.error(e.stderr)
                #sys.exit(1)
            finally:
                if result == QMessageBox.Ok:
                    self.mCvtLog.warning(f'파일경로 및 파일명 오류')
                    self.le_fileInputPath.clear()
                pass
        else:
            self.statusBar().showMessage("파일열기 취소")
    
    # make a savefile dialog using Qt only video files
    def slot_fileSave(self):
        DefaultPath = self.dataOpt.inputfilePath
        try:
            fname = QFileDialog.getSaveFileName(self, 'Save a video file', DefaultPath, 'Video files(*.mov);;All files(*)')
            print(fname)

            if fname[0] != "":
                self.le_fileSavePath.setText(fname[0])
                # 출력 파일 설정
                dir, file = os.path.split(fname[0])
                if fname[0].find('mov'):
                    self.dataOpt.outputfilePath = fname[0]
                else:
                    self.dataOpt.outputfilePath = f'{dir}/{file}.mov'  # 데이터클래스에 저장
            else:
                self.statusBar().showMessage("파일저장 취소")
        except Exception as e:
            self.mCvtLog.error(e)

    # play a video file
    def slot_previewer(self):
        if self.dataOpt.inputfilePath != "" and self.dataOpt.outputfilePath == "":      # 입력파일만 있는경우
            print(self.dataOpt.inputfilePath, self.dataOpt.outputfilePath)
            dir, file = os.path.split(self.dataOpt.inputfilePath)
            if " " in file:
                self.statusBar().showMessage("파일경로 및 파일에 공백을 제거해 주세요!")
                return
            cmd = f'mplayer {self.dataOpt.inputfilePath} -xy 960 -loop 0 -geometry 10:50 -use-filename-title'
            try:
                asyncio.run(Happlay.mPlay(cmd)) # 단일 실행
            except Exception as e:
                self.mCvtLog.error(f'Play error : {e}')
            else:
                self.mCvtLog.info(f'Play video input file : {input_cmd}')
        elif self.dataOpt.inputfilePath != "" and self.dataOpt.outputfilePath != "":    # 둘다 있는 경우   
            print(self.dataOpt.inputfilePath, self.dataOpt.outputfilePath)
            input_cmd = f'mplayer {self.dataOpt.inputfilePath} -xy 960 -loop 0 -geometry 10:50 -use-filename-title'
            output_cmd = f'mplayer {self.dataOpt.outputfilePath} -xy 960 -loop 0 -geometry 10:550 -use-filename-title'
            try:
                asyncio.run(self.task_preview(inputCmd=input_cmd, outputCmd=output_cmd))    # 복수 실행
            except Exception as e:
                self.mCvtLog.error(f'Play error : {e}')
            else:
                self.mCvtLog.info(f'Play video input file : {input_cmd}')
                self.mCvtLog.info(f'Play video output file : {output_cmd}')
        else:   # 입력파일이 없는 경우
            self.mCvtLog.warning(f'{self.dataOpt.inputfilePath} 입력파일이 없습니다.')
            return
    
    # start convert to a Hap codec 
    def slot_fileConvert(self):
        self.subProc.progress = 0
        # 예외처리
        if " " in self.dataOpt.outputfilePath:
            self.statusBar().showMessage("저장할 파일에 공백을 제거해 주세요!")
            return
        elif not self.le_width.text():
            self.statusBar().showMessage("가로해상도와 세로해상도를 입력하세요!")
            return

        # 저장위치가 없으면, 동일한 폴더에 파일 경로 설정
        if not self.le_fileSavePath.text():
            input_file = self.dataOpt.inputfilePath
            codec = self.dataOpt.cvtOpt
            dir, file = os.path.split(input_file)
            output_file = f'{dir}/{codec}_{file}.mov'
            self.dataOpt.outputfilePath = output_file
            self.txt_fileinfo.append(f'')
            self.txt_fileinfo.append(f'변환파일위치 : {output_file}')
            self.mCvtLog.info(output_file)

        # 진행률 설정
        self.progress_bar.setMaximum(self.dataOpt.getMaxFrame())
        print(f'Progress bar maximum : {self.dataOpt.getMaxFrame()}')

        # 커맨드 설정
        command = self.dataOpt.ffmpegCmd()
        cmd = ' '.join(command)
        self.mCvtLog.info(f'[ffmpeg cmd] {cmd}')

        # 커맨드 확인 및 실행
        try:
            if command[3] != '':
                asyncio.run(self.task_Convert(cmd))
            else:
                raise Exception(f'cmd 구문애러 : {cmd}')                
        except Exception as e:
            self.mCvtLog.error(f'변환오류 : {e}')
            self.subProc.run = False
            print(f'변환오류 : {e}')
        else:
            fileinfo = self.func_fileinfo(self.dataOpt.outputfilePath)
            self.txt_fileinfo.append(f'=====================출력파일정보=====================')
            self.txt_fileinfo.append(f'출력파일 : {self.dataOpt.outputfilePath}')
            self.txt_fileinfo.append(f'Video Codec : {fileinfo["video_codec"]}')
            self.txt_fileinfo.append(f'bit rate : {fileinfo["bit_rate"]:.2f} Mb/s')
            self.txt_fileinfo.append(f'Resolution : {str(fileinfo["res_width"])} x {str(fileinfo["res_height"])}')
            self.txt_fileinfo.append(f'Frame rate : {fileinfo["frame"]}')
            self.txt_fileinfo.append(f'Duration : {str(fileinfo["duration"])} (sec)')
            self.txt_fileinfo.append(f'File Size : {fileinfo["file_size"]:.2f} Mbytes')
            self.txt_fileinfo.append(f'Audio Codec : {fileinfo["audio_codec"]}')
            self.txt_fileinfo.append(f'Audio Sample rate : {str(fileinfo["sample_rate"])}')
            self.mCvtLog.info(f'파일변환 : I[{self.dataOpt.inputfilePath}] --> O[{self.dataOpt.outputfilePath}]')
    #endregion 버튼시그널

    #region 체크박스 시그널
    # 원본해상도
    def slot_getCheck(self):
        if self.cb_originalRes.isChecked() == False:
            self.le_width.clear()
            self.le_height.clear()
            self.dataOpt.originalRes = False
            self.statusBar().showMessage("가로해상도와 세로해상도를 입력하세요!")
        else:
            self.le_width.setText(str(self.dataOpt.ori_width))
            self.le_height.setText(str(self.dataOpt.ori_height))
            self.dataOpt.originalRes = True
            self.statusBar().showMessage("원본해상도로 변환합니다.")
    
    # Scale 옵션 활성화
    def slot_scaleOptCheck(self):
        if self.cb_scaleEnable.isChecked() == False:
            self.cb_aspertRatio.setEnabled(False)
            self.cbb_algorithm.setEnabled(False)
            self.cb_originalRes.setEnabled(True)
            self.dataOpt.scaleAlgo = " "
        else:
            self.cb_aspertRatio.setEnabled(True)
            self.cbb_algorithm.setEnabled(True)
            self.cb_originalRes.setChecked(False)
            self.cb_originalRes.setEnabled(False)

    # 종횡비 고정
    def slot_fixedRatioCheck(self):
        if self.cb_aspertRatio.isChecked() == False:
            self.le_height.setEnabled(True)
            self.dataOpt.scaleRatio = False
        else:
            self.le_height.setEnabled(False)
            self.cb_originalRes.setEnabled(False)
            self.dataOpt.scaleRatio = True
            self.dataOpt.height = -4
    #endregion 체크박스 시그널

    #region 콤보박스 시그널
    # 코덱
    def slot_getOpt(self):
        self.dataOpt.cvtOpt = self.cbb_option.currentText()
        if self.dataOpt.cvtOpt == "none":
            self.statusBar().showMessage(f'코덱:{self.dataOpt.cvtOpt} 기본 h.264로 변환됩니다.')
    
    # Scale 알고리즘
    def slot_getAlgoOpt(self):
        self.dataOpt.scaleAlgo = self.cbb_algorithm.currentText()
    #endregion 콤보박스 시그널

    #region 텍스트박스 시그널
    # 파일 열기
    def slot_inputfileChanged(self):
        if not self.le_fileInputPath.text():
            self.dataOpt.inputfilePath = ""
            self.statusBar().showMessage(f'파일 열기 취소')

    def slot_outputfileChanged(self):
        if not self.le_fileSavePath.text():
            self.dataOpt.outputfilePath = ""
            self.statusBar().showMessage(f'파일 저장 취소')

    # 해상도 변경
    def slot_widthEdit(self):
        width = self.le_width.text()
        self.dataOpt.width = width
        self.statusBar().showMessage(f'가로해상도 {width} 저장')
    
    def slot_heightEdit(self):
        height = self.le_height.text()
        self.dataOpt.height = height
        self.statusBar().showMessage(f'세로해상도 {height} 저장')

    # 코어수 변경
    def slot_multicpuEdit(self):
        multiCPU = self.le_multicpu.text()
        self.dataOpt.multiCPU = multiCPU
        self.statusBar().showMessage(f'코어수 {multiCPU} 저장')
    
    # 사용자스크립트 변경
    def slot_addScriptEdit(self):
        script = self.le_userScript.text()
        self.dataOpt.usrScript = script
        self.statusBar().showMessage(f'사용자 스크립트 저장')
    #endregion 텍스트박스 시그널

    #region 코루틴
    ### reference : https://tech.buzzvil.com/blog/asyncio-no-1-coroutine-and-eventloop/ ###
    # 코루틴 work 설정
    async def task_Convert(self, cmd):
        result = await asyncio.gather(
            self.Convert(cmd),
            asyncio.create_task(self.update_message()),
            # asyncio.create_task(self.update_progress())
        )
        self.mCvtLog.info(f'Converter return : {result}')

    async def task_preview(self, inputCmd, outputCmd):
        result = await asyncio.gather(
            Happlay.mPlay(inputCmd),
            Happlay.mPlay(outputCmd)
        )
        self.mCvtLog.info(f'Previewer return : {result}')

    # async def update_progress(self) -> None:
    #     while True:
    #         value = self.subProc.progress
    #         self.progress_bar.setValue(int((value/100)*value))
    #         QApplication.processEvents()
    #         await asyncio.sleep(0.01)
    #         if value == 100 or self.subProc.run == False:
    #             break
    
    async def update_message(self) -> None:
        msgs = ['변환중.','변환중..','변환중...','변환중....','변환중.....','변환중......']
        idx = 0
        while True:
            if idx > 5: idx = 0
            self.statusBar().showMessage(msgs[idx])
            QApplication.processEvents()
            await asyncio.sleep(0.4)
            idx += 1
            if self.subProc.run == False:
                break

    async def update_progress_value(self, value) -> None:
        self.subProc.progress = value
        self.progress_bar.setValue(value)
        QApplication.processEvents()
        await asyncio.sleep(0.01)
    
    async def Convert(self, cmd):
        total_line = 0
        try:
            cmd_list = shlex.split(cmd)
            proc = await asyncio.create_subprocess_exec(
                *cmd_list,
                stdout=asyncio.subprocess.PIPE, 
                stderr=asyncio.subprocess.STDOUT
            )
            self.subProc.pid = proc.pid
            self.subProc.run = True
            log = b''
            while proc.returncode is None:
                buf = await proc.stdout.read(100)
                if not buf:
                    break
                else:
                    if 'frame' in buf.decode():
                        frame = buf.decode().split(' ')
                        frame = [v for v in frame if v]
                        print(int(frame[1]))
                        if frame[0] == 'frame=':
                            total_line = int(frame[1])
                            log = buf
                    elif 'failed' in buf.decode():
                        raise Exception(f'변환실패-{buf.decode()}')
                    else:
                        total_line += 1
                    # self.progress_bar.setValue(int((total_line/100)*total_line))
                    await self.update_progress_value(total_line)
                # log += buf
                # sys.stdout.write(buf.decode())
                print(f'[{total_line}] [{buf.decode()}]')
            result = subprocess.CompletedProcess(cmd, proc.returncode, stdout=log, stderr=b'')
        except subprocess.CalledProcessError as e:
            self.subProc.run = False
            print(f'[Error] {e.output}')
            self.mCvtLog.error(e.output)
        except Exception as e:
            self.subProc.run = False
            print(f'[Error] {e}')
            self.statusBar().showMessage("변환실패!")
            self.mCvtLog.error(e)
        else:
            self.subProc.run = False
            self.statusBar().showMessage("변환완료!")
            self.subProc.returnCode = proc.returncode    # 정상종료시 '0'
            await self.update_progress_value(self.dataOpt.getMaxFrame())
            return result

    #endregion 코루틴

#region 데이터클래스
@dataclass
class subProcCheck:
    pid : int
    run : bool
    returnCode : int
    progress : int

    @property
    def pid(self): return self._pid
    @pid.setter
    def pid(self, value): self._pid = value
    @property
    def run(self): return self._run
    @run.setter
    def run(self, value): self._run = value
    @property
    def returnCode(self): return self._returnCode
    @returnCode.setter
    def returnCode(self, value): self._returnCode = value
    @property
    def progress(self): return self._progress
    @progress.setter
    def progress(self, value): self._progress = value

    def procCheck(self):
        dic = dict()
        dic['process ID'] = self.pid
        dic['running'] = self.run
        dic['return code'] = self.returnCode
        dic['progress'] = self.progress
        return dic

@dataclass
class DataOpt:
    inputfilePath : str
    outputfilePath : str
    width: int
    ori_width: int
    height: int
    ori_height: int
    cvtOpt: str
    originalRes: bool
    multiCPU: int
    scaleRatio: bool
    scaleAlgo: str
    usrScript: str
    frameRate: float
    duration: float
        
    @property
    def inputfilePath(self): return self._inputfilePath
    @inputfilePath.setter
    def inputfilePath(self, value): self._inputfilePath = value
    
    @property
    def outputfilePath(self): return self._outputfilePath
    @outputfilePath.setter
    def outputfilePath(self, value): self._outputfilePath = value
    
    @property
    def width(self): return self._width
    @width.setter
    def width(self, value): self._width = value
    
    @property
    def ori_width(self): return self._ori_width
    @ori_width.setter
    def ori_width(self, value): self._ori_width = value

    @property
    def height(self): return self._height
    @height.setter
    def height(self, value): self._height = value
    
    @property
    def ori_height(self): return self._ori_height
    @ori_height.setter
    def ori_height(self, value): self._ori_height = value

    @property
    def cvtOpt(self): return self._cvtOpt
    @cvtOpt.setter
    def cvtOpt(self, value): self._cvtOpt = value
    
    @property
    def originalRes(self): return self._originalRes
    @originalRes.setter
    def originalRes(self, value): self._originalRes = value
    
    @property
    def multiCPU(self): return self._multiCPU
    @multiCPU.setter
    def multiCPU(self, value): self._multiCPU = value
    
    @property
    def scaleRatio(self): return self._scaleRatio
    @scaleRatio.setter
    def scaleRatio(self, value): self._scaleRatio = value
    
    @property
    def scaleAlgo(self): return self._scaleAlgo
    @scaleAlgo.setter
    def scaleAlgo(self, value): self._scaleAlgo = value
    
    @property
    def usrScript(self): return self._usrScript
    @usrScript.setter
    def usrScript(self, value): self._usrScript = value

    @property
    def frameRate(self): return self._frameRate
    @frameRate.setter
    def frameRate(self, value): self._frameRate = value

    @property
    def duration(self): return self._duration
    @duration.setter
    def duration(self, value): self._duration = value


    def ffmpegCmd(self):
        command = ['ffmpeg.exe', '-y', '-i', self.inputfilePath]
        # 코덱 및 포맷 설정
        if self.cvtOpt=='hap':
            command.append('-c:v hap -c:a copy')
        elif self.cvtOpt=='hap_alpha':
            list = ['-c:v hap', '-c:a copy', '-format hap_alpha']
            command.extend(list)
        elif self.cvtOpt=='hap_q':
            list = ['-c:v hap', '-c:a copy', '-format hap_q']
            command.extend(list)
        elif self.cvtOpt=='copy':
            command.append('-c:v copy -c:a copy')
        else:
            command.append(' ')
        # 해상도 설정
        if self.originalRes is True:
            command.append(f'-vf scale={self.ori_resolution()}')
        elif self.scaleRatio is True:
            command.append(f'-vf scale={self.width}:-4')
        else:
            command.append(f'-vf scale={self.width}:{self.height}')
        # 스케일 알고리즘 설정
        if self.scaleAlgo != "":
            command.append(f'-sws_flags {self.scaleAlgo}')
        else:
            command.append(' ')
        # CPU 인코딩 설정
        command.append(f'-chunks {self.multiCPU}')  # default : 6
        # Add Script 설정
        command.append(f'{self.usrScript}')
        # 출력파일
        command.append(f'{self.outputfilePath}')
        return command

    def ori_resolution(self):
        return f'{self.ori_width}:{self.ori_height}'
    
    def getMaxFrame(self):
        return int(self.frameRate*self.duration)

    def getOptDict(self):
        dic = dict()
        dic['width'] = self.width
        dic['ori_width'] = self.ori_width
        dic['height'] = self.height
        dic['ori_height'] = self.ori_height
        dic['cvtOpt'] = self.cvtOpt
        dic['originalRes'] = self.originalRes
        dic['multiCPU'] = self.multiCPU
        dic['scaleRatio'] = self.scaleRatio
        dic['scaleAlgo'] = self.scaleAlgo
        dic['usrScript'] = self.usrScript
        return dic

    
#endregion 데이터클래스

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
#     UiShow = uiShow()
#     UiShow.show()
#     sys.exit(app.exec_())