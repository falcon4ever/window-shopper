import time


class SimpleLogger:

    def __init__(self, name):
        self.logger_name = name

    def info(self, message):
        print(f'{time.ctime()} - {self.logger_name} - INFO - {message}')

    def warning(self, message):
        print(f'{time.ctime()} - {self.logger_name} - WARNING - {message}')

    def error(self, message):
        print(f'{time.ctime()} - {self.logger_name} - ERROR - {message}')
