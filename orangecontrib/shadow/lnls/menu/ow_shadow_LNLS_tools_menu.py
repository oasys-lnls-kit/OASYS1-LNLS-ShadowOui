__author__ = 'labx'

from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap
from orangecanvas.scheme.link import SchemeLink
from oasys.menus.menu import OMenu


class ShadowLNLSToolsMenu(OMenu):

    def __init__(self):
        super().__init__(name="Shadow LNLS Tools")

        self.openContainer()
        self.addContainer("LNLS Help")
        self.addSubMenu("Help")        
        self.closeContainer()        
        

    def executeAction_1(self, action):
        try:
           self.showHelpMessage("Shadow LNLS Tools Help")

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
    
    def showHelpMessage(self,title):
        msgBox = QtWidgets.QMessageBox()                
        msgBox.setText("For widgget theory and examples, access:")
        msgBox.setInformativeText("<a href='https://github.com/oasys-lnls-kit/OASYS1-LNLS-ShadowOui'>OASYS1-LNLS-ShadowOui/</a> \n")        
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)         
        msgBox.exec()
        
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

    #################################################################
    #
    # SCHEME MANAGEMENT
    #
    #################################################################

    def getWidgetFromNode(self, node):
        return self.canvas_main_window.current_document().scheme().widget_for_node(node)

    def createLinks(self, nodes):
        previous_node = None
        for node in nodes:
            if not (isinstance(node, str)) and not previous_node is None and not (isinstance(previous_node, str)):
                link = SchemeLink(source_node=previous_node, source_channel="Beam", sink_node=node, sink_channel="Input Beam")
                self.canvas_main_window.current_document().addLink(link=link)
            previous_node = node

    def getWidgetDesc(self, widget_name):
        return self.canvas_main_window.widget_registry.widget(widget_name)

    def createNewNode(self, widget_desc):
        return self.canvas_main_window.current_document().createNewNode(widget_desc)

    def createNewNodeAndWidget(self, widget_desc):
        messages = []

        try:
            node = self.createNewNode(widget_desc)
            widget = self.getWidgetFromNode(node)

            # here you can put values on the attrubutes

        except Exception as exception:
            messages.append(exception.args[0])

        return widget, node, messages
