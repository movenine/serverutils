import subprocess, os, sys
import asyncio
from dataclasses import dataclass
from Applog import syslog as SL

if getattr(sys, 'frozen', False):
    root_path = sys._MEIPASS
else:
    root_path = os.getcwd()

log_file_path = os.path.join(root_path, 'log', 'playerLog.log')
# log_file_path = f'{os.getcwd()}\\log\\playerLog.log'

mplayLog = SL('playerlogger')
mplayLog = mplayLog.rotating_filehandler(
    filename=log_file_path,
    mode='a',
    level="DEBUG",
    backupCount=10,
    logMaxSize=1048576
    )

async def mPlay(cmd):
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        proc_log,_ = await proc.communicate()
        lines = proc_log.decode('utf-8')
        line = lines.split('\r\n') # \r 문자로 구분 리스트
        line = [v for v in line if v]  # 공백 제거한 리스트
        mplayLog.info('\n'.join(line))
        await proc.wait()  
    except subprocess.CalledProcessError as e:
        mplayLog.error(e.output)
    except Exception as e:
        mplayLog.error(e)

# if __name__ == '__main__':
#     log_file_path = f'{os.getcwd()}\\Files'
#     file_list = os.listdir(log_file_path)
#     cmd = f'mplayer "{log_file_path}\\{file_list[1]}" -vf scale=1920:-1 -x 1920 -use-filename-title'
#     asyncio.run(mPlay(cmd))