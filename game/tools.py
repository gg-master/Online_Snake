import os
import sys
import calendar
import time


def resourcePath(relativePath):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        basePath = sys._MEIPASS
    except Exception:
        basePath = os.path.abspath(".")

    return os.path.join(basePath, relativePath)


def get_time():
    # Возвращаем время по гринвичу. Вроде выдает одинаковый результат с
    # разных точек мира
    return calendar.timegm(time.gmtime())
