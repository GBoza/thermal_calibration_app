
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

class MainWindow(QtWidgets.QMainWindow):
    # class constructor
    def __init__(self, parent = None):
        # call QWidget constructor
        super(MainWindow, self).__init__(parent=parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # create a timer
        self.timer = QTimer()
        # set timer timeout callback function
        self.timer.timeout.connect(self.update_window)
        
        self.timer.start(100)
        self.counter = 0
        
        # set pushButton callback clicked function
        self.ui.pushButton.clicked.connect(self.calibration_25)
        # set pushButton_2 callback clicked function
        self.ui.pushButton_2.clicked.connect(self.calibration_45)

        self._t25 = calibrationDict['t25'] #lectura de sensor a 25°C
        self._t45 = calibrationDict['t45'] #lectura de sensor a 45°C
    
    def recalcularTemp(self, value):
        # y = m * x + b
        # m = 20 / (t45 - t25)
        # b = 25 - 20 * t25 / (t45 - t25)
        m = 20.0 / (self._t45 - self._t25)
        b = 25.0 - 20.0 * self._t25 / (self._t45 - self._t25)
        return (m * value + b)

    def calibration_25(self):
        acc = 0.0
        # toma 8 lecturas y realiza promedio
        for i in range(0, 8):
            t, fr = dev.get_frame_temperature()
            (tobject, tmax, tmin, tavg) = self.getObjectTemp(fr)
            acc = acc + tobject
        acc = acc / 8 
        self._t25 = acc
        print("t25: ", self._t25)
        calibrationDict['t25'] = self._t25
        with open("calibration.json", "w") as fp:
            json.dump(calibrationDict, fp, indent=4)
    
    def calibration_45(self):
        acc = 0.0
        # toma 8 lecturas y realiza promedio
        for i in range(0, 8):
            t, fr = dev.get_frame_temperature()
            (tobject, tmax, tmin, tavg) = self.getObjectTemp(fr)
            acc = acc + tobject
        acc = acc / 8
        self._t45 = acc
        print("t45: ", self._t45)
        calibrationDict['t45'] = self._t45
        with open("calibration.json", "w") as fp:
            json.dump(calibrationDict, fp, indent=4)
    
    def update_window(self):
        temp, fr1 = dev.get_frame_temperature()
        temp, fr2 = dev.get_frame_temperature()
        fr = (fr1 + fr2) / 2
        #temp, fr = dev.get_frame_temperature()
        #remap_fr = remap(fr, fr.min(), fr.max(), 0, 255) # remap
        remap_fr = remap(fr, 10, 50, 0, 255) # remap 0°C to 50°C
        remap_fr = np.round(remap_fr) # round
        remap_fr = remap_fr.astype(np.uint8) # as 8bit
        #img_thermal = cv2.applyColorMap(remap_fr, cv2.COLORMAP_HOT) # colormap
        img_thermal = cv2.applyColorMap(remap_fr, cv2.COLORMAP_JET) # colormap
        img_thermal = cv2.resize(img_thermal, (256,256), interpolation = cv2.INTER_NEAREST) #interpolation
        
        img_thermal = cv2.cvtColor(img_thermal, cv2.COLOR_BGR2RGB)
        
        # get image infos
        height, width, channel = img_thermal.shape
        step = channel * width
        # create QImage from image
        qImg = QImage(img_thermal.data, width, height, step, QImage.Format_RGB888)
        # show image in label
        self.ui.label.setPixmap(QPixmap.fromImage(qImg)) 
        
        #################################################
        (tobject, tmax, tmin, tavg) = self.getObjectTemp(fr)

        self.ui.label_tmax.setText("Tmax: " + str(round(self.recalcularTemp(tmax), 2)) + "°C")
        self.ui.label_tmin.setText("Tmin: " + str(round(self.recalcularTemp(tmin), 2)) + "°C")
        self.ui.label_tavg.setText("Tavg: " + str(round(self.recalcularTemp(tavg), 2)) + "°C")
        self.ui.lcdNumber.setProperty("value", str(round(self.recalcularTemp(tobject), 1)))
    
    def getObjectTemp(self, frame):
        frame = np.asarray(frame, dtype = "float")
        kernel_size = 3
        filtered_frame = filters.uniform_filter(frame, size = kernel_size, mode = "constant")
        weights = filters.uniform_filter(np.ones(filtered_frame.shape), size = kernel_size, mode = "constant")
        filtered_frame = filtered_frame / weights # normalized convolution result
        tmax = frame.max()
        tmin = frame.min()
        tavg = np.average(frame)
        tobject = filtered_frame.max()
        return (tobject, tmax, tmin, tavg)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    # create and show mainWindow
    mainWindow = MainWindow()
    mainWindow.show()
    
    sys.exit(app.exec_())
