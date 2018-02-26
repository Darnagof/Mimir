# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'design.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(645, 502)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.graphicsView = QtWidgets.QGraphicsView(self.centralwidget)
        self.graphicsView.setObjectName("graphicsView")
        self.verticalLayout.addWidget(self.graphicsView)
        self.btnSave = QtWidgets.QPushButton(self.centralwidget)
        self.btnSave.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.btnSave.setObjectName("btnSave")
        self.verticalLayout.addWidget(self.btnSave)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menuBar = QtWidgets.QMenuBar(MainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 645, 26))
        self.menuBar.setObjectName("menuBar")
        self.menuFiles = QtWidgets.QMenu(self.menuBar)
        self.menuFiles.setObjectName("menuFiles")
        MainWindow.setMenuBar(self.menuBar)
        self.actionLoadFile = QtWidgets.QAction(MainWindow)
        self.actionLoadFile.setObjectName("actionLoadFile")
        self.menuFiles.addAction(self.actionLoadFile)
        self.menuBar.addAction(self.menuFiles.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.btnSave.setText(_translate("MainWindow", "Save Section"))
        self.menuFiles.setTitle(_translate("MainWindow", "File"))
        self.actionLoadFile.setText(_translate("MainWindow", "LoadFile"))

