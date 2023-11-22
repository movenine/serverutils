# HAP Convert README

서버에 설치되는 유틸리티 프로그램으로 HAP 코덱 변환 및 미리보기를 지원하는 툴킷이다.
코덱 변환은 ffmpeg 라이브러리를 활용하였다.

## Project Overview

[![language](https://img.shields.io/badge/language-python_%7C_PyQt5-blue)]
[![project status](https://img.shields.io/badge/Tested-100%25-blue?color=green)](https://github.com/movenine/serverutils.git)

## Features

- 미디어 파일 정보 표출
- 미디어 파일 열기 및 저장
- HAP / HAP-Q / HAP-Alpha 코덱 지원
- 변환파일 미리보기
- 변환옵션 저장 및 불러오기

## Build & Install

- Python 3.8.10 가상환경 생성
- 패키지 설치 : pip install -r requirements.txt
- 빌드 : pyinstaller Utiltray.spec
- 빌드생성경로 : {project folder}\ServerUtils\dist\Utiltray_v100
- 라이브러리 파일 : [ffmpeg](https://ffmpeg.org/download.html), [mplayer](https://www.mplayerhq.hu/design7/dload.html)
- 환경변수 : C:\Program Files\ServerUtils\ `your_lib_folder` \ffmpeg\bin, C:\Program Files\ServerUtils\ `your_lib_folder` \MPlayer 
- [inno setup complier](https://jrsoftware.org/isinfo.php)를 사용하여 라이브러리 폴더와 환경변수 설정이 포함된 Installer package 생성

## Install folder configuration

- `files` *.opt 옵션파일 저장폴더
- `log` hapConvertLog.log, playerLog.log 로깅 폴더
- `manual` html 형식의 메뉴얼 폴더
- `resource` 아이콘 파일폴더
- `Utiltray.exe` 실행파일
- 기타 python 구동을 위한 파일

