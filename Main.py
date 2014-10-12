# -*- coding: utf-8 -*-
'''
Created on 2014年9月16日

@author: Ying
'''

import sys
from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import Qt
from PyQt4.QtCore import pyqtSignal
from MainWindow_ui import Ui_MainWindow
import requests
import json
import serial
import threading


class BusyBar(QtGui.QProgressDialog):

    def __init__(self, text=""):
        super(BusyBar, self).__init__()
        self.text = text
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setRange(0, 0)
        self.setLabelText(self.text)
        self.setValue(0)
        self.setFixedSize(500, 100)
        self.setAutoClose(False)
        self.setWindowModality(Qt.Qt.WindowModal)


class SerialThread(threading.Thread):
    def __init__(self, com):
        threading.Thread.__init__(self)
        self.thread_stop = False
        self.ser = serial.Serial(com)
        self.ser.baudrate = 115200
        print(self.ser.isOpen())
        self.id = 0

        self.myCommunicator = MyCommunicator()

    def run(self):
        while not self.thread_stop:
            try:
                data = self.ser.readline()
                self.id = data
#                 print(self.id)
#                 print("before sendsignal")
                self.myCommunicator.sendSignal()
#                 print("after sendsignal")
            except:
                print("readline fail")

    def stop(self):
        if self.ser.isOpen():
            self.ser.close()
        print(self.ser.isOpen())
        self.thread_stop = True


class MyCommunicator(QtCore.QObject):

    trigger = pyqtSignal(name='SerialDataReceived')

    def __init__(self, parent=None):
        super(MyCommunicator, self).__init__()

    def sendSignal(self):
        self.trigger.emit()


class MyMainWindow(Ui_MainWindow):

    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__()
        # QtGui.QMainWindow.__init__(self,parent)
        self.ui = Ui_MainWindow(self)
        self.ui.setupUi(self)
        self.setupConnect()

        self.isOpenCom = False

        self.serverURL = 'http://166.111.53.137:8080/makerPlus/servlet/'
#         self.serverURL = 'http://59.66.81.161:8080/makerPlus/servlet/'
#         self.serverURL = 'http://172.27.35.42:8080/makerPlus/servlet/'
#         self.busyBar = BusyBar("Connecting to Server...")
#         self.busyBar.setLabelText("Connecting")
#         self.busyBar.show()
        try:
            self.eventList = requests.get(self.serverURL + 'Event').json()
            self.updateEventList(self.eventList)
            self.eventSelected()
#             self.busyBar.close()
        except:
#             self.busyBar.close()
            QtGui.QMessageBox.warning(self, "Error", "Can't connect to server",
                                              QtGui.QMessageBox.Cancel, QtGui.QMessageBox.NoButton,
                                              QtGui.QMessageBox.NoButton)

        strFileType = "TXT File (*.txt)"
        self.localFilePath = QtGui.QFileDialog.getSaveFileName(self,
                "Save MSpectrum",
                "/home",
                strFileType)

    def __del__(self):
        print("in del")
        try:
            self.mySerialThread.stop()
        except:
            pass

    def setupConnect(self):
        self.ui.pushButton.clicked.connect(self.upLoad)
#         self.ui.comboBox.currentIndexChanged.connect(self.eventSelected)
        self.ui.comboBox.activated.connect(self.eventSelected)
        self.ui.pushButton_openCom.clicked.connect(self.onPressCom)

    def upLoad(self):
        uploadParameters = dict()
        for i in range(len(self.currentEventParameters)):
            if i == 0:
                uploadParameters[self.currentEventParameters[i]] = self.ui.lineEdit_1.text()
            elif i == 1:
                uploadParameters[self.currentEventParameters[i]] = self.ui.lineEdit_2.text()
            elif i == 2:
                uploadParameters[self.currentEventParameters[i]] = self.ui.lineEdit_3.text()
            elif i == 3:
                uploadParameters[self.currentEventParameters[i]] = self.ui.lineEdit_4.text()
            elif i == 4:
                uploadParameters[self.currentEventParameters[i]] = self.ui.lineEdit_5.text()
            elif i == 5:
                uploadParameters[self.currentEventParameters[i]] = self.ui.lineEdit_6.text()
            elif i == 6:
                uploadParameters[self.currentEventParameters[i]] = self.ui.lineEdit_7.text()
            elif i == 7:
                uploadParameters[self.currentEventParameters[i]] = self.ui.lineEdit_8.text()

        r = requests.post(self.serverURL + "Event?EventName=" + self.currentEventName, data={'data': str(uploadParameters)})
