import os
import time
import sys


def resourcePath(relativePath):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        basePath = sys._MEIPASS
    except Exception:
        basePath = os.path.abspath(".")

    return os.path.join(basePath, relativePath)


def get_time(time_delta):
    return round((time.time() + time_delta) * 1000)


def get_time_delta():
    import ntplib
    client = ntplib.NTPClient()
    response = client.request('pool.ntp.org')
    return response.tx_time - time.time()
