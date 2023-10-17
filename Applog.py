import logging
import logging.handlers

class syslog:
    def __init__(self, name):
        self.log = logging.getLogger(name)
        self.log.propagate = True
        self.log.setLevel(logging.DEBUG)
        self.formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s',
                                           "%Y-%m-%d %H:%M:%S")
        self.levels = {"DEBUG" : logging.DEBUG ,
                       "INFO" : logging.INFO ,
                       "WARNING" : logging.WARNING ,
                       "ERROR" : logging.ERROR ,
                       "CRITICAL" : logging.CRITICAL }

    def stream_handler(self, level):
        streamHandler = logging.StreamHandler()
        streamHandler.setLevel(self.levels[level])
        streamHandler.setFormatter(self.formatter)
        self.log.addHandler(streamHandler)
        return self.log

    def file_handler(self, filename, mode, level):
        """
        filename : ~.log
        mode : w or a
        """
        fileHandler = logging.FileHandler(filename, mode= mode)
        fileHandler.setLevel(self.levels[level])
        fileHandler.setFormatter(self.formatter)
        self.log.addHandler(fileHandler)
        return self.log

    def rotating_filehandler(self, filename, mode, level, backupCount, logMaxSize):
        """
        filename : ~.log
        mode : w or a
        backupCount : backup할 파일 개수
        log_max_size : 한 파일당 용량 최대
        """
        fileHandler = logging.handlers.RotatingFileHandler(
            filename=filename ,
            mode=mode ,
            backupCount=backupCount ,
            maxBytes=logMaxSize
        )
        fileHandler.setLevel(self.levels[level])
        fileHandler.setFormatter(self.formatter)
        self.log.addHandler(fileHandler)
        return self.log

    def timeRotate_handler(self, filename, when, level, backupCount, interval):
        """
        file_name :
        when : 저장 주기
        interval : 저장 주기에서 어떤 간격으로 저장할지
        backupCount : 5
        atTime : datetime.time(0, 0, 0)
        """
        fileHandler = logging.handlers.TimedRotatingFileHandler(
            filename=filename,
            when=when,
            backupCount=backupCount,
            interval=interval
        )
        fileHandler.setLevel(self.levels[level])
        fileHandler.setFormatter(self.formatter)
        self.log.addHandler(fileHandler)
        return self.log

# if __name__ == '__main__':
#     file_path = f'{os.getcwd()}\\log\\TestLog.log'
#     mplayLog = syslog('playerlogger')
#     # mplayLog.stream_handler("INFO")
#     logger = mplayLog.rotating_filehandler(
#         filename=file_path,
#         mode='a',
#         level="DEBUG",
#         backupCount=5,
#         logMaxSize=1048576
#         )
    
#     logger.debug("2023.09.07")
#     logger.debug(f'Files path : {file_path}')

#     idx = 0
#     while True :
#         logger.debug('debug {}'.format(idx))
#         logger.info('info {}'.format(idx))
#         logger.warning('warning {}'.format(idx))
#         logger.error('error {}'.format(idx))
#         logger.critical('critical {}'.format(idx))
#         idx += 1
#         if idx ==10 :
#             break
