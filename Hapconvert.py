#-*-coding: utf-8

import os, sys, ffmpeg, subprocess, asyncio, shlex, json, Happlay, webbrowser
from dataclasses import dataclass, fields
from dacite import from_dict
from PyQt5.QtWidgets import *
# from PyQt5.QtCore import *
from PyQt5 import uic, QtGui, QtCore
from tqdm import tqdm
from Applog import syslog as SL

if getattr(sys, 'frozen', False):
    root_path = sys._MEIPASS
else:
    root_path = os.getcwd()

# form_class = uic.loadUiType("hapconvert.ui")[0]
form_class = uic.loadUiType(os.path.join(root_path, "hapconvert.ui"))[0]

# log_file_path = f'{os.getcwd()}\\log\\hapConvertLog.log'
# app_title_icon_path = f'{os.getcwd()}\\resources\\app_title_icon.png'
# save_file_path = f'{os.getcwd()}\\Files'
# manual_file_path = f'{os.getcwd()}\\Manual\\html\\HAP_Convert_manual.html'
log_file_path = os.path.join(root_path, 'log', 'hapConvertLog.log')
app_title_icon_path = os.path.join(root_path, 'resources', 'app_title_icon.png')
save_file_path = os.path.join(root_path, 'Files')
manual_file_path = os.path.join(root_path, 'Manual', 'HAP_Convert_manual.html')

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
            scaleEnable=False,
            scaleRatio=False,
            scaleAlgo='none',
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
        # self.cb_aspertRatio.setEnabled(False)
        # self.cbb_algorithm.setEnabled(False)
        # self.bt_preViewer.setEnabled(False)
        # Json 파일 import

    def init_fileOpen(self):
        self.txt_fileinfo.clear()
        self.le_width.clear()
        self.le_height.clear()
        self.progress_bar.setValue(0)
        self.cb_originalRes.setCheckState(False)
        self.bt_preViewer.setEnabled(True)
        QApplication.processEvents()

    ## 메뉴얼 이벤트 콜백
    def openManual(self):
        try:
            webbrowser.open_new_tab(manual_file_path)
            self.statusBar().showMessage(f'메뉴얼 열기')
        except FileNotFoundError:
            self.statusBar().showMessage(f'메뉴얼 파일이 없습니다.')
            self.mCvtLog.warn(f'메뉴얼 파일 없음 {manual_file_path}')
            pass
        return
    
    ## 프로그램정보 이벤트 콜백
    def openInfo(self):
        pixmap = QtGui.QPixmap(app_title_icon_path)
        msg = QMessageBox()
        msg.setIconPixmap(pixmap)
        msg.setWindowIcon(QtGui.QIcon(app_title_icon_path))
        msg.setTextFormat(QtCore.Qt.RichText)
        msg.setWindowTitle("About Hap Convert")
        msg.setText(
            "<p><b>HAP Codec Convert</b><br><br>"
            "Copyright (C) 2023 leedg<br>"
            "Version : v1.0.0<br>"
            "Build Date : 2023.11.03<br>"
            "Licence : <a href=http://ffmpeg.org>FFmpeg</a> licensed under the <a href=http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html>LGPLv2.1</a>"
            "<br><br>"
            "이 소프트웨어는 LGPLv2.1에 따라 FFmpeg 프로젝트의 라이브러리를 사용합니다.<br>"
            "서비스 제공사의 허락없이 무단 복제사용을 금지합니다.<br>"
        )
        msg.exec_()
        return

    ## 설정 가져오기 이벤트 콜백
    def getImport(self):
        try:
            fname = QFileDialog.getOpenFileName(self, 'Import a option file', save_file_path, 'Option files(*.opt);;All files(*)')
            print(fname)
            
            if fname[0] != "":
                with open(fname[0], "r") as openfile:
                    load_file = json.load(openfile) # De-serialization json file and convert dict <type:dict>
                print(load_file)

                to_dataOpt = from_dict(data_class=DataOpt, data=load_file)  # set class variable from dict
                # 정의되지 않는 값
                notDefine = ["inputfilePath", "outputfilePath", "duration", "frameRate"]
                # 각 인스턴스의 필드값을 비교반복하여 업데이트
                for field in fields(DataOpt):
                    if field.name in notDefine:
                        pass
                    else:
                        setattr(self.dataOpt, field.name, getattr(to_dataOpt, field.name))

                # text box 설정
                if to_dataOpt.originalRes:
                    self.le_width.setText(str(to_dataOpt.ori_width))
                    self.le_height.setText(str(to_dataOpt.ori_height))
                else:
                    self.le_width.setText(str(to_dataOpt.width))
                    self.le_height.setText(str(to_dataOpt.height))

                if to_dataOpt.scaleRatio:
                    self.le_height.clear()
                    self.le_height.setEnabled(False)

                self.le_multicpu.setText(str(to_dataOpt.multiCPU))
                self.le_userScript.setText(to_dataOpt.usrScript)
                # combo box 설정
                self.cbb_option.setCurrentText(to_dataOpt.cvtOpt)
                self.cbb_algorithm.setCurrentText(to_dataOpt.scaleAlgo)
                # check box 설정
                # self.cb_scaleEnable.setEnabled(to_dataOpt.scaleEnable)
                self.cb_scaleEnable.setChecked(to_dataOpt.scaleEnable)
                # self.cb_originalRes.setEnabled(to_dataOpt.originalRes)
                self.cb_originalRes.setChecked(to_dataOpt.originalRes)
                # self.cb_aspertRatio.setEnabled(to_dataOpt.scaleRatio)
                self.cb_aspertRatio.setChecked(to_dataOpt.scaleRatio)
            else:
                self.statusBar().showMessage("옵션파일 불러오기 취소")
                return
        except Exception as e:
            self.mCvtLog.error(e)
        else:
            dir, file = os.path.split(fname[0])
            self.statusBar().showMessage(f'{dir}/{file}.opt 옵션파일 불러오기')
            self.mCvtLog.info(f'{dir}/{file}.opt 옵션파일 불러오기')

    ## 설정 내보내기 이벤트 콜백
    def saveExport(self):
        try:
            fname = QFileDialog.getSaveFileName(self, 'Export a option file', save_file_path, 'Option files(*.opt);;All files(*)')
            print(fname)

            if fname[0] != "":
                fileData = self.dataOpt.getOptDict()    # get dictionary
                serial_fileData = json.dumps(fileData, indent=11)   # serialization for json
                # 옵션 파일 쓰기
                with open(fname[0], "w") as outfile:
                    outfile.write(serial_fileData)
            else:
                self.statusBar().showMessage("옵션파일 저장 취소")
                return
        except Exception as e:
            self.mCvtLog.error(e)
        else:
            dir, file = os.path.split(fname[0])
            self.statusBar().showMessage(f'{dir}/{file}.opt 옵션파일 저장')
            self.mCvtLog.info(f'{dir}/{file}.opt 옵션파일 저장')

    #region private method 
    ## 파일정보
    # parameter : file path
    # return : fileinfo of dict type
    def func_fileinfo(self, path):
        dic = dict()
        try:
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
                    if 'display_aspect_ratio' in file_meta['streams'][0]:
                        ratio = stream['display_aspect_ratio']
                    else:
                        ratio = 'none'
                    pix_fmt = stream['pix_fmt']
                    list = frate.split('/')
                    frame = float(int(list[0])/int(list[1]))
                    bit_rate = float(int(bitrate) / (1000 * 1000))
                    file_size = float(int(size) / (1024 * 1024))

                    dic['video_codec'] = video_codec
                    dic['res_width'] = res_width
                    dic['res_height'] = res_height
                    dic['duration'] = duration
                    dic['frame'] = frame
                    dic['bit_rate'] = bit_rate
                    dic['file_size'] = file_size
                    dic['ratio'] = ratio
                    dic['pix_fmt'] = pix_fmt

                elif stream['codec_type'] == 'audio':
                    audio_codec = stream['codec_name']
                    sample_rate = stream['sample_rate']

                    dic['audio_codec'] = audio_codec
                    dic['sample_rate'] = sample_rate
        except ffmpeg.Error as e:
            print(e.stderr, file=sys.stderr)
            self.mCvtLog.error(e.stderr)
        finally:
            print(dic)
            pass

        return dic
    def find_listIndex(self, src_list, string, col):
        for i, s in enumerate(src_list):
            if string in s:
                if col == 0:
                    return i
                else:
                    return i + col
        return -1
    def cut_string(self, src_string, target_string, direction):
        """
        args:
            src_string : 문자열 소스
            target_string : 기준이 될 문자열
            direction : 기준에서 좌우 방향 ('L', 'R')
        return:
            처리된 문자열 반환
        """
        index = src_string.find(target_string)
        if index != -1:
            if direction == 'L':
                return src_string[index:]
            else:
                return src_string[:index + len(target_string)]
        return src_string

    #endregion private method
    
    #region 버튼 시그널
    # make a openfile dialog using Qt only video files
    def slot_fileOpen(self):
        result = None
        # [first_QC : 최초 파일경로는 바탕화면이고, 이후 열었던 경로로 변경 2023.11.02]
        if self.dataOpt.inputfilePath:
            DefaultPath = self.dataOpt.inputfilePath
        else:
            DefaultPath = os.path.join(os.path.expanduser('~'),'Desktop')
        self.init_fileOpen()
        fname = QFileDialog.getOpenFileName(self, 'Select a video file', DefaultPath, 'Video files(*.mp4 *.avi *.mkv *.mov *.webm);;All files(*)')
        print(fname)
        if fname[0] != "":
            try:
                file_path = fname[0]
                dir, file = os.path.split(file_path)
                fileCheck = file.split('.')
                if " " in file or " " in dir:
                    new_file_path = file_path.replace(' ', '_')
                    result = QMessageBox.question(
                        self,
                        "파일 공백처리 경고",
                        f'경로 및 파일명에 공백이 포함되어 있습니다. \n\n원래 파일명: {file_path}\n새 파일명: {new_file_path}\n\n새 파일명으로 저장하시겠습니까?',
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                        )
                    if result == QMessageBox.Yes:
                        os.rename(file_path, new_file_path)
                        file_path = new_file_path
                    else:
                        self.statusBar().showMessage("파일열기 취소")
                        return
                elif len(fileCheck) > 2:
                    result = QMessageBox.warning(self, "주의", "파일명에 확장자명은 하나만 지정해주세요", QMessageBox.Ok)
                    return
                
                self.le_fileInputPath.setText(file_path)
                self.txt_fileinfo.setText(f'[소스파일 : {file_path}]')
                self.dataOpt.inputfilePath = file_path
                fileinfo = self.func_fileinfo(file_path) # [first_QC : fileinfo 함수 진입 순서 변경 2023.11.02]

                if len(fileinfo) > 0:
                    self.dataOpt.ori_width = fileinfo['res_width']
                    self.dataOpt.ori_height = fileinfo['res_height']
                    self.dataOpt.frameRate = float(fileinfo["frame"])
                    self.dataOpt.duration = float(fileinfo["duration"])
                    self.txt_fileinfo.append(f'Video Codec : {fileinfo["video_codec"]}')
                    self.txt_fileinfo.append(f'bit rate : {fileinfo["bit_rate"]:.2f} Mb/s')
                    self.txt_fileinfo.append(f'Resolution : {str(fileinfo["res_width"])} x {str(fileinfo["res_height"])}')
                    self.txt_fileinfo.append(f'Ratio : {str(fileinfo["ratio"])}')
                    self.txt_fileinfo.append(f'Pixel format : {str(fileinfo["pix_fmt"])}')
                    self.txt_fileinfo.append(f'Frame rate : {fileinfo["frame"]}')
                    self.txt_fileinfo.append(f'Duration : {str(fileinfo["duration"])} (sec)')
                    self.txt_fileinfo.append(f'File Size : {fileinfo["file_size"]:.2f} Mbytes')
                    if 'audio_codec' and 'sample_rate' in fileinfo:
                        self.txt_fileinfo.append(f'Audio Codec : {fileinfo["audio_codec"]}')
                        self.txt_fileinfo.append(f'Audio Sample rate : {str(fileinfo["sample_rate"])}')
                    else:
                        self.txt_fileinfo.append(f'Audio Codec : none')
                        self.txt_fileinfo.append(f'Audio Sample rate : none')
                else:
                    self.mCvtLog.error(f'파일정보없음 : {fileinfo} {dir}/{file}')
            except ffmpeg.Error as e:
                print(e.stderr, file=sys.stderr)
                self.txt_fileinfo.setText(e.stderr)
                self.mCvtLog.error(e.stderr)
                pass
            except Exception as e:
                self.mCvtLog.error(f'파일열기 실패 : {e}')
                self.statusBar().showMessage(f'파일열기 실패')
                pass
        else:
            self.statusBar().showMessage("파일열기 취소")
    
    # make a savefile dialog using Qt only video files
    def slot_fileSave(self):
        if self.dataOpt.inputfilePath:
            DefaultPath = self.dataOpt.inputfilePath
        else:
            DefaultPath = os.path.join(os.path.expanduser('~'),'Desktop')
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
            pass

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
                pass
            else:
                self.mCvtLog.info(f'Play video input file : {cmd}')
        elif self.dataOpt.inputfilePath != "" and self.dataOpt.outputfilePath != "":    # 둘다 있는 경우   
            print(self.dataOpt.inputfilePath, self.dataOpt.outputfilePath)
            input_cmd = f'mplayer {self.dataOpt.inputfilePath} -xy 960 -loop 0 -geometry 10:50 -use-filename-title'
            output_cmd = f'mplayer {self.dataOpt.outputfilePath} -xy 960 -loop 0 -geometry 10:550 -use-filename-title'
            try:
                asyncio.run(self.task_preview(inputCmd=input_cmd, outputCmd=output_cmd))    # 복수 실행
            except Exception as e:
                self.mCvtLog.error(f'Play error : {e}')
                pass
            else:
                self.mCvtLog.info(f'Play video input file : {input_cmd}')
                self.mCvtLog.info(f'Play video output file : {output_cmd}')
        else:   # 입력파일이 없는 경우
            self.mCvtLog.warning(f'{self.dataOpt.inputfilePath} 입력파일이 없습니다.')
            return
    
    # start convert to a Hap codec 
    def slot_fileConvert(self):
        self.subProc.progress = 0
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
            self.statusBar().showMessage(f'변환오류 : {e}')
            self.subProc.run = False
            print(f'변환오류 : {e}')
        else:
            fileinfo = self.func_fileinfo(self.dataOpt.outputfilePath)
            if len(fileinfo) > 0:
                self.txt_fileinfo.append(f'=====================출력파일정보=====================')
                self.txt_fileinfo.append(f'출력파일 : {self.dataOpt.outputfilePath}')
                self.txt_fileinfo.append(f'Video Codec : {fileinfo["video_codec"]}')
                self.txt_fileinfo.append(f'bit rate : {fileinfo["bit_rate"]:.2f} Mb/s')
                self.txt_fileinfo.append(f'Resolution : {str(fileinfo["res_width"])} x {str(fileinfo["res_height"])}')
                self.txt_fileinfo.append(f'Frame rate : {fileinfo["frame"]}')
                self.txt_fileinfo.append(f'Duration : {str(fileinfo["duration"])} (sec)')
                self.txt_fileinfo.append(f'File Size : {fileinfo["file_size"]:.2f} Mbytes')
                if 'audio_codec' and 'sample_rate' in fileinfo:
                    self.txt_fileinfo.append(f'Audio Codec : {fileinfo["audio_codec"]}')
                    self.txt_fileinfo.append(f'Audio Sample rate : {str(fileinfo["sample_rate"])}')
                else:
                    self.txt_fileinfo.append(f'Audio Codec : none')
                    self.txt_fileinfo.append(f'Audio Sample rate : none')
                self.mCvtLog.info(f'파일변환 : I[{self.dataOpt.inputfilePath}] --> O[{self.dataOpt.outputfilePath}]')
            else:
                self.mCvtLog.error(f'파일정보오류 : fileinfo {fileinfo}')
                return
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
            self.dataOpt.scaleAlgo = "none" # [first_QC : 옵션 비활성화일때 알고리즘 'none' 변경 2023.11.02]
            self.dataOpt.scaleEnable = False
            self.dataOpt.originalRes = True
        else:
            self.cb_aspertRatio.setEnabled(True)
            self.cbb_algorithm.setEnabled(True)
            self.cb_originalRes.setChecked(False)
            self.cb_originalRes.setEnabled(False)
            self.dataOpt.originalRes = False
            self.dataOpt.scaleAlgo = self.cbb_algorithm.currentText() # [first_QC : 옵션 활성화 전환시 선택된 알고리즘 적용 2023.11.02]
            self.dataOpt.scaleEnable = True

    # 종횡비 고정
    def slot_fixedRatioCheck(self):
        codec = self.dataOpt.cvtOpt
        if self.cb_aspertRatio.isChecked() == False:
            self.le_height.setEnabled(True)
            self.dataOpt.scaleRatio = False
        else:
            self.le_height.setEnabled(False)
            self.cb_originalRes.setEnabled(False)
            self.dataOpt.scaleRatio = True
            if codec == 'none':
                self.dataOpt.height = -1
            else:
                self.dataOpt.height = -4
            self.statusBar().showMessage("원본해상도 비율고정.")
    #endregion 체크박스 시그널

    #region 콤보박스 시그널
    # 코덱
    def slot_getOpt(self):
        self.dataOpt.cvtOpt = self.cbb_option.currentText()
        if self.dataOpt.cvtOpt == "none":   
            self.statusBar().showMessage(f'코덱:{self.dataOpt.cvtOpt} 기본 h.264로 변환됩니다.')
        else:   # [first_QC : 코덱 none 일때 아닐때 처리 변경 2023.11.02]
            self.statusBar().showMessage(f'코덱: {self.dataOpt.cvtOpt}')
    
    # Scale 알고리즘
    def slot_getAlgoOpt(self):
        self.dataOpt.scaleAlgo = self.cbb_algorithm.currentText()
        self.statusBar().showMessage(f'변환 알고리즘: {self.dataOpt.scaleAlgo}')
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

    # 해상도 변경 : int
    def slot_widthEdit(self):
        width = self.le_width.text()
        if width:
            self.dataOpt.width = int(width)
        else:
            width = self.dataOpt.width
        self.statusBar().showMessage(f'가로해상도 : {width}')
    
    def slot_heightEdit(self):
        height = self.le_height.text()
        if height:
            self.dataOpt.height = int(height)
        else:
            height = self.dataOpt.height
        self.statusBar().showMessage(f'세로해상도 : {height}')

    # 코어수 변경 : int
    def slot_multicpuEdit(self):
        multiCPU = self.le_multicpu.text()
        if multiCPU:
            self.dataOpt.multiCPU = int(multiCPU)
        else:
            multiCPU = self.dataOpt.multiCPU
        self.statusBar().showMessage(f'코어수 : {multiCPU}')
    
    # 사용자스크립트 변경 : str
    def slot_addScriptEdit(self):
        script = self.le_userScript.text()
        self.dataOpt.usrScript = script
        self.statusBar().showMessage(f'사용자 스크립트 적용')
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
                stderr=asyncio.subprocess.STDOUT,
            )
            self.subProc.pid = proc.pid
            self.subProc.run = True
            log = b''
            while proc.returncode is None:  # [first_QC : byte 단위로 한글을 끊어서 읽으면, UnicodeDecodeError 발생 2023.11.02]
                buf = await proc.stdout.read(128)    
                if not buf:
                    break
                else:
                    if b'frame=' in buf:
                        frame = buf.decode().split(' ')
                        frame = [v for v in frame if v]
                        index = self.find_listIndex(frame, 'frame', 1) # return -1 not found, 'frame' 다음 인덱스를 lookup
                        if index > 0 and len(frame) != index:   # [first_QC : index 길이값이 list를 초과 error 처리 2023.11.02]    
                            total_line = int(frame[index])
                            log = buf
                    elif b'failed' in buf:
                        raise Exception(f'변환실패-{buf}')
                    await self.update_progress_value(total_line)
                print(f'[{total_line}] [{log}]')
            log = self.cut_string(log.decode(), "frame", "L")
            result = subprocess.CompletedProcess(cmd, proc.returncode, stdout=log, stderr=b'')
        except subprocess.CalledProcessError as e:
            self.subProc.run = False
            print(f'[Error Subprocess] {e.output}')
            self.statusBar().showMessage("프로세스 애러!")
            self.mCvtLog.error(e.output)
            pass
        except Exception as e:
            self.subProc.run = False
            self.mCvtLog.error(f'[Error] {e}')
            print(f'[Error] {e}')
            if 'UnicodeDecodeError' in e:
                self.statusBar().showMessage("디코딩오류로 변환실패")
            else:
                self.statusBar().showMessage("변환실패")
            pass
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
    scaleEnable: bool
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
    def scaleEnable(self): return self._scaleEnable
    @scaleEnable.setter
    def scaleEnable(self, value): self._scaleEnable = value

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
        if not self.scaleAlgo == 'none':
            command.append(f'-sws_flags {self.scaleAlgo}')
        elif self.scaleAlgo == ' ': #예외 처리
            command.append(' ')
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
        dic['scaleEnable'] = self.scaleEnable
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