#         r = requests.post(self.serverURL + "Event?EventName=" + self.currentEventName, data={'data': u"{'some':'毕滢'}"})
        print(r.text)
        if r.status_code != 200:
            QtGui.QMessageBox.warning(self, "Error",
                                              "Upload Error: " + str(r.status_code),
                                              QtGui.QMessageBox.Cancel, QtGui.QMessageBox.NoButton,
                                              QtGui.QMessageBox.NoButton)
        else:
            isShowDialog = False
            if self.currentEventName == "RegisterEvent":
                dialogShowStr = r.text
                isShowDialog = True
            elif self.currentEventName == "CheckEvent":
                memberInfo = r.json()
                phoneNum = memberInfo["电话"]
                showPhoneNum = "手机尾号:" + phoneNum[len(phoneNum) - 4:len(phoneNum)]
                self.ui.label_return_info_1.setText(memberInfo["姓名"])
                self.ui.label_return_info_2.setText(showPhoneNum)
                isShowDialog = False
            elif self.currentEventName == "LotteryEvent":
                memberInfo = r.json()
                phoneNum = memberInfo["电话"]
                showPhoneNum = "手机尾号:" + phoneNum[len(phoneNum) - 4:len(phoneNum)]
                self.ui.label_return_info_1.setText(memberInfo["姓名"])
                self.ui.label_return_info_2.setText(showPhoneNum)
                dialogShowStr = "获得15点经验值！！"
                isShowDialog = True

            if isShowDialog:
                QtGui.QMessageBox.warning(self, "Done!",
                                                  dialogShowStr,
                                                  QtGui.QMessageBox.Information, QtGui.QMessageBox.NoButton,
                                                  QtGui.QMessageBox.NoButton)

            self.f = open(self.localFilePath, 'a')
            self.f.write(str(uploadParameters))
            self.f.write(" ")
            self.f.write(r.text)
#             self.f.write("\n")
            self.f.close()

            # copy id to clipboard
            clipboard = QtGui.QApplication.clipboard()
            mimeData = QtCore.QMimeData()
#             mimeData.setText(r.text)
            mimeData.setText(r.text[0:len(r.text) - 2])
            clipboard.setMimeData(mimeData)

    def updateEventList(self, eventList):
        self.ui.comboBox.clear()
        for i in range(len(eventList)):
            self.ui.comboBox.addItem(eventList[i])

    def eventSelected(self):
        self.currentEventName = self.eventList[self.ui.comboBox.currentIndex()]
        self.currentEventParameters = requests.get(self.serverURL + 'Event?EventName=' + self.currentEventName).json()
#         self.currentEventParameters = requests.get(self.serverURL + 'Tester').json()

        # clean label text
        self.ui.label_1.setText("")
        self.ui.label_2.setText("")
        self.ui.label_3.setText("")
        self.ui.label_4.setText("")
        self.ui.label_5.setText("")
        self.ui.label_6.setText("")
        self.ui.label_7.setText("")
        self.ui.label_8.setText("")

        for i in range(len(self.currentEventParameters)):
            if i == 0:
                self.ui.label_1.setText(self.currentEventParameters[i])
            elif i == 1:
                self.ui.label_2.setText(self.currentEventParameters[i])
            elif i == 2:
                self.ui.label_3.setText(self.currentEventParameters[i])
            elif i == 3:
                self.ui.label_4.setText(self.currentEventParameters[i])
            elif i == 4:
                self.ui.label_5.setText(self.currentEventParameters[i])
            elif i == 5:
                self.ui.label_6.setText(self.currentEventParameters[i])
            elif i == 6:
                self.ui.label_7.setText(self.currentEventParameters[i])
            elif i == 7:
                self.ui.label_8.setText(self.currentEventParameters[i])

    def onPressCom(self):
        if not self.isOpenCom:
            try:
                self.mySerialThread = SerialThread(int(self.ui.lineEdit_com.text()) - 1)
                self.mySerialThread.myCommunicator.trigger.connect(self.updateIDfromSerial)
                self.mySerialThread.start()
                self.isOpenCom = True
                self.ui.pushButton_openCom.setText("关闭串口")
            except:
                self.mySerialThread.stop()
                QtGui.QMessageBox.warning(self, "Error",
                                                  "Can't open Com",
                                                  QtGui.QMessageBox.Cancel, QtGui.QMessageBox.NoButton,
                                                  QtGui.QMessageBox.NoButton)
        else:
            self.mySerialThread.stop()
            self.isOpenCom = False
            self.ui.pushButton_openCom.setText("开启串口")

    def updateIDfromSerial(self):
        self.id = self.mySerialThread.id
        if not self.currentEventName == "RegisterEvent":
            idStr = str(self.id)
            self.ui.lineEdit_1.setText(idStr[2:len(idStr) - 5])
        print(self.id)

app = QtGui.QApplication(sys.argv)
widget = MyMainWindow()
widget.show()
sys.exit(app.exec_())
