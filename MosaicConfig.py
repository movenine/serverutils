import os, sys
import subprocess
from dataclasses import dataclass
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QRunnable, QThreadPool, QObject, pyqtSignal, QThread
from PyQt5 import uic

form_class = uic.loadUiType("mosaicConfig.ui")[0]
