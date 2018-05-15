__author__ = 'labx'

from PyQt5 import QtWidgets
from orangecanvas.scheme.link import SchemeLink
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
            widget_desc_1 = self.getWidgetDesc("orangecontrib.shadow.widgets.sources.ow_geometrical_source.GeometricalSource")
            widget_desc_2 = self.getWidgetDesc("orangecontrib.shadow.lnls.widgets.optical_elements.ow_test_widget.TestWidget")
            widget_desc_3 = self.getWidgetDesc("orangecontrib.shadow.widgets.optical_elements.ow_plane_mirror.PlaneMirror")

            nodes = []
            messages = []

            widget_1, node_1, messages_1 = self.createNewNodeAndWidget(widget_desc_1)
            widget_2, node_2, messages_2 = self.createNewNodeAndWidget(widget_desc_2)
            widget_3, node_3, messages_3 = self.createNewNodeAndWidget(widget_desc_3)

            widget_1.single_line_value = 20000.0

            widget_2.test_value = 34567.0

            widget_3.source_plane_distance = 1000.0
            widget_3.image_plane_distance = 3000.0

            nodes.append(node_1)
            nodes.append(node_2)
            nodes.append(node_3)

            self.createLinks(nodes)

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
