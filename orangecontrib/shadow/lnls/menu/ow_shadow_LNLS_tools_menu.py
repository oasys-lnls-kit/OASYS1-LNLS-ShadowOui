__author__ = 'labx'

from PyQt5 import QtWidgets
from oasys.menus.menu import OMenu

class ShadowLNLSToolsMenu(OMenu):

    def __init__(self):
        super().__init__(name="Shadow LNLS Tools")

        self.openContainer()
        self.addContainer("Container 1")
        self.addSubMenu("Submenu 1.1")
        self.addSubMenu("Submenu 1.2")
        self.closeContainer()
        self.openContainer()
        self.addContainer("Container 2")
        self.addSubMenu("Submenu 2.1")
        self.addSubMenu("Submenu 2.2")
        self.addSeparator()
        self.addSubMenu("Submenu 2.3")
        self.closeContainer()
        self.addSeparator()
        self.addSubMenu("Submenu 3")

    def executeAction_1(self, action):
        try:
            self.showWarningMessage("Submenu 1.1")

        except Exception as exception:
            self.showCriticalMessage(exception.args[0])

    def executeAction_2(self, action):
        try:
            self.showWarningMessage("Submenu 1.2")

        except Exception as exception:
            self.showCriticalMessage(exception.args[0])

    #ENABLE PLOTS
    def executeAction_3(self, action):
        try:
            self.showWarningMessage("Submenu 2.1")

        except Exception as exception:
            self.showCriticalMessage(exception.args[0])

    def executeAction_4(self, action):
        try:
            self.showWarningMessage("Submenu 2.2")

        except Exception as exception:
            self.showCriticalMessage(exception.args[0])

    def executeAction_5(self, action):
        try:
            self.showWarningMessage("Submenu 2.3")

        except Exception as exception:
            self.showCriticalMessage(exception.args[0])

    def executeAction_6(self, action):
        try:
            self.showWarningMessage("Submenu 3")

        except Exception as exception:
            self.showCriticalMessage(exception.args[0])


    ###############################################################
    #
    # MESSAGING
    #
    ###############################################################

    def showConfirmMessage(self, message, informative_text):
        msgBox = QtWidgets.QMessageBox()
        msgBox.setIcon(QtWidgets.QMessageBox.Question)
        msgBox.setText(message)
        msgBox.setInformativeText(informative_text)
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.No)

        return msgBox.exec_()

    def showWarningMessage(self, message):
        msgBox = QtWidgets.QMessageBox()
        msgBox.setIcon(QtWidgets.QMessageBox.Warning)
        msgBox.setText(message)
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgBox.exec_()

    def showCriticalMessage(self, message):
        msgBox = QtWidgets.QMessageBox()
        msgBox.setIcon(QtWidgets.QMessageBox.Critical)
        msgBox.setText(message)
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgBox.exec_()

