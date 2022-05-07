
# import system module
import sys

# import some PyQt5 modules
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer
import PyQt5.QtCore as QtCore
from PyQt5.QtWidgets import QMessageBox

# import OpenCV module
import cv2 

# import other modules
import requests
import numpy as np
import json
import scipy.ndimage.filters as filters

# ipmort ui_main_window.py
from ui_main_window import *

#
from libs.htpa import *
#
from datetime import datetime

# Thermal camera driver
dev = HTPA(0x1A)
print("TN:" , dev.TABLENUMBER)
print("GlobalOffset:", dev.globalOff)
print("GlobalGain:", dev.globalGain)

try:
    with open("calibration.json", "r") as fp:
        calibrationDict = json.load(fp)

except IOError:
    print("Calibration file not found, will create a new one.")
    calibrationDict = {}
    calibrationDict['t25'] = 25.0
    calibrationDict['t45'] = 45.0

def remap(x,a,b,c,d):
    r = c + ((x - a)*(d - c)/(b - a))
    return r

def getObjectTemp():
    temp, fr = dev.get_frame_temperature()
    frame = np.asarray(fr, dtype = "float")
    kernel_size = 3
    filtered = filters.uniform_filter(frame, size = kernel_size, mode = "constant")
    weights = filters.uniform_filter(np.ones(filtered.shape), size = kernel_size, mode = "constant")
    filtered = filtered / weights # normalized convolution result
    tmax = fr.max()
    tmin = fr.min()
    tavg = np.average(fr)
    tobject = filtered.max()
    return (tobject, tmax, tmin, tavg)

if __name__ == '__main__':
    while True:
        (tobject, tmax, tmin, tavg) = getObjectTemp()
        print("{}: Tmax = {}, Tmin = {}, Tavg={}, T={}".format(str(datetime.now()), round(tmax, 2), round(tmin, 2), round(tavg, 2), round(tobject, 2)))
        with open("log.dat", "a") as fp:
            fp.write("{}: Tmax = {}, Tmin = {}, Tavg={}, T={}\r\n".format(str(datetime.now()), round(tmax, 2), round(tmin, 2), round(tavg, 2), round(tobject, 2)